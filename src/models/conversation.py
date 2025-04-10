from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class Message:
    is_bot: bool
    content: str
    timestamp: datetime
    message_id: str

    @property
    def prompt_format(self):
        return {"message_id": self.message_id, "role": "assistant" if self.is_bot else "user", "content": self.content}


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

