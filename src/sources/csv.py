from typing import List

import pandas as pd

from models.conversation import Conversation, Message, ROLE

from sources.source import Source

class CSVSource(Source):

    def __init__(self, file_path: str):
        self.file_path = file_path

    def get_conversations(self) -> List[Conversation]:
        conversation_df = pd.read_csv(self.file_path)

        # Either user_id or conversation_id is required
        user_id_column = "user_id" if "user_id" in conversation_df.columns else "conversation_id"
        conversation_id_column = "conversation_id" if "conversation_id" in conversation_df.columns else "user_id"

        # Convert timestamps to datetime before creating Message objects
        conversation_df['timestamp'] = pd.to_datetime(conversation_df['timestamp'])

        conversations = []
        for conversation_id, group_df in conversation_df.groupby(conversation_id_column):
        
            # Ensure index is reset to ensure messages contain correct message_id
            group_df = group_df.reset_index(drop=True)
        
            conversation = Conversation(
                id=conversation_id,
                user_id=group_df.iloc[0][user_id_column],
                messages=[Message(ROLE[row['role']], row['content'], row['timestamp'], row.get('message_id', str(i))) for i, row in group_df.iterrows()]
            )
            conversations.append(conversation)

        return conversations
