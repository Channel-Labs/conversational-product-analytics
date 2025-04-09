from functions.llm_queries.llm_query import LLMQuery, OpenAIQuery
from functions.models.chatbot import Chatbot
from functions.models.conversation import Conversation

class UserGeneratedQuery(OpenAIQuery):

    def __init__(self, client, model: str, prompt: str, conversation: Conversation, chatbot: Chatbot):
        super().__init__(client, model)
        self.prompt = prompt
        self.conversation = conversation
        self.chatbot = chatbot

    def generate_prompt(self) -> str:
        return f"""Determine whether the following conversation satisfies the user's query.

### User Query
{self.prompt}

### Assistant
{self.chatbot.prompt_format}

### Conversation
{self.conversation.prompt_format}
"""

    # def response_format(self):
    #     properties = dict()
    #     properties["is_satisfied"] = {
    #         "type": "boolean",
    #         "description": "Whether the conversation satisfies the user's query.",
    #     }