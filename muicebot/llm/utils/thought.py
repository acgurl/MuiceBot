import re
from typing import Optional


class ThoughtProcessor:
    def __init__(self, status: int = 1):
        if status not in (0, 1, 2):
            raise ValueError("status must be 0, 1, or 2")
        self.status = status
        self.inside_think = False  # 用于流式处理

    def process_message(self, message: str) -> tuple[str, str]:
        if self.status == 0:
            return "", message

        thoughts_pattern = re.compile(r"<think>(.*?)</think>", re.DOTALL)
        match = thoughts_pattern.search(message)
        thoughts = match.group(1).replace("\n", "") if match else ""
        result = thoughts_pattern.sub("", message).strip()

        if self.status == 2 or not thoughts:
            return "", result

        return f"思考过程：{thoughts}", result

    def process_chunk(self, chunk: str) -> Optional[str]:
        if self.status == 0:
            return chunk

        if self.status == 2:
            if "<think>" in chunk:
                self.inside_think = True
                chunk = chunk.replace("<think>", "")
            if "</think>" in chunk:
                self.inside_think = False
                chunk = chunk.replace("</think>", "")
            if self.inside_think:
                return None  # 当前在思考区域，屏蔽掉
            return chunk

        # status == 1
        chunk = chunk.replace("<think>", "思考过程：").replace("</think>", "\n\n")
        return chunk
