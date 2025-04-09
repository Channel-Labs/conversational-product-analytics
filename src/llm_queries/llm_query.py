from abc import ABC, abstractmethod
import json
import time
import openai


class LLMQuery(ABC):
    """Base abstract class for LLM queries that defines the common interface."""
    
    @abstractmethod
    def __init__(self, model_id, temp=0):
        self.model_id = model_id
        self.temp = temp
    
    @abstractmethod
    def generate_prompt(self) -> str:
        """Generate the prompt to send to the LLM."""
        pass
    
    @abstractmethod
    def response_format(self):
        """Define the expected response format."""
        pass
    
    @abstractmethod
    def parse_response(self, json_response):
        """Parse the JSON response from the LLM."""
        pass
    
    @abstractmethod
    def query(self, max_retries=3, retry_delay=2, timeout=60):
        """Send the query to the LLM and return the parsed response."""
        pass


class OpenAIQuery(LLMQuery):

    def __init__(self, client, model_id, temp=0, reasoning_effort="low"):
        super().__init__(model_id, temp)
        self.client = client
        self.reasoning_effort = reasoning_effort


    def query(self, max_retries=3, retry_delay=2, timeout=60):
        user_msg = self.generate_prompt()

        retries = 0
        while retries < max_retries:
            try:
                # The reasoning models don't support temperature, but they have a reasoning_effort instead
                if self.model_id.startswith("o"):
                    response = self.client.chat.completions.create(
                        model=self.model_id,
                        messages=[
                            {"role": "user", "content": user_msg}
                        ],
                        reasoning_effort=self.reasoning_effort,
                        seed=42,
                        response_format=self.response_format(),
                        timeout=timeout
                    ).choices[0].message.content
                else:
                    response = self.client.chat.completions.create(
                        model=self.model_id,
                        messages=[
                            {"role": "user", "content": user_msg}
                        ],
                        temperature=self.temp,
                        seed=42,
                        response_format=self.response_format(),
                        timeout=timeout
                    ).choices[0].message.content

                json_response = json.loads(response)
                return self.parse_response(json_response)
            except openai.RateLimitError as e:
                retries += 1
                print(e)
                print(f"Rate limit hit. Retrying in {retry_delay} seconds... (Attempt {retries}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay += 2
            except Exception as e:
                print(f"Unexpected error: {e}")
                break

        raise Exception("Unable to complete llm query.")


class BedrockQuery(LLMQuery):

    def __init__(self, bedrock_client, model_id, temp=0):
        super().__init__(model_id, temp)
        self.bedrock_client = bedrock_client

    def query(self, max_retries=2, retry_delay=2, timeout=60):
        user_msg = self.generate_prompt()

        retries = 0
        while retries < max_retries:
            try:
                response = self._query_claude(user_msg, timeout)
                json_response = json.loads(response)
                return self.parse_response(json_response)
            except Exception as e:
                retries += 1
                print(f"Error: {e}")
                print(f"Retrying in {retry_delay} seconds... (Attempt {retries}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay += 2

        raise Exception("Unable to complete llm query.")
    
    def _query_claude(self, user_msg, timeout):
        """Handle Claude API calls via Amazon Bedrock using tool use for schema enforcement"""
        response_format = self.response_format()
        
        # Prepare the request body for Claude
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 4096,
            "temperature": self.temp,
            "messages": [
                {"role": "user", "content": user_msg}
            ],
            "tools": [response_format],
            "tool_choice": {"type": "tool", "name": response_format["name"]}
        }
         
        # Call the Bedrock API
        response = self.bedrock_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(request_body),
            contentType="application/json",
            accept="application/json"
        )
        
        # Parse the response
        response_body = json.loads(response['body'].read().decode('utf-8'))
        print(f"Response body: {response_body}")
        
        input = response_body["content"][0]["input"]
        return json.dumps(input)
