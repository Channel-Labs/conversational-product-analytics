from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import List, Optional


class ROLE(Enum):
    user = auto()
    assistant = auto()

@dataclass
class Message:
    role: ROLE
    content: str
    timestamp: datetime
    message_id: str

    @property
    def prompt_format(self):
        return {"message_id": self.message_id, "role": self.role.name.lower(), "content": self.content}


@dataclass
class Conversation:
    id: str
    user_id: str
    messages: List[Message]

    @property
    def start_time(self) -> Optional[datetime]:
        if not self.messages:
            return None

        return min(message.timestamp for message in self.messages)

    @property
    def end_time(self) -> Optional[datetime]:
        if not self.messages:
            return None

        return max(message.timestamp for message in self.messages)

    @property
    def prompt_format(self):
        return [m.prompt_format for m in self.messages]

