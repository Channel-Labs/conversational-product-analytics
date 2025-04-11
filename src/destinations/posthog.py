from posthog import Posthog

from destinations.destination import Destination
from models.event import Event


class PosthogDestination(Destination):

    def __init__(self, posthog_client: Posthog):
        self.posthog_client = posthog_client

    def send_event(self, event: Event):

        event_properties = {
            "conversation_id": event.conversation_id,
            "message_id": event.message.message_id,
            "content": event.message.content,
            "role": event.message.role.name.lower(),
            "explanation": event.explanation
        }

        for property_name, property_value in event.property_values.items():
            event_properties[property_name] = property_value

        self.posthog_client.capture(
            distinct_id=str(event.user_id),
            event=event.event_type.name,
            properties=event_properties,
            timestamp=event.message.timestamp
        )