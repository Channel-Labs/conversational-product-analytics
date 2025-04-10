from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict
from enum import Enum, auto
import json

from models.conversation import Message
class SenderType(Enum):
    USER = auto()
    ASSISTANT = auto()

@dataclass
class EventType:
    name: str
    definition: str
    sender_type: SenderType

    @property
    def prompt_object(self) -> Dict[str, str]:
        return {"name": self.name, "definition": self.definition}

    @property
    def prompt_format(self) -> str:
        return json.dumps(self.prompt_object, indent=4)

@dataclass
class Event:
    user_id: str
    event_type: EventType
    conversation_id: str
    message: Message
