from dataclasses import asdict
import json
from typing import List

from functions.models.chatbot import Chatbot
from functions.models.conversation import Conversation, Message
from functions.models.event import EventType, Event
from functions.llm_queries.llm_query import OpenAIQuery


class ExplanationGenerator(OpenAIQuery):

    def __init__(
            self, 
            client,
            chat_model, 
            chatbot: Chatbot, 
            event_types: List[EventType],
            events: List[Event],
            conversation: Conversation
        ):
        super().__init__(client, chat_model)
        self.chatbot = chatbot
        self.event_types = event_types
        self.events = events
        self.conversation = conversation

    def generate_prompt(self) -> str:        
        return  f"""You are analyzing a conversation with assigned event types. Your task is to explain why each message was classified with its specific event type.

### Instructions
1. Review the assistant description, event type definitions, conversation, and assigned event types.
2. Provide an explanation (1-2 sentences) for why each message in the conversation represents on occurrence of its assigned event type.
3. Each explanation should include specific details about the event occurrence. Make sure to highlight elements that may prove valuable when performing clustering of explanations to detect behavioral patterns for each event type.

### Assistant
{self.chatbot.prompt_format}

### Event Type Definitions
{json.dumps([event_type.prompt_object for event_type in self.event_types], indent=4)}

### Conversation
{json.dumps(self.conversation.prompt_format, indent=4)}

### Assigned Event Types
{json.dumps([{"message_id": e.message_id, "event_type": e.event_type.name} for e in self.events], indent=4)}
"""
    
    def response_format(self):
        properties = {}
        for event in self.events:
            properties[str(event.message_id)] = {
                "type": "string",
                "description": f"A 1-2 sentence explanation of why the current message was assigned the following event type: {event.event_type.prompt_format}"
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

    def parse_response(self, json_response) -> List[Event]:
        print(json_response)

        # Create a list to store updated events
        updated_events = []
        
        # Update each event with its explanation from the response
        for event in self.events:
            message_id = str(event.message_id)
            explanation = json_response[message_id]
            
            # Create new event with the explanation
            updated_event = Event(
                event_type=event.event_type,
                conversation_id=event.conversation_id,
                message_id=message_id,
                explanation=explanation
            )
            updated_events.append(updated_event)
            
        return updated_events
