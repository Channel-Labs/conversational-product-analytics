import argparse

import boto3
from openai import OpenAI
import pandas as pd

from conversation_handlers import CSVConversationHandler

from llm_queries.event_generator import EventGenerator

from models.data_schema import DataSchema

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=str, required=True)
    parser.add_argument("--data-schema-path", type=str, required=True)
    args = parser.parse_args()

    openai_client = OpenAI()
    s3_client = boto3.client("s3")

    data_schema = DataSchema.from_yaml(args.data_schema_path)

    print(args.data_path)
    df = pd.read_csv(args.data_path)
    print(df.head())

    handler = CSVConversationHandler(s3_client)
    conversations = [handler.format(group) for _, group in df.groupby("conversation_id")]

    # TODO: make this configurable
    event_model = "gpt-4o"

    for conversation in conversations[:10]:
        event_generator = EventGenerator(
            openai_client,
            event_model, 
            data_schema.assistant, 
            data_schema.event_types,
            conversation=conversation
        )
        events = event_generator.query(max_retries=2, retry_delay=2, timeout=60)




