from dataclasses import dataclass, field
from typing import Dict, List, Optional
import json

from models.conversation import Message, ROLE

@dataclass
class EventProperty:
    name: str
    definition: str
    choices: List[str]

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, EventProperty):
            return self.name == other.name
        return False

    @property
    def prompt_object(self) -> Dict[str, str]:
        return {"name": self.name, "definition": self.definition, "choices": self.choices}

    @property
    def prompt_format(self) -> str:
        return json.dumps(self.prompt_object, indent=4)

@dataclass
class EventType:
    name: str
    definition: str
    role: ROLE
    properties: List[EventProperty] = field(default_factory=list)
    
    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        if isinstance(other, EventType):
            return self.name == other.name
        return False
    
    @property
    def prompt_object(self) -> Dict[str, str]:
        return {"name": self.name, "definition": self.definition, "role": self.role.name}

    @property
    def prompt_format(self) -> str:
        return json.dumps(self.prompt_object, indent=4)

@dataclass
class Event:
    user_id: str
    event_type: EventType
    conversation_id: str
    message: Message
    property_values: Dict[EventProperty, str] = field(default_factory=dict)
    explanation: Optional[str] = None
