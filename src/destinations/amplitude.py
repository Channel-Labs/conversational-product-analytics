import os

from amplitude import Amplitude
from amplitude import BaseEvent

from destinations.destination import Destination
from models.event import Event, ROLE


class AmplitudeDestination(Destination):

    def __init__(self, amplitude_client: Amplitude):
        self.amplitude_client = amplitude_client

    def send_event(self, event: Event):
        self.amplitude_client.track(
            BaseEvent(
                event_type=event.event_type.name,
                user_id=str(event.user_id),
                time=int(event.message.timestamp.timestamp()  * 1000),
                event_properties={
                    "conversation_id": event.conversation_id,
                    "message_id": event.message.message_id,
                    "content": event.message.content,
                    "role": event.message.role.name.lower()
                }
            )
        )