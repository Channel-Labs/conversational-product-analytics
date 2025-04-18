import argparse
import logging

import boto3
from anthropic import Anthropic
from openai import OpenAI

# Configure root logger to WARNING to silence third-party libraries
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from llm_queries.assistant_namer import AssistantNamer
from llm_queries.event_type_schema_generator import EventTypeSchemaGenerator
from llm_queries.event_property_schema_generator import EventPropertySchemaGenerator
from llm_queries.llm_judge_criteria_generator import LLMJudgeCriteriaGenerator
from llm_queries.llm_query import OpenAIModelProvider, BedrockModelProvider, AnthropicModelProvider
from models.data_schema import DataSchema
from sources.local import LocalSource
from sources.s3 import S3Source

# Set loggers within this application to INFO
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logging.getLogger('openai').setLevel(logging.WARNING)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=str, required=True)
    parser.add_argument("--data-schema-output-path", type=str, required=True, help="The location to save the generated data schema")
    parser.add_argument("--model-provider", type=str, choices=["openai", "bedrock", "anthropic"], default="openai")
    parser.add_argument("--assistant-namer-model", type=str, default="gpt-4.1")
    parser.add_argument("--llm-judge-criteria-model", type=str, default="o4-mini")
    parser.add_argument("--event-schema-model", type=str, default="o4-mini")
    args = parser.parse_args() 


    if args.model_provider == "openai":
        openai_client = OpenAI()
        model_provider = OpenAIModelProvider(openai_client)
    elif args.model_provider == "anthropic":
        anthropic_client = Anthropic()
        model_provider = AnthropicModelProvider(anthropic_client)
    elif args.model_provider == "bedrock":
        bedrock_client = boto3.client("bedrock-runtime")
        model_provider = BedrockModelProvider(bedrock_client)

    # Automatically determine source type based on path prefix
    if args.data_path.startswith("s3://"):
        logger.info("Detected S3 path, loading data from S3")
        s3_client = boto3.client("s3")
        source = S3Source(s3_client, args.data_path)
    else:
        logger.info("Loading data from local file")
        source = LocalSource(args.data_path)

    conversations = source.get_conversations()

    logger.info("Generating assistant definition")
    assistant_namer = AssistantNamer(model_provider, args.assistant_namer_model, conversations)
    assistant = assistant_namer.query()

    logger.info("Generating LLM judge criteria")
    llm_judge_criteria_generator = LLMJudgeCriteriaGenerator(model_provider, args.llm_judge_criteria_model, assistant)
    llm_judge_criteria = llm_judge_criteria_generator.query(max_retries=2, timeout=120)

    logger.info("Generating event schema")
    batch_size = 40
    num_batches = 1
    event_types = set()

    for i in range(0, min(len(conversations), batch_size * num_batches), batch_size):
        logger.info(f"Executing batch {i // batch_size + 1} of {num_batches}")

        convos = conversations[i:i+batch_size]

        # First identify common event types across conversations in this batch
        logger.info("Generating event types")
        event_type_schema_generator = EventTypeSchemaGenerator(model_provider, args.event_schema_model, assistant, convos, list(event_types))
        new_event_types = event_type_schema_generator.query(max_retries=2, timeout=120)
        logger.info(f"Generated event types in batch {i // batch_size + 1}: {[e.name for e in new_event_types]}")

        # Now generate event properties for each event type identified in this batch
        for event_type in new_event_types:
            logger.info(f"Generating event properties for event type: {event_type.name}")
            event_property_schema_generator = EventPropertySchemaGenerator(model_provider, args.event_schema_model, assistant, event_type, convos)
            event_type = event_property_schema_generator.query(max_retries=2, timeout=120)

            # Remove the event type from the set and add the updated event type back to the set, so that it's saved with the updated properties
            event_types.discard(event_type)
            event_types.add(event_type)


    logger.info(f"Generated event types: {[e.name for e in event_types]}")

    logger.info("Saving data schema")
    sorted_event_types = sorted(event_types, key=lambda e: (e.role.name, e.name))
    data_schema = DataSchema(assistant, llm_judge_criteria, sorted_event_types)
    data_schema.to_yaml(args.data_schema_output_path)
