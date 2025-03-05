import asyncio
import base64
import hashlib
import hmac
import json
import ssl
from datetime import datetime
from functools import partial
from time import mktime
from urllib.parse import urlencode, urlparse
from wsgiref.handlers import format_date_time

import websocket
from nonebot import logger

from ._types import BasicModel, ModelConfig
from .utils.auto_system_prompt import auto_system_prompt


class Xfyun(BasicModel):
    """
    星火大模型
    """

    def __init__(self, model_config: ModelConfig) -> None:
        super().__init__(model_config)
        self._require("app_id", "api_key", "api_secret", "service_id", "resource_id")

    def load(self) -> bool:
        self.app_id = self.config.app_id
        self.api_key = self.config.api_key
        self.api_secret = self.config.api_secret
        self.service_id = self.config.service_id
        self.resource_id = self.config.resource_id
        self.system_prompt = self.config.system_prompt
        self.auto_system_prompt = self.config.auto_system_prompt
        self.temperature = self.config.temperature
        self.top_k = self.config.top_k
        self.max_tokens = self.config.max_tokens
        self.url = (
            self.config.api_host
            if self.config.api_host
            else "wss://maas-api.cn-huabei-1.xf-yun.com/v1.1/chat"
        )
        self.host = urlparse(self.url).netloc
        self.path = urlparse(self.url).path
        self.response = ""
        self.is_history = False
        self.is_running = True
        return self.is_running

    # 生成url
    def __create_url(self):
        # 生成RFC1123格式的时间戳
        now = datetime.now()
        date = format_date_time(mktime(now.timetuple()))

        # 拼接字符串
        signature_origin = "host: " + self.host + "\n"
        signature_origin += "date: " + date + "\n"
        signature_origin += "GET " + self.path + " HTTP/1.1"

        # 进行hmac-sha256进行加密
        signature_sha = hmac.new(
            self.api_secret.encode("utf-8"),  # type: ignore
            signature_origin.encode("utf-8"),  # type: ignore
            digestmod=hashlib.sha256,
        ).digest()

        signature_sha_base64 = base64.b64encode(signature_sha).decode(encoding="utf-8")

        authorization_origin = (
            f'api_key="{self.api_key}", '
            f'algorithm="hmac-sha256", '
            f'headers="host date request-line", '
            f'signature="{signature_sha_base64}"'
        )

        authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode(
            encoding="utf-8"
        )

        # 将请求的鉴权参数组合为字典
        v = {"authorization": authorization, "date": date, "host": self.host}
        # 拼接鉴权参数，生成url
        url = self.url + "?" + urlencode(v)
        # 此处打印出建立连接时候的url,参考本demo的时候可取消上方打印的注释，比对相同参数时生成的url与自己代码生成的url是否一致
        return url

    def __on_message(self, ws, message):
        response = json.loads(message)
        logger.debug(f"Spark返回数据: {response}")
        if response["header"]["code"] != 0:  # 不合规时该值为10013
            logger.warning(
                f"调用Spark在线模型时发生错误: {response['header']['message']}"
            )
            self.response = "（已被过滤）"
            ws.close()
        elif (
            response["header"]["status"] in [0, 1, 2]
            and response["payload"]["choices"]["text"][0]["content"] != " "
        ):
            self.response += response["payload"]["choices"]["text"][0]["content"]
        if response["header"]["status"] == 2:
            ws.close()

    def __on_error(self, ws, error):
        logger.error(f"调用Spark在线模型时发生错误: {error}")
        ws.close()

    def __on_close(self, ws, close_status_code, close_msg):
        pass

    def __on_open(self, ws):
        request_data = {
            "header": {"app_id": self.app_id, "patch_id": [self.resource_id]},
            "parameter": {
                "chat": {
                    "domain": self.service_id,
                    "temperature": self.temperature,
                    "top_k": self.top_k,
                    "max_tokens": self.max_tokens,
                }
            },
            "payload": {"message": {"text": self.history}},
        }
        ws.send(json.dumps(request_data))

    def __generate_system_prompt(self, user_text: str) -> str:
        if self.auto_system_prompt:
            return "system\n\n" + auto_system_prompt(user_text) + "user\n\n"
        return "system\n\n" + self.system_prompt + "user\n\n"

    def __generate_history(self, history: list):
        self.history = []
        if len(history) == 0:
            return
        self.is_history = True
        self.history.append(
            {
                "role": "user",
                "content": self.__generate_system_prompt(history[0][0]) + history[0][1],
            }
        )
        for item in history:
            self.history.append({"role": "user", "content": item[0]})
            self.history.append({"role": "assistant", "content": item[1]})

    def __ask(self, prompt: str, history: list) -> str:
        self.response = ""
        self.__generate_history(history)
        if not self.is_history:
            self.history.append(
                {
                    "role": "user",
                    "content": self.__generate_system_prompt(prompt) + prompt,
                }
            )
        else:
            self.history.append({"role": "user", "content": prompt})

        logger.debug(f"发送给Spark的数据: {self.history}")
        ws = websocket.WebSocketApp(
            self.__create_url(),
            on_message=self.__on_message,
            on_error=self.__on_error,
            on_close=self.__on_close,
        )
        ws.on_open = self.__on_open
        ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE}, ping_timeout=10)

        return self.response

    async def ask(self, prompt, history=None) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, partial(self.__ask, prompt=prompt, history=history)
        )
