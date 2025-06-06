from dataclasses import dataclass


@dataclass
class BotInfo:
    self_id: int = 123456
    superuser_id: int = 100000
    normaluser_id: int = 100001
    message_id: int = 200001
