import argparse
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from tqdm import tqdm

from anthropic import Anthropic
from amplitude import Amplitude
import boto3
from openai import OpenAI
from posthog import Posthog

# Configure root logger to WARNING to silence third-party libraries
logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from destinations.amplitude import AmplitudeDestination
from destinations.posthog import PosthogDestination
from llm_queries.event_generator import EventGenerator
from llm_queries.event_property_generator import EventPropertyGenerator
from llm_queries.explanation_generator import ExplanationGenerator
from llm_queries.llm_query import OpenAIModelProvider, BedrockModelProvider, AnthropicModelProvider
from models.data_schema import DataSchema
from sources.local import LocalSource
from sources.s3 import S3Source

# Set loggers within this application to INFO
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

logging.getLogger('openai').setLevel(logging.WARNING)
logging.getLogger('amplitude').setLevel(logging.WARNING)
logging.getLogger('anthropic').setLevel(logging.WARNING)
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-path", type=str, required=True)
    parser.add_argument("--data-schema-path", type=str, required=True)
    parser.add_argument("--destination", type=str, choices=["amplitude", "posthog"], required=True)
    parser.add_argument("--model-provider", type=str, choices=["openai", "anthropic", "bedrock"], default="openai")
    parser.add_argument("--event-model", type=str, default="gpt-4o")
    parser.add_argument("--event-property-model", type=str, default="gpt-4o")
    parser.add_argument("--explanation-model", type=str, default="gpt-4o-mini")
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

    data_schema = DataSchema.from_yaml(args.data_schema_path)

    # Automatically determine source type based on path prefix
    if args.data_path.startswith("s3://"):
        logger.info("Detected S3 path, loading data from S3")
        s3_client = boto3.client("s3")
        source = S3Source(s3_client, args.data_path)
    else:
        logger.info("Loading data from local file")
        source = LocalSource(args.data_path)

    if args.destination == "amplitude":
        logger.info("Using Amplitude destination")
        destination = AmplitudeDestination(amplitude_client=Amplitude(os.getenv("AMPLITUDE_API_KEY")))
    else:
        logger.info("Using Posthog destination")
        posthog_client = Posthog(
            project_api_key=os.getenv("POSTHOG_API_KEY"),
            host=os.getenv("POSTHOG_HOST")
        )
        destination = PosthogDestination(posthog_client=posthog_client)       

    logger.info("Loading conversations")
    conversations = source.get_conversations()
    logger.info(f"Found {len(conversations)} conversations")

    logger.info("Generating events")
    events_by_conversation = dict()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {
            executor.submit(
                EventGenerator(
                    model_provider,
                    args.event_model, 
                    data_schema.assistant, 
                    data_schema.event_types,
                    conversation=conversation
                ).query,
                max_retries=2,
                retry_delay=2,
                timeout=60
            ): conversation for conversation in conversations
        }
        
        for future in tqdm(as_completed(futures), total=len(conversations), desc="Generating events"):
            try:
                conversation = futures[future]
                events_for_conversation = future.result()
                events_by_conversation[conversation] = events_for_conversation
            except Exception as e:
                logger.error(f"Error processing conversation {conversation.id}: {e}")
    
    logger.info("Generating event explanations")
    events = list()
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for conversation, events_for_conversation in events_by_conversation.items():
            future = executor.submit(
                ExplanationGenerator(
                    model_provider,
                    args.explanation_model, 
                    data_schema.assistant, 
                    data_schema.event_types,
                    events_for_conversation,
                    conversation
                ).query,
                max_retries=2,
                retry_delay=2,
                timeout=60
            )
            futures[future] = conversation
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Generating explanations"):
            try:
                events_with_explanations = future.result()
                events.extend(events_with_explanations)
            except Exception as e:
                conversation = futures[future]
                logger.error(f"Error generating explanation for conversation {conversation.id}: {e}")

    logger.info("Generating event property values. Number of events: %d", len(events))
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        batch_size = 50
        event_mapping = {event.message.message_id: i for i, event in enumerate(events)}

        for event_type in data_schema.event_types:
            events_for_event_type = [event for event in events if event.event_type == event_type]
            if not events_for_event_type:
                continue
                
            # Skip if no properties to process
            if not event_type.properties:
                continue
                
            for event_property in event_type.properties:
                # Process events in batches
                for i in range(0, len(events_for_event_type), batch_size):
                    events_batch = events_for_event_type[i:i + batch_size]
                    future = executor.submit(
                        EventPropertyGenerator(
                            model_provider,
                            args.event_property_model, 
                            data_schema.assistant, 
                            event_type, 
                            events_batch,
                            event_property
                        ).query,
                        max_retries=2,
                        retry_delay=2,
                        timeout=60
                    )
                    futures[future] = (event_type.name, event_property.name, [event.message.message_id for event in events_batch])
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Generating event properties"):
            try:
                events_with_property_values = future.result()
                # Update existing events in events with new property values
                for updated_event in events_with_property_values:
                    message_id = updated_event.message.message_id
                    if message_id in event_mapping:
                        index = event_mapping[message_id]
                        # Merge properties instead of replacing the entire event
                        for prop, prop_value in updated_event.property_values.items():
                            events[index].property_values[prop] = prop_value
            except Exception as e:
                event_type_name, property_name, _ = futures[future]
                logger.error(f"Error generating property {property_name} for event type {event_type_name}: {e}")

    logger.info(f"Uploading events")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures= [
            executor.submit(destination.send_event, event) for event in events
        ]
        
        for future in tqdm(as_completed(futures), total=len(events), desc="Uploading events"):
            try:
                future.result()
            except Exception as e:
                logger.error(f"Error sending event: {e}")




