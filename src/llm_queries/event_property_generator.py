import json
from typing import List, Dict

from llm_queries.llm_query import OpenAIQuery
from models.assistant import Assistant
from models.event import EventType, Event, EventProperty

class EventPropertyGenerator(OpenAIQuery):

    def __init__(
        self, 
        client,
        model, 
        assistant: Assistant, 
        event_type: EventType,
        events: List[Event], 
        event_property: EventProperty
    ):
        super().__init__(client, model)
        self.assistant = assistant
        self.event_type = event_type
        self.events = events   
        self.event_property = event_property

    def generate_prompt(self) -> str:
        explanations_json = [
            {
                "message_id": issue.message.message_id,
                "explanation": issue.explanation
            }
            for issue in self.events
        ]
            
        return f"""Determine the appropriate event property value for each event, based on the explanations provided for why each message was tagged with the specified event type.

### Assistant
{self.assistant.prompt_format}

### Event Type
{self.event_type.prompt_format}

### Event Property
{self.event_property.prompt_format}

### Event Explanations
{json.dumps(explanations_json, indent=4)}
"""
    
    def response_format(self):
        properties = {}
        for event in self.events:
            properties[str(event.message.message_id)] = {
                "type": "string",
                "enum": self.event_property.choices,
                "description": f"The event property value that occurred during message_id {event.message.message_id}. If the message should not be tagged with any of the event property values, returnn an empty string."
            }

        schema = {
            "type": "object",
            "properties": properties,
            "required": [str(e.message.message_id) for e in self.events],
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
       
    def parse_response(self, json_response) -> List[Event]:
        results = []
        
        for message_id, event_property_value in json_response.items():
            event = next((e for e in self.events if e.message.message_id == message_id), None)
            if event is None:
                raise ValueError(f"Event not found for message_id {message_id}")
            
            event.property_values[self.event_property.name] = event_property_value
            results.append(event)
            
        return results
       

