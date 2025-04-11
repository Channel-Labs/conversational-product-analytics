import argparse
import logging

import boto3
from openai import OpenAI

# Configure root logger to WARNING to silence third-party libraries
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from llm_queries.assistant_namer import AssistantNamer
from llm_queries.event_type_schema_generator import EventTypeSchemaGenerator
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
    parser.add_argument("--assistant-namer-model", type=str, default="gpt-4o")
    parser.add_argument("--event-schema-model", type=str, default="o3-mini")
    args = parser.parse_args() 

    openai_client = OpenAI()   


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
    assistant_namer = AssistantNamer(openai_client, args.assistant_namer_model, conversations)
    assistant = assistant_namer.query()

    logger.info("Generating event schema")
    batch_size = 30
    num_batches = 3
    event_types = set()

    for i in range(0, min(len(conversations), batch_size * num_batches), batch_size):
        logger.info(f"Executing batch {i // batch_size + 1} of {num_batches}")

        convos = conversations[i:i+batch_size]
        event_type_schema_generator = EventTypeSchemaGenerator(openai_client, args.event_schema_model, assistant, convos, list(event_types))
        new_event_types = event_type_schema_generator.query()
        event_types.update(new_event_types)

    logger.info(f"Generated event types: {[e.name for e in event_types]}")

    logger.info("Saving data schema")
    sorted_event_types = sorted(event_types, key=lambda e: (e.role.name, e.name))
    data_schema = DataSchema(assistant, sorted_event_types)
    data_schema.to_yaml(args.data_schema_output_path)
