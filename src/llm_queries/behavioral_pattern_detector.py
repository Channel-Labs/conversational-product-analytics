import json
from typing import List, Dict

from functions.llm_queries.llm_query import OpenAIQuery
from functions.models.behavior import Behavior
from functions.models.chatbot import Chatbot
from functions.models.event import Event, EventType

class BehavioralPatternDetector(OpenAIQuery):

    MISCELLANEOUS_PATTERN_NAME = "Miscellaneous"

    def __init__(self, client, model, chatbot: Chatbot, event_type: EventType, events: List[Event], behaviors: List[Behavior]):
        super().__init__(client, model)
        self.chatbot = chatbot
        self.event_type = event_type
        self.events = events   
        self.behaviors = behaviors

    def generate_prompt(self) -> str:
        explanations_json = [
            {
                "message_id": issue.message_id,
                "explanation": issue.explanation
            }
            for issue in self.events
        ]
            
        return f"""Determine the appropriate behavioral pattern classification for each message explanation.

### Assistant
{self.chatbot.prompt_format}

### Event Type
{self.event_type.prompt_format}

### Behavioral Patterns
{json.dumps([b.prompt_json for b in self.behaviors], indent=4)}

### Message Explanations
{json.dumps(explanations_json, indent=4)}
"""
    
    def response_format(self):
        behavior_names = [b.name for b in self.behaviors] + [self.MISCELLANEOUS_PATTERN_NAME]
        properties = {}
        for message in self.events:
            properties[str(message.message_id)] = {
                "type": "string",
                "enum": behavior_names,
                "description": f"The behavior pattern that occurred during message_id {message.message_id}. If the message does not contain any of the behavioral patterns, classify it as {self.MISCELLANEOUS_PATTERN_NAME}."
            }

        schema = {
            "type": "object",
            "properties": properties,
            "required": [str(e.message_id) for e in self.events],
            "additionalProperties": False
        }

        return {
            "type": "json_schema",
            "json_schema": {
                "name": "response",
                "strict": True,
                "schema": schema
            }
        }
       
    def parse_response(self, json_response) -> Dict[str, Behavior]:
        result = {}
        behavior_map = {b.name: b for b in self.behaviors}
        
        for message_id, behavior_name in json_response.items():
            # Look up the behavior object by name
            behavior = behavior_map.get(behavior_name, None)
            # Store as a list to maintain consistency with other parts of the system
            result[int(message_id)] = behavior
            
        return result
       

