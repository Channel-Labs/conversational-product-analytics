from dataclasses import dataclass
import json
from typing import List

import yaml
from models.assistant import Assistant
from models.event import EventType, ROLE, EventProperty
from models.llm_judge_criteria import LLMJudgeCriteria

@dataclass
class DataSchema:
    assistant: Assistant
    llm_judge_criteria: LLMJudgeCriteria
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
        
        # Parse LLM judge criteria
        judge_criteria_data = schema_data['llm_judge_criteria']
        llm_judge_criteria = LLMJudgeCriteria(
            primary_goals=judge_criteria_data.get('primary_goals', []),
            secondary_goals=judge_criteria_data.get('secondary_goals', []),
            tertiary_goals=judge_criteria_data.get('tertiary_goals', []),
            dealbreakers=judge_criteria_data.get('dealbreakers', [])
        )
        
        # Parse event types
        event_types = []
        for event_type_data in schema_data['event_types']:
            # Parse properties if they exist
            properties = []
            if 'properties' in event_type_data:
                for prop_name, prop_data in event_type_data['properties'].items():
                    choices = prop_data.get('choices', [])
                    property = EventProperty(
                        name=prop_name,
                        definition=prop_data.get('definition', ''),
                        choices=choices
                    )
                    properties.append(property)
            
            event_type = EventType(
                name=event_type_data['name'],
                definition=event_type_data['definition'],
                role=ROLE[event_type_data['role']],
                properties=properties
            )
            event_types.append(event_type)
        
        return cls(
            assistant=assistant,
            llm_judge_criteria=llm_judge_criteria,
            event_types=event_types
        )

    def to_yaml(self, file_path: str):
        """
        Save the DataSchema object to a YAML file.
        
        Args:
            file_path: Path where the YAML file will be saved
        """
        # Create a dictionary representing the schema structure
        schema_dict = {
            'assistant': {
                'name': self.assistant.name,
                'description': self.assistant.description
            },
            'llm_judge_criteria': {
                'primary_goals': self.llm_judge_criteria.primary_goals,
                'secondary_goals': self.llm_judge_criteria.secondary_goals,
                'tertiary_goals': self.llm_judge_criteria.tertiary_goals,
                'dealbreakers': self.llm_judge_criteria.dealbreakers
            },
            'event_types': []
        }
        
        # Add each event type to the schema
        for event_type in self.event_types:
            event_type_dict = {
                'name': event_type.name,
                'definition': event_type.definition,
                'role': event_type.role.name
            }
            
            # Add properties if they exist
            if event_type.properties:
                event_type_dict['properties'] = {}
                for prop in event_type.properties:
                    event_type_dict['properties'][prop.name] = {
                        'definition': prop.definition
                    }
                    if prop.choices:
                        event_type_dict['properties'][prop.name]['choices'] = prop.choices
            
            schema_dict['event_types'].append(event_type_dict)
        
        # Write the dictionary to the YAML file
        with open(file_path, 'w') as f:
            yaml.dump(schema_dict, f, sort_keys=False)

    
