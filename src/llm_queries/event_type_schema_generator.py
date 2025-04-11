import json
from typing import List

from llm_queries.llm_query import OpenAIQuery
from models.assistant import Assistant
from models.conversation import Conversation
from models.event import EventType, ROLE

class EventTypeSchemaGenerator(OpenAIQuery):

    examples = [
        {
            "assistant": {"name": "Mental Health Companion"}, 
            "event_types": [
                {"name": "Emotional Disclosure", "role": "user"}, 
                {"name": "Crisis Disclosure", "role": "user"}, 
                {"name": "Emotional Withdrawal", "role": "user"}, 
                {"name": "Express Gratitude", "role": "user"}, 
                {"name": "Narrative Disclosure", "role": "user"},
                {"name": "Personal Insight", "role": "user"}, 
                {"name": "Seek Clarification", "role": "user"}, 
                {"name": "Self-Exploration", "role": "user"}, 
                {"name": "Small Talk", "role": "user"},
                {"name": "Support Request", "role": "user"}, 
                {"name": "Therapeutic Resistance", "role": "user"},
                {"name": "Educational Guidance", "role": "assistant"},
                {"name": "Positive Affirmation", "role": "assistant"}, 
                {"name": "Request Deflection", "role": "assistant"}, 
                {"name": "Small Talk", "role": "assistant"},
                {"name": "Therapeutic Intervention", "role": "assistant"}, 
                {"name": "Therapeutic Misalignment", "role": "assistant"}
            ]
        }
    ]

    def __init__(
        self,
        client, 
        model, 
        assistant: Assistant, 
        conversations: List[Conversation], 
        previous_event_types: List[EventType],
        reasoning_effort: str="medium"
    ):
        super().__init__(client, model, reasoning_effort=reasoning_effort)
        self.assistant = assistant
        self.conversations = conversations
        self.previous_event_types = previous_event_types

    def generate_prompt(self) -> str:
        conversations_json = [{"conversation_id": conversation.id, "messages": [msg.prompt_format for msg in conversation.messages]} for conversation in self.conversations]
        previous_event_types_json = [event_type.prompt_object for event_type in self.previous_event_types]

        return f"""Determine the event types that should be tracked in order to enable effective product analytics for conversational assistants. A downstream pipeline will then tag each message with the appropriate event type, and the events will be sent to a product analytics platform.
        
### Instructions
1. Review the assistant, examples of effective event schemas, and conversations.
2. Identify patterns of events that commonly appear across conversations and should be tracked.
3. Ensure each event type is tangible, mutually exclusive, and contains the correct amount of specificity. If the events are too specific, the user will be overwhelmed when using the product analytics platform and not be able to find meaningful insights. However, if they are too generic, the user won't be able to find meaningful insights. Also, note that a downstream prompt will generate event properties for each event type to add additional specfics.
4. The examples of effective event schemas represent high-quality event type schemas that were generated for other assistants. They each represent a complete schema with the correct amount of specificity.
5. The previous event types represent those identified in prior conversations with this assistant. For identified event types that are semantically similar to an existing event type, provide the EXACT same name/definition as the existing event type. For identified event types that are semantically different, provide a new name/definition.
6. Continue to re-read the conversations until you're confident that you've identified all the notable event types. 

### Assistant
{self.assistant.prompt_format}

### Examples of Effective Event Schemas
{json.dumps(self.examples, indent=4)}

### Previous Event Types
{json.dumps(previous_event_types_json, indent=4)}

### Conversations
{json.dumps(conversations_json, indent=4)}
"""
    
    def response_format(self):
        properties = {}
        properties["event_types"] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "A short (3-5 words) name that captures the essence or main focus of the event type."
                    },
                    "definition": {
                        "type": "string",
                        "description": "A brief (1-2 sentences) definition of the event type."
                    },
                    "role": {
                        "type": "string",
                        "description": "Whether the event type is associated with the assistant or the user.",
                        "enum": ["assistant", "user"]
                    }
                },
                "required": ["name", "definition", "role"],
                "additionalProperties": False
            },
        }

        schema = {
            "type": "object",
            "properties": properties,
            "required": ["event_types"],
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
       
    def parse_response(self, json_response) -> List[EventType]:
        results = []
        event_types_data = json_response.get("event_types", [])
        for event_type_data in event_types_data:
            event_type = EventType(
                name=event_type_data["name"],
                definition=event_type_data["definition"],
                role=ROLE[event_type_data["role"]]
            )
            results.append(event_type)  

        return results
