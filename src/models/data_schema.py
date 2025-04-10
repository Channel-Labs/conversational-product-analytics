from dataclasses import dataclass
import json
from typing import List, ClassVar

import yaml
from models.event import EventType, ROLE


@dataclass
class Assistant:
    name: str
    description: str

    @property
    def prompt_format(self) -> str:
        return json.dumps({"name": self.name, "description": self.description}, indent=4)

@dataclass
class DataSchema:
    assistant: Assistant
    event_types: List[EventType]
    
    @classmethod
    def from_yaml(cls, schema_path: str):
        """
        Load a YAML schema file and convert it into a DataSchema object.
        
        Args:
            schema_path: Path to the YAML schema file
            
        Returns:
            DataSchema object containing the parsed schema
        """
        with open(schema_path, 'r') as f:
            schema_data = yaml.safe_load(f)
        
        # Parse assistant data
        assistant_data = schema_data['assistant']
        assistant = Assistant(
            name=assistant_data['name'],
            description=assistant_data['description']
        )
        
        # Parse event types
        event_types = []
        for event_type_data in schema_data['event_types']:
            event_type = EventType(
                name=event_type_data['name'],
                definition=event_type_data['definition'],
                role=ROLE[event_type_data['role']]
            )
            event_types.append(event_type)
        
        return cls(
            assistant=assistant,
            event_types=event_types
        )


    
