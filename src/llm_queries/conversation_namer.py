import json

from functions.models.conversation import Conversation
from functions.llm_queries.llm_query import OpenAIQuery


# names conversations by querying an LLM
class ConversationNamer(OpenAIQuery,):

    max_messages_to_include = 4

    def __init__(self, client, model: str, conversation: Conversation):
        super().__init__(client, model)
        self.conversation = conversation

    def generate_prompt(self) -> str:
        initial_messages = [m.prompt_format for m in self.conversation.messages[:self.max_messages_to_include]]
    
        return f"""You are an assistant that specializes in summarizing conversations with concise titles. Below are the initial turns of a chatbot conversation. Based on these turns, generate a short, descriptive name that captures the essence or main focus of the conversation. The title should be engaging, informative, and no longer than a few words (e.g., 3–8 words). Avoid generic names like "Chat Session" or "Conversation 1", and aim for a title that highlights any unique or defining aspect present in the turns.

### Conversation
{json.dumps(initial_messages, indent=4)}
"""
    
    def response_format(self):
        properties = dict()
        properties["conversation_name"] = {
            "type": "string",
            "description": "A short and descriptive name that captures the essence or main focus of the conversation.",
        }

        required = ["conversation_name"]

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
        if "conversation_name" not in json_response:
            raise ValueError(f"conversation_namer response missing required field: {json_response}")

        return json_response["conversation_name"]


