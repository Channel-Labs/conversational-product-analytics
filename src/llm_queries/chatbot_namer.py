from typing import List
import json

from functions.models.chatbot import Chatbot
from functions.models.conversation import Conversation
from functions.llm_queries.llm_query import OpenAIQuery


class ChatbotNamer(OpenAIQuery):

    max_messages_per_conversation = 6
    max_conversations = 30

    def __init__(self, openai_client, model: str, conversations: List[Conversation]):
        super().__init__(openai_client, model)
        self.conversations = conversations

    def generate_prompt(self) -> str:
        # Format conversation samples as JSON
        conversation_samples = []
        for conversation in self.conversations[:self.max_conversations]: 
            messages = conversation.messages[:self.max_messages_per_conversation]  
            if not messages:
                continue
            
            conversation_samples.append({
                "conversation_id": conversation.id,
                "messages": [msg.prompt_format for msg in messages]
            })

        return f"""Generate a name and description for a chatbot based on the provided conversations between a chatbot and its users.

### Conversations
{json.dumps(conversation_samples, indent=2)}

### Instructions
- The chatbot may already identify itself within the conversations. If so, you can use this information to generate the name and description.
- If the chatbot does not identify itself, you should infer the chatbot's name and description based on the conversation data. The name should be short and professional ("Mental Health Companion", "Customer Support Agent", "Sales Coach", etc.), and the description should be brief (1-2 sentences) and capture the chatbot's purpose and how it interacts with users.
"""

    def response_format(self):
        properties = dict()
        properties["chatbot_name"] = {
            "type": "string",
            "description": "A short (1-3 words) name that captures the essence or main focus of the chatbot.",
        }
        properties["chatbot_description"] = {
            "type": "string",
            "description": "A brief (1-2 sentences) description that captures the chatbot's purpose and how it interacts with users.",
        }            
        required = ["chatbot_name", "chatbot_description"]

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
        if "chatbot_name" not in json_response or "chatbot_description" not in json_response:
            raise ValueError(f"chatbot_namer response missing required field: {json_response}")

        return Chatbot(
            name=json_response["chatbot_name"],
            description=json_response["chatbot_description"]
        )