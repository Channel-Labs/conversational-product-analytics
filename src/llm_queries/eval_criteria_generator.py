from dataclasses import asdict
from typing import List
import json

from openai import OpenAI

from functions.models.chatbot import Chatbot
from functions.models.conversation import Conversation
from functions.models.evaluation_criteria import EvaluationCriteria
from functions.llm_queries.llm_query import OpenAIQuery


class EvalCriteriaGenerator(OpenAIQuery):

    def __init__(self, openai_client, model: str, chatbot: Chatbot, reasoning_effort: str = "low"):
        super().__init__(openai_client, model, reasoning_effort=reasoning_effort)
        self.chatbot = chatbot

    def generate_prompt(self) -> str:
        mental_health_example_chatbot = Chatbot(
            name="Mental Health Companion",
            description="Your compassionate companion, here to provide a listening ear and support as you navigate life's challenges. Whether you're seeking a safe space to share your feelings or guidance on personal goals, I'm dedicated to helping you find clarity and comfort.",
        )

        example_evaluation_criteria = EvaluationCriteria(
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
                "chatbot": {"name": mental_health_example_chatbot.name, "description": mental_health_example_chatbot.description},
                "evaluation_criteria": asdict(example_evaluation_criteria)
            }
        ]

        return f"""### Task
Define the evaluation criteria that should be used to assess the chatbot's performance in a conversation.

### Examples
{json.dumps(examples, indent=4)}

### Chatbot
{self.chatbot.prompt_format}
"""

    def response_format(self):
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
        if not all(key in json_response for key in {"primary_goals", "secondary_goals", "tertiary_goals", "dealbreakers"}):
            raise ValueError(f"eval_criteria_generator response missing required field: {json_response}")

        return EvaluationCriteria(
            primary_goals=json_response["primary_goals"],
            secondary_goals=json_response["secondary_goals"],
            tertiary_goals=json_response["tertiary_goals"],
            dealbreakers=json_response["dealbreakers"]
        )


if __name__ == "__main__":
    openai_client = OpenAI()
    model = "o3-mini"
    chatbot = Chatbot(
        name="Tax Advisor",
        description="Your friendly tax assistant, here to help you navigate the complexities of filing taxes, deductions, and refunds. With a mix of guidance and a touch of uncertainty, I aim to provide you with the information you need to make informed decisions."
    )

    eval_criteria_generator = EvalCriteriaGenerator(openai_client, model, chatbot)
    eval_criteria = eval_criteria_generator.query(None)
    print(eval_criteria)
