import json
from typing import List

from llm_queries.llm_query import LLMQuery, ModelProvider
from models.assistant import Assistant
from models.conversation import Conversation, Message
from models.event import EventType, Event


class ExplanationGenerator(LLMQuery):

    def __init__(
            self, 
            model_provider: ModelProvider,
            model_id: str, 
            assistant: Assistant, 
            event_types: List[EventType],
            events: List[Event],
            conversation: Conversation
        ):
        super().__init__(model_provider, model_id)
        self.assistant = assistant
        self.event_types = event_types
        self.events = events
        self.conversation = conversation

    def generate_prompt(self) -> str:        
        return  f"""You are analyzing a conversation where each message has been assigned an event type. Your task is to explain why each message was assigned its event type.

### Instructions
1. Review the assistant description, event type definitions, conversation, and assigned event types.
2. Provide an explanation (1-2 sentences) for why each message in the conversation represents on occurrence of its assigned event type.
3. Each explanation should include specific details about the event occurrence. Make sure to highlight elements that may prove valuable when performing clustering of explanations to detect behavioral patterns for each event type.

### Assistant
{self.assistant.prompt_format}

### Event Type Definitions
{json.dumps([event_type.prompt_object for event_type in self.event_types], indent=4)}

### Conversation
{json.dumps(self.conversation.prompt_format, indent=4)}

### Assigned Event Types
{json.dumps([{"message_id": e.message.message_id, "event_type": e.event_type.name} for e in self.events], indent=4)}
"""
    
    def response_schema(self):
        properties = {}
        for event in self.events:
            properties[str(event.message.message_id)] = {
                "type": "string",
                "description": f"A 1-2 sentence explanation of why the current message was assigned the following event type: {event.event_type.prompt_format}"
            }
    
        return {
            "type": "object",
            "properties": properties,
            "required": [str(e.message.message_id) for e in self.events],
            "additionalProperties": False
        }

    def parse_response(self, json_response) -> List[Event]:
        # Create a list to store updated events
        updated_events = []
        
        # Update each event with its explanation from the response
        for event in self.events:
            message_id = str(event.message.message_id)
            event = next((e for e in self.events if e.message.message_id == message_id), None)
            if event is None:
                raise ValueError(f"Event not found for message_id {message_id}")
            
            explanation = json_response[message_id]

            event.explanation = explanation
            updated_events.append(event)
            
        return updated_events
