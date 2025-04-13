from abc import ABC, abstractmethod

from models.event import Event

class Destination(ABC):

    @abstractmethod
    def send_event(self, event: Event, llm_judge_score: int):
        pass
