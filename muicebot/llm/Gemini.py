from typing import AsyncGenerator, List, Literal, Optional, Union, overload

from google import genai
from google.genai import errors
from google.genai.types import (
    Content,
    ContentOrDict,
    GenerateContentConfig,
    GoogleSearch,
    HarmBlockThreshold,
    HarmCategory,
    Part,
    SafetySetting,
    Tool,
)
from httpx import ConnectError
from nonebot import logger

from ..models import Resource
from ._types import (
    BasicModel,
    ModelCompletions,
    ModelConfig,
    ModelRequest,
    ModelStreamCompletions,
    function_call_handler,
)
from .utils.images import get_file_base64


class Gemini(BasicModel):
    def __init__(self, model_config: ModelConfig) -> None:
        super().__init__(model_config)
        self._require("model_name", "api_key")

        self.model_name = self.config.model_name
        self.api_key = self.config.api_key
        self.enable_search = self.config.online_search

        self.client = genai.Client(api_key=self.api_key)

        self.gemini_config = GenerateContentConfig(
            temperature=self.config.temperature,
            top_p=self.config.top_p,
            top_k=self.config.top_k,
            max_output_tokens=self.config.max_tokens,
            presence_penalty=self.config.presence_penalty,
            frequency_penalty=self.config.frequency_penalty,
            response_modalities=[m.upper() for m in self.config.modalities if m in {"image", "text"}],
            safety_settings=(
                [
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    ),
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    ),
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    ),
                    SafetySetting(
                        category=HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
                        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
                    ),
                ]
                if self.config.content_security
                else []
            ),
        )

        self.model = self.client.chats.create(model=self.model_name, config=self.gemini_config)

    def __build_user_parts(self, request: ModelRequest) -> list[Part]:
        user_parts: list[Part] = [Part.from_text(text=request.prompt)]

        if not request.resources:
            return user_parts

        for resource in request.resources:
            if resource.type == "image" and resource.path is not None:
                resource.ensure_mimetype()
                user_parts.append(
                    Part.from_bytes(
                        data=get_file_base64(resource.path), mime_type=resource.mimetype or "image/jpeg"  # type:ignore
                    )
                )

        return user_parts

    def __build_tools_list(self, tools: Optional[List] = []):
        format_tools = []

        for tool in tools if tools else []:
            tool = tool["function"]
            required_parameters = tool["required"]
            del tool["required"]
            tool["parameters"]["required"] = required_parameters
            format_tools.append(tool)

        function_tools = Tool(function_declarations=format_tools)  # type:ignore

        if self.enable_search:
            function_tools.google_search = GoogleSearch()

        if tools or self.enable_search:
            self.gemini_config.tools = [function_tools]

    def _build_messages(self, request: ModelRequest) -> list[ContentOrDict]:
        messages: List[ContentOrDict] = []

        if request.history:
            for index, item in enumerate(request.history):
                messages.append(
                    Content(
                        role="user", parts=self.__build_user_parts(ModelRequest(item.message, resources=item.resources))
                    )
                )
                messages.append(Content(role="model", parts=[Part.from_text(text=item.respond)]))

        messages.append(Content(role="user", parts=self.__build_user_parts(request)))

        return messages

    async def _ask_sync(self, messages: list[ContentOrDict], **kwargs) -> ModelCompletions:
        compltions = ModelCompletions()

        try:
            chat = self.client.aio.chats.create(model=self.model_name, config=self.gemini_config, history=messages[:-1])
            message = messages[-1].parts  # type:ignore
            response = await chat.send_message(message=message)  # type:ignore
            if response.usage_metadata:
                total_token_count = response.usage_metadata.total_token_count
                self._total_tokens += total_token_count if total_token_count else -1

            if response.text:
                compltions.text = response.text

            if (
                response.candidates
                and response.candidates[0].content
                and response.candidates[0].content.parts
                and response.candidates[0].content.parts[0].inline_data
                and response.candidates[0].content.parts[0].inline_data.data
            ):
                compltions.resources = [
                    Resource(type="image", raw=response.candidates[0].content.parts[0].inline_data.data)
                ]

            if response.function_calls:
                function_call = response.function_calls[0]
                function_name = function_call.name
                function_args = function_call.args

                logger.info(f"function call 请求 {function_name}, 参数: {function_args}")
                function_return = await function_call_handler(function_name, function_args)  # type:ignore
                logger.success(f"Function call 成功，返回: {function_return}")

                function_response_part = Part.from_function_response(
                    name=function_name,  # type:ignore
                    response={"result": function_return},
                )

                messages.append(Content(role="model", parts=[Part(function_call=function_call)]))
                messages.append(Content(role="user", parts=[function_response_part]))

                return await self._ask_sync(messages)

            compltions.text = compltions.text or "（警告：模型无输出！）"
            compltions.usage = self._total_tokens
            return compltions

        except errors.APIError as e:
            error_message = f"API 状态异常: {e.code}({e.response})"
            compltions.text = error_message
            compltions.succeed = False
            logger.error(error_message)
            logger.error(e.message)
            return compltions

        except ConnectError:
            error_message = "模型加载器连接超时"
            compltions.text = error_message
            compltions.succeed = False
            logger.error(error_message)
            return compltions

    async def _ask_stream(self, messages: list, **kwargs) -> AsyncGenerator[ModelStreamCompletions, None]:
        try:
            total_tokens = 0
            stream = await self.client.aio.models.generate_content_stream(
                model=self.model_name, contents=messages, config=self.gemini_config
            )
            async for chunk in stream:
                stream_completions = ModelStreamCompletions()

                if chunk.text:
                    stream_completions.chunk = chunk.text
                    yield stream_completions

                if chunk.usage_metadata and chunk.usage_metadata.total_token_count:
                    total_tokens = chunk.usage_metadata.total_token_count

                if (
                    chunk.candidates
                    and chunk.candidates[0].content
                    and chunk.candidates[0].content.parts
                    and chunk.candidates[0].content.parts[0].inline_data
                    and chunk.candidates[0].content.parts[0].inline_data.data
                ):
                    stream_completions.resources = [
                        Resource(type="image", raw=chunk.candidates[0].content.parts[0].inline_data.data)
                    ]
                    yield stream_completions

                if chunk.function_calls:
                    function_call = chunk.function_calls[0]
                    function_name = function_call.name
                    function_args = function_call.args

                    logger.info(f"function call 请求 {function_name}, 参数: {function_args}")
                    function_return = await function_call_handler(function_name, function_args)  # type:ignore
                    logger.success(f"Function call 成功，返回: {function_return}")

                    function_response_part = Part.from_function_response(
                        name=function_name,  # type:ignore
                        response={"result": function_return},
                    )

                    messages.append(Content(role="model", parts=[Part(function_call=function_call)]))
                    messages.append(Content(role="user", parts=[function_response_part]))

                    async for final_chunk in self._ask_stream(messages):
                        yield final_chunk

            totaltokens_completions = ModelStreamCompletions()

            self._total_tokens += total_tokens
            totaltokens_completions.usage = self._total_tokens
            yield totaltokens_completions

        except errors.APIError as e:
            stream_completions = ModelStreamCompletions()
            error_message = f"API 状态异常: {e.code}({e.response})"
            stream_completions.chunk = error_message
            logger.error(error_message)
            logger.error(e.message)
            stream_completions.succeed = False
            yield stream_completions
            return

        except ConnectError:
            stream_completions = ModelStreamCompletions()
            error_message = "模型加载器连接超时"
            stream_completions.chunk = error_message
            logger.error(error_message)
            stream_completions.succeed = False
            yield stream_completions
            return

    @overload
    async def ask(self, request: ModelRequest, *, stream: Literal[False] = False) -> ModelCompletions: ...

    @overload
    async def ask(
        self, request: ModelRequest, *, stream: Literal[True] = True
    ) -> AsyncGenerator[ModelStreamCompletions, None]: ...

    async def ask(
        self, request: ModelRequest, *, stream: bool = False
    ) -> Union[ModelCompletions, AsyncGenerator[ModelStreamCompletions, None]]:
        self._total_tokens = 0
        self.__build_tools_list(request.tools)
        self.gemini_config.system_instruction = request.system

        messages = self._build_messages(request)

        if stream:
            return self._ask_stream(messages)

        return await self._ask_sync(messages)
