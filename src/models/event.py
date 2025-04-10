from dataclasses import dataclass
from typing import Dict
import json

from models.conversation import Message, ROLE


@dataclass
class EventType:
    name: str
    definition: str
    role: ROLE

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
