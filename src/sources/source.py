from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List

import pandas as pd

from models.conversation import Conversation, Message, ROLE

class Source(ABC):

    @abstractmethod
    def get_conversations(self) -> List[Conversation]:
        pass

    def _transform_data_frame(self, df: pd.DataFrame) -> List[Conversation]:
         # Either user_id or conversation_id is required
        user_id_column = "user_id" if "user_id" in df.columns else "conversation_id"
        conversation_id_column = "conversation_id" if "conversation_id" in df.columns else "user_id"

        # Check if timestamp column exists, if not, we'll add it later per conversation
        has_timestamp = 'timestamp' in df.columns
        if has_timestamp:
            # Convert timestamps to datetime before creating Message objects
            df['timestamp'] = pd.to_datetime(df['timestamp'])

        conversations = []
        for conversation_id, group_df in df.groupby(conversation_id_column):
        
            # Ensure index is reset to ensure messages contain correct message_id
            group_df = group_df.reset_index(drop=True)
            
            # If no timestamp column, create timestamps starting from now
            if not has_timestamp:
                now = datetime.now()
                timestamps = [now + timedelta(seconds=i) for i in range(len(group_df))]
                group_df['timestamp'] = timestamps
        
            conversation = Conversation(
                id=conversation_id,
                user_id=group_df.iloc[0][user_id_column],
                messages=[Message(ROLE[row['role']], row['content'], row['timestamp'], row.get('message_id', str(i))) for i, row in group_df.iterrows()]
            )
            conversations.append(conversation)     

        return conversations
    
    def _parse_json_data(self, json_data) -> pd.DataFrame:
        rows = []
        for convo_id, convo_data in json_data.items():
            for message in convo_data['messages']:
                rows.append({
                    'conversation_id': convo_id,
                    'role': message['role'],
                    'content': message['content']
                })

        return pd.DataFrame(rows)
