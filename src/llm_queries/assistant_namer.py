from typing import List
import json

from models.assistant import Assistant
from models.conversation import Conversation
from llm_queries.llm_query import OpenAIQuery


class AssistantNamer(OpenAIQuery):

    max_messages_per_conversation = 6
    max_conversations = 30

    def __init__(self, openai_client, model: str, conversations: List[Conversation]):
        super().__init__(openai_client, model)
        self.conversations = conversations

    def generate_prompt(self) -> str:
        conversations_json = [{"conversation_id": conversation.id, "messages": [msg.prompt_format for msg in conversation.messages]} for conversation in self.conversations[:self.max_conversations]]

        return f"""Generate a name and description for the AI assistant based on the provided conversations between an assistant and its users.

### Conversations
{json.dumps(conversations_json, indent=2)}

### Instructions
- The assistant may already identify itself within the conversations. If so, you can use this information to generate the name and description.
- If the assistant does not identify itself, you should infer the assistant's name and description based on the conversation data. The name should be short and professional ("Mental Health Companion", "Customer Support Agent", "Sales Coach", etc.), and the description should be brief (1-2 sentences) and capture the assistant's purpose and how it interacts with users.
"""

    def response_format(self):
        properties = dict()
        properties["assistant_name"] = {
            "type": "string",
            "description": "A short (1-3 words) name that captures the essence or main focus of the assistant.",
        }
        properties["assistant_description"] = {
            "type": "string",
            "description": "A brief (1-2 sentences) description that captures the assistant's purpose and how it interacts with users.",
        }            
        required = ["assistant_name", "assistant_description"]

        schema = {
            "type": "object",
            "properties": properties,
            "required": required,
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

    def parse_response(self, json_response):
        print(json_response)
        if "assistant_name" not in json_response or "assistant_description" not in json_response:
            raise ValueError(f"assistant_namer response missing required field: {json_response}")

        return Assistant(
            name=json_response["assistant_name"],
            description=json_response["assistant_description"]
        )