from dataclasses import asdict
from typing import List
import json

from openai import OpenAI

from models.assistant import Assistant
from models.llm_judge_criteria import LLMJudgeCriteria
from llm_queries.llm_query import LLMQuery, ModelProvider


class LLMJudgeCriteriaGenerator(LLMQuery):

    def __init__(self, model_provider: ModelProvider, model_id: str, assistant: Assistant):
        super().__init__(model_provider, model_id)
        self.assistant = assistant

    def generate_prompt(self) -> str:
        mental_health_assistant_example = Assistant(
            name="Mental Health Companion",
            description="Your compassionate companion, here to provide a listening ear and support as you navigate life's challenges. Whether you're seeking a safe space to share your feelings or guidance on personal goals, I'm dedicated to helping you find clarity and comfort.",
        )

        example_llm_judge_criteria = LLMJudgeCriteria(
            primary_goals=[
                "Demonstrate empathetic listening and genuine compassion",
                "Correctly utilize therapeutic techniques to help the user explore their feelings, encourage further sharing, and gain personal insights",
                "Maintain a safe and non-judgmental space that encourages open sharing and emotional security"
            ],
            secondary_goals=[
                "Offer tailored, contextually relevant responses based on the user's unique experiences and expressed needs",    
                "Balance a warm and compassionate tone with clear guidance and, when necessary, appropriate disclaimers"
            ],
            tertiary_goals=[
                "Ensure consistency in tone, language, and messaging throughout the conversation",
                "Adapt responses flexibly to match the user's emotional state and evolving context",
                "Communicate clearly and simply, avoiding overly technical terms or ambiguous language",
            ],
            dealbreakers=[
                "Using insensitive, dismissive, or offensive language that invalidates the user's feelings",
                "Providing harmful, dangerous, or inappropriate advice that could exacerbate the user's distress",
                "Offering overly generic or repetitive responses that make the user feel unheard or misunderstood",
                "Assuming the user's situation or blindly agreeing to their thinking"
            ]
        )

        examples = [
            {
                "assistant": mental_health_assistant_example.prompt_object,
                "response": asdict(example_llm_judge_criteria)
            }
        ]

        return f"""Define the criteria that an LLM judge should use to assess the assistant's performance in a conversation.

### Examples
{json.dumps(examples, indent=4)}

### Assistant
{self.assistant.prompt_format}
"""

    def response_schema(self):
        properties = dict()
        properties["primary_goals"] = {
            "type": "array",
            "items": {
                "type": "string",
            },
        }
        properties["secondary_goals"] = {
            "type": "array",
            "items": {
                "type": "string",
            },
        }
        properties["tertiary_goals"] = {
            "type": "array",
            "items": {
                "type": "string",
            },
        }
        properties["dealbreakers"] = {
            "type": "array",
            "items": {
                "type": "string",
            },
        }

        required = ["primary_goals", "secondary_goals", "tertiary_goals", "dealbreakers"]

        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False
        }

    def parse_response(self, json_response):
        print(json_response)
        if not all(key in json_response for key in {"primary_goals", "secondary_goals", "tertiary_goals", "dealbreakers"}):
            raise ValueError(f"eval_criteria_generator response missing required field: {json_response}")

        return LLMJudgeCriteria(
            primary_goals=json_response["primary_goals"],
            secondary_goals=json_response["secondary_goals"],
            tertiary_goals=json_response["tertiary_goals"],
            dealbreakers=json_response["dealbreakers"]
        )
