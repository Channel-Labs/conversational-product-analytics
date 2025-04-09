import json

from dataclasses import asdict, dataclass

from functions.models.chatbot import Chatbot
from functions.models.conversation import Conversation
from functions.models.evaluation_criteria import EvaluationCriteria
from functions.llm_queries.llm_query import OpenAIQuery

class LLMJudge(OpenAIQuery):

    def __init__(self, client, model: str, chatbot: Chatbot, eval_criteria: EvaluationCriteria, conversation: Conversation):
        super().__init__(client, model)
        self.chatbot = chatbot
        self.eval_criteria = eval_criteria
        self.conversation = conversation

    def generate_prompt(self) -> str:
        return f"""Assess the chatbot's performance in the conversation based on the specified evaluation criteria.

### Chatbot
{json.dumps(asdict(self.chatbot), indent=4)}

### Evaluation Criteria
{json.dumps(asdict(self.eval_criteria), indent=4)}

### Conversation
{json.dumps(self.conversation.prompt_format, indent=4)}
"""
    

    def response_format(self):
        properties = dict()
        properties["score"] = {
            "type": "number",
            "description": "A score between 0 and 100 assessing the chatbot's performance in the conversation based on the evaluation criteria.",
        }

        required = ["score"]

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
    
    def parse_response(self, json_response) -> int:
        print(json_response)
        if "score" not in json_response:
            raise ValueError(f"judge response missing required field: {json_response}")

        score = json_response["score"]
        if score < 0 or score > 100:
            raise ValueError(f"judge score outside of bounds: {json_response}")

        return score       

        
        
        
        