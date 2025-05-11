import re
from dataclasses import dataclass

from nonebot.adapters import Event

from muicebot.config import plugin_config
from muicebot.llm import ModelCompletions, ModelStreamCompletions
from muicebot.models import Message
from muicebot.plugin.hook import on_after_completion, on_finish_chat, on_stream_chunk

_PROCESS_MODE = plugin_config.thought_process_mode
_STREAM_PROCESS_STATE: dict[str, bool] = {}
_PROCESSCACHES: dict[str, "ProcessCache"] = {}


@dataclass
class ProcessCache:
    thoughts: str = ""
    result: str = ""


def general_processor(message: str) -> tuple[str, str]:
    thoughts_pattern = re.compile(r"<think>(.*?)</think>", re.DOTALL)
    match = thoughts_pattern.search(message)
    thoughts = match.group(1).replace("\n", "") if match else ""
    result = thoughts_pattern.sub("", message).strip()
    return thoughts, result


@on_after_completion(priority=1, stream=False)
def async_processor(completions: ModelCompletions, event: Event):
    session_id = event.get_session_id()
    thoughts, result = general_processor(completions.text)
    _PROCESSCACHES[session_id] = ProcessCache(thoughts, result)

    if _PROCESS_MODE == 0:
        return
    if _PROCESS_MODE == 2 or not thoughts:
        completions.text = result
    elif _PROCESS_MODE == 1:
        completions.text = f"思考过程: {thoughts}\n\n{result}"


@on_stream_chunk(priority=1)
def stream_processor(chunk: ModelStreamCompletions, event: Event):
    session_id = event.get_session_id()
    cache = _PROCESSCACHES.setdefault(session_id, ProcessCache())
    state = _STREAM_PROCESS_STATE

    # 思考过程中
    if "<think>" in chunk.chunk:
        state[session_id] = True
        cache.thoughts += chunk.chunk.replace("<think>", "")
        if _PROCESS_MODE == 1:
            chunk.chunk = chunk.chunk.replace("<think>", "思考过程: ")
        elif _PROCESS_MODE == 2:
            chunk.chunk = ""
        return

    # 思考结束
    elif "</think>" in chunk.chunk:
        del state[session_id]
        cache.result += chunk.chunk.replace("</think>", "")
        if _PROCESS_MODE == 1:
            chunk.chunk = chunk.chunk.replace("</think>", "\n\n")
        elif _PROCESS_MODE == 2:
            chunk.chunk = chunk.chunk.replace("</think>", "")
        return

    # 思考过程中
    elif state.get(session_id, False):
        cache.thoughts += chunk.chunk
        if _PROCESS_MODE == 2:
            chunk.chunk = ""

    # 思考结果中
    else:
        cache.result += chunk.chunk


@on_finish_chat(priority=1)
def save_processor(message: Message, event: Event):
    session_id = event.get_session_id()
    cache = _PROCESSCACHES.pop(session_id, ProcessCache())
    message.respond = cache.result
