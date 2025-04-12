import json
from typing import List

from models.assistant import Assistant
from models.conversation import Conversation
from models.event import Event, EventType, ROLE
from llm_queries.llm_query import LLMQuery, ModelProvider


class EventGenerator(LLMQuery):

    def __init__(
            self, 
            model_provider: ModelProvider,
            model_id: str, 
            assistant: Assistant, 
            event_types: List[EventType],
            conversation: Conversation
        ):
        super().__init__(model_provider, model_id)
        self.assistant = assistant
        self.event_types = event_types
        self.conversation = conversation

    def generate_prompt(self) -> str:      
        return  f"""Determine the events that occurred during a conversation between a user and an assistant.

### Instructions
1. Review the assistant description, event type definitions, and conversation carefully.
2. For each message in the conversation, assign exactly one event type that most accurately represents what occurred in that message.
3. Consider the full context of the conversation and how each message relates to previous exchanges.
4. For event types with similar definitions, identify the distinguishing characteristics and use them to make clear distinctions.
5. Prioritize specific evidence in the message content over general impressions.
6. These event tags will be used to perform product analytics on the user/assistant conversations. Thus, think about which event type would be most beneficial for the message to be tagged with in a product analytics platform.

### Assistant
{self.assistant.prompt_format}

### Event Types
{json.dumps([event_type.prompt_object for event_type in self.event_types], indent=4)}

### Conversation
{json.dumps(self.conversation.prompt_format, indent=4)}
"""
    
    def response_schema(self):
        properties = {}

        for message in self.conversation.messages:
            if message.role == ROLE.assistant:
                event_type_ids = [str(et.name) for et in self.event_types if (et.role == ROLE.assistant)]
            else:
                event_type_ids = [str(et.name) for et in self.event_types if (et.role == ROLE.user)]

            properties[str(message.message_id)] = {
                "type": "string",
                "enum": event_type_ids,
                "description": f"The event_id that occurred during message_id {message.message_id}"
            }

        return {
            "type": "object",
            "properties": properties,
            "required": [str(m.message_id) for m in self.conversation.messages],
            "additionalProperties": False
        }

    def parse_response(self, json_response) -> List[Event]:   
        events = []
        for message in self.conversation.messages:
            message_id = str(message.message_id)
            event_type_id = json_response.get(message_id)
            event_type = next((et for et in self.event_types if str(et.name) == event_type_id), None)

            if not event_type:
                raise ValueError(f"Event type {event_type_id} not found in event types")

            events.append(Event(
                user_id=self.conversation.user_id,
                event_type=event_type,
                conversation_id=self.conversation.id,
                message=message
            ))
        return events        
