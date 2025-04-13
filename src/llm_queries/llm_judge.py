import json

from dataclasses import asdict, dataclass

from models.assistant import Assistant
from models.conversation import Conversation
from models.llm_judge_criteria import LLMJudgeCriteria
from llm_queries.llm_query import LLMQuery, ModelProvider

class LLMJudge(LLMQuery):

    def __init__(self, model_provider: ModelProvider, model_id: str, assistant: Assistant, llm_judge_criteria: LLMJudgeCriteria, conversation: Conversation):
        super().__init__(model_provider, model_id)
        self.assistant = assistant
        self.llm_judge_criteria = llm_judge_criteria
        self.conversation = conversation

    def generate_prompt(self) -> str:
        return f"""Assess the assistant's performance in the conversation based on the specified evaluation criteria.

### Assistant
{json.dumps(asdict(self.assistant), indent=4)}

### Evaluation Criteria
{json.dumps(asdict(self.llm_judge_criteria), indent=4)}

### Conversation
{json.dumps(self.conversation.prompt_format, indent=4)}
"""
    
    def response_schema(self):
        properties = dict()
        properties["score"] = {
            "type": "number",
            "description": "A score between 0 and 100 assessing the assistant's performance in the conversation based on the evaluation criteria.",
        }

        required = ["score"]

        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }
    
    def parse_response(self, json_response) -> int:
        if "score" not in json_response:
            raise ValueError(f"judge response missing required field: {json_response}")

        score = json_response["score"]
        if score < 0 or score > 100:
            raise ValueError(f"judge score outside of bounds: {json_response}")

        return score       

        
        
        
        