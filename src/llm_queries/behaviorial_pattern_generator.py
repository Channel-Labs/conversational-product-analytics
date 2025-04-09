import json
from typing import List

from functions.llm_queries.llm_query import OpenAIQuery
from functions.models.behavior import Behavior
from functions.models.chatbot import Chatbot
from functions.models.event import EventType, Event

class BehaviorPatternGenerator(OpenAIQuery):

    prompt_examples = {
        # EventType.QUERY_REFUSAL: [Behavior(EventType.QUERY_REFUSAL, "Unable to Reveal Personal Information", "When asked for personal information, the assistant acknowledges the request but intentionally refrains from providing direct responses, typically explaining that it lacks such data because it is not a human.")],
        # EventType.MISINTERPRETED_QUERY: [
        #     Behavior(EventType.MISINTERPRETED_QUERY, "Assuming Specific Meaning for Ambiguous Messages", "For ambiguous or vaguely stated user messages, instead of seeking clarification or addressing multiple possible interpretations, the assistant immediately commits to one interpretation that may not align with the user's intent.")
        # ],
        # EventType.INCONSISTENT_RESPONSE: []
    }

    def __init__(
        self,
        client, 
        model, 
        chatbot: Chatbot, 
        event_type: EventType, 
        events: List[Event], 
        previous_behaviors: List[Behavior], 
        reasoning_effort: str="medium"
    ):
        super().__init__(client, model, reasoning_effort=reasoning_effort)
        self.chatbot = chatbot
        self.event_type = event_type
        self.events = events  
        self.previous_behaviors = previous_behaviors

    def generate_prompt(self) -> str:
        observations_json = [
            {
                "conversation_id": issue.conversation_id,
                "observation": issue.explanation
            }
            for issue in self.events
        ]

        example_behaviors = self.prompt_examples.get(self.event_type.name, [])
        # Deduplicate behaviors in example with same name as previous behaviors, keeping the previous behavior version
        previous_behavior_names = {b.name for b in self.previous_behaviors}
        filtered_examples = [b for b in example_behaviors if b.name not in previous_behavior_names]
        prompt_example_behaviors = self.previous_behaviors + filtered_examples

        prompt_example_behaviors_json = [behavior.prompt_json for behavior in prompt_example_behaviors]

        return f"""Cluster the event occurrences to identify behavior patterns exhibited by the assistant that are related to the specified event type.

### Instructions
1. Review the assistant, event type, previous behavior patterns, and event occurrences.
2. Identify behavior patterns within the event occurrences that the assistant is exhibiting.
3. Ensure each behavior pattern is tangible, specific, and mutually exclusive. The ultimate goal is to enable effective product analytics for conversational assistants. Therefore, each behavior pattern should provide a product manager with a concrete insight into the assistant's behavior that they can use to improve their product.
4. The previous behavior patterns represent those identified in prior event occurrences. For identified patterns that are semantically similar to an existing pattern, provide the EXACT same name/description as the existing pattern. For identified patterns that are semantically different, provide a new name/description.
5. Continue to re-read the event occurrences until you're confident that you've identified all the notable behavior patterns. 

### Assistant
{self.chatbot.prompt_format}

### Event Type
{self.event_type.prompt_format}

### Previous Behavior Patterns
{json.dumps(prompt_example_behaviors_json, indent=4)}

### Event Occurrences
{json.dumps(observations_json, indent=4)}
"""
    
    def response_format(self):
        properties = {}
        properties["patterns"] = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "A short (3-5 words) name that captures the essence or main focus of the behavior pattern."
                    },
                    "description": {
                        "type": "string",
                        "description": "A brief (1-2 sentences) description of how the pattern manifests in the event occurrences."
                    },
                },
                "required": ["name", "description"],
                "additionalProperties": False
            },
        }

        schema = {
            "type": "object",
            "properties": properties,
            "required": ["patterns"],
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
       
    def parse_response(self, json_response) -> List[Behavior]:
        print(json_response)

        previous_behavior_names = set([behavior.name for behavior in self.previous_behaviors])
        new_behaviors = self.previous_behaviors

        behaviors_data = json_response.get("patterns", [])
        for behavior_data in behaviors_data:
            if behavior_data["name"] in previous_behavior_names:
                print(f"Behavior {behavior_data['name']} already exists. Skipping.")
                continue

            behavior = Behavior(
                event_type=self.event_type,
                name=behavior_data["name"],
                description=behavior_data["description"]
            )
            new_behaviors.append(behavior)

        return new_behaviors
