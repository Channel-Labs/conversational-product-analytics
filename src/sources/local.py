import json
from typing import List

import pandas as pd

from models.conversation import Conversation, Message, ROLE

from sources.source import Source

class LocalSource(Source):

    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_conversations(self) -> List[Conversation]:
        if self.file_path.endswith("csv"):
            conversation_df = pd.read_csv(self.file_path)
        else:
            with open(self.file_path, 'r') as f:
                data = json.load(f)
            conversation_df = self._parse_json_data(data)

        return self._transform_data_frame(conversation_df)
