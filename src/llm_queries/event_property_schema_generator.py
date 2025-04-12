import json
from typing import List

from llm_queries.llm_query import OpenAIQuery
from models.assistant import Assistant
from models.conversation import Conversation
from models.event import EventType, EventProperty

class EventPropertySchemaGenerator(OpenAIQuery):

    examples = [
        {
            "assistant": {"name": "Mental Health Companion"}, 
            "event_type": {"name": "Emotional Disclosure", "role": "user"}, 
            "event_properties": [
                {
                    "name": "Emotion",
                    "definition": "The emotion that the user is expressing.",
                    "values": [
                        "Anger/Frustration",
                        "Anxiety/Fear/Panic",
                        "Confusion",
                        "Guilt/Self-Blame",
                        "Joy/Happiness",
                        "Isolation/Loneliness",
                        "Sadness/Depression/Grief",
                        "Shame/Humiliation"
                    ]
                }
            ]
        }
    ]

    def __init__(
        self,
        client, 
        model, 
        assistant: Assistant, 
        event_type: EventType, 
        conversations: List[Conversation], 
        reasoning_effort: str="low"
    ):
        super().__init__(client, model, reasoning_effort=reasoning_effort)
        self.assistant = assistant
        self.event_type = event_type
        self.conversations = conversations
    def generate_prompt(self) -> str:
        conversations_json = [{"conversation_id": conversation.id, "messages": [msg.prompt_format for msg in conversation.messages]} for conversation in self.conversations]
        previous_event_properties_json = [event_property.prompt_object for event_property in self.event_type.properties]

        return f"""Determine the event properties that should be added to the specified event type. A downstream pipeline will later tag each message with the appropriate event type and property values, and the events will be sent to a product analytics platform.
        
### Instructions
1. Review the assistant, event type, examples of effective event properties, previous event properties, and conversations.
2. Identify event properties that should be added to the event type.
3. Ensure the values for each event property are tangible, mutually exclusive, and contain the correct amount of specificity. If the values are too specific, the user will be overwhelmed when using the product analytics platform and not be able to find meaningful insights. However, if they are too generic, the user won't be able to find meaningful insights.
4. The previous event properties represent those identified in the assistant's prior conversations. For identified properties that are semantically similar to an existing property, provide the EXACT same name/definition as the existing property. For identified properties that are semantically different, provide a new name/definition.
5. Similarly, when generating the values for each event property, first check which values are semantically similar to existing values. For values that are semantically similar to any existing value, use the existing value. For values that are semantically different, generate a new value.
6. The examples of effective event properties represent high-quality event properties that were generated for other assistants. They each represent the complete list of properties and values that were identified for the event type. Use them as a guide to ensure the properties and values you generate are at the right level of granularity.
7. Continue to re-read the event occurrences until you're confident that you've identified all the notable event properties. 

### Assistant
{self.assistant.prompt_format}

### Event Type
{self.event_type.prompt_format}

### Examples of Effective Event Properties
{json.dumps(self.examples, indent=4)}

### Previous Event Properties
{json.dumps(previous_event_properties_json, indent=4)}

### Conversations
{json.dumps(conversations_json, indent=4)}
"""
    
    def response_format(self):
        properties = {}
        properties["event_properties"] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "A short (3-5 words) name that captures the essence or main focus of the event property."
                    },
                    "definition": {
                        "type": "string",
                        "description": "A brief (1 sentence) definition explaining what the event property represents."
                    },
                    "values": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "description": "A possible value for the event property."
                        }
                    }
                },
                "required": ["name", "definition", "values"],
                "additionalProperties": False
            },
        }

        schema = {
            "type": "object",
            "properties": properties,
            "required": ["event_properties"],
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
       
    def parse_response(self, json_response) -> EventType:
        print(json_response)

        properties_data = json_response.get("event_properties", [])
        for property_obj in properties_data:
            property = EventProperty(
                name=property_obj["name"],
                definition=property_obj["definition"],
                choices=property_obj["values"]
            )

            if property not in self.event_type.properties:
                self.event_type.properties.append(property)
            else:
                # If the property already exists, update the existing property with the new values
                existing_property = next(p for p in self.event_type.properties if p.name == property.name)
                existing_property.choices = list(set(existing_property.choices + property.choices))

        return self.event_type
