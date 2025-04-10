import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from tqdm import tqdm

from amplitude import Amplitude
import boto3
from openai import OpenAI

# Configure root logger to WARNING to silence third-party libraries
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from destinations.amplitude import AmplitudeDestination
from llm_queries.event_generator import EventGenerator
from models.data_schema import DataSchema
from sources.local import LocalSource
from sources.s3 import S3Source

# Set loggers within this application to INFO
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('amplitude').setLevel(logging.WARNING)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=str, required=True)
    parser.add_argument("--data-schema-path", type=str, required=True)
    parser.add_argument("--event-model", type=str, default="gpt-4o")
    args = parser.parse_args()

    openai_client = OpenAI()

    data_schema = DataSchema.from_yaml(args.data_schema_path)

    # Automatically determine source type based on path prefix
    if args.data_path.startswith("s3://"):
        logger.info("Detected S3 path, loading data from S3")
        s3_client = boto3.client("s3")
        source = S3Source(s3_client, args.data_path)
    else:
        logger.info("Loading data from local file")
        source = LocalSource(args.data_path)

    conversations = source.get_conversations()[:10]
    logger.info(f"Found {len(conversations)} conversations")

    events = list()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(
                EventGenerator(
                    openai_client,
                    args.event_model, 
                    data_schema.assistant, 
                    data_schema.event_types,
                    conversation=conversation
                ).query,
                max_retries=2,
                retry_delay=2,
                timeout=60
            ) for conversation in conversations
        ]
        
        for future in tqdm(as_completed(futures), total=len(conversations), desc="Generating events"):
            try:
                events_for_conversation = future.result()
                events.extend(events_for_conversation)
            except Exception as e:
                logger.error(f"Error processing conversation: {e}")

    logger.info(f"Uploading {len(events)} events")
    amplitude = AmplitudeDestination(amplitude_client=Amplitude(os.getenv("AMPLITUDE_API_KEY")))
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures= [
            executor.submit(amplitude.send_event, event) for event in events
        ]
        
        for future in tqdm(as_completed(futures), total=len(events), desc="Uploading events"):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error sending event: {e}")




