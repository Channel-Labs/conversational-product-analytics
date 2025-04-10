from abc import ABC, abstractmethod
from typing import List

from models.conversation import Conversation

class Source(ABC):

    @abstractmethod
    def get_conversations(self) -> List[Conversation]:
        pass
