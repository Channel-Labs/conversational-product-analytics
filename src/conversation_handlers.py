from abc import ABC, abstractmethod
from typing import Dict, Optional
import io

import boto3
import pandas as pd


from models.conversation import Conversation, Message

    
class ConversationHandler(ABC):

    def __init__(self, s3_client: boto3.client, type: str):
        self.s3_client = s3_client
        self.type = type

    def read_from_s3(self, s3_bucket: str, s3_key: str) -> pd.DataFrame:
        try:
            # Fetch the file content from S3
            response = self.s3_client.get_object(Bucket=s3_bucket, Key=s3_key)
            file_content = response['Body'].read()

            # Convert to DataFrame
            df = self.to_pandas_df(file_content)
        
            # Check required columns exist
            required_columns = self.get_required_columns()
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                raise ValueError(f"Missing required columns in CSV data: {missing_columns}")

            return df.astype(required_columns)
        except Exception as e:
            raise Exception(f"Failed to read conversation data from S3: {str(e)}")
        
    @abstractmethod
    def format(self, conversation_df: pd.DataFrame) -> Optional[Conversation]:
        pass

    @abstractmethod
    def to_pandas_df(self, file_content: bytes) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_required_columns(self) -> Dict[str, type]:
        pass


class CSVConversationHandler(ConversationHandler):

    def __init__(self, s3_client: boto3.client):
        super().__init__(s3_client, "conversations")

    def format(self, conversation_df: pd.DataFrame) -> Optional[Conversation]:
        convo_ids = conversation_df["conversation_id"].unique().tolist()
        if len(convo_ids) != 1:
            raise ValueError(f"A conversation can only contain one unique conversation_id, found {len(convo_ids)}")

        # Convert timestamps to datetime before creating Message objects
        conversation_df['timestamp'] = pd.to_datetime(conversation_df['timestamp'])
        
        # Ensure index is reset to ensure messages contain correct message_id
        conversation_df = conversation_df.reset_index(drop=True)
        
        return Conversation(
            id=convo_ids[0],
            name='',
            messages=[Message(row['is_bot'], row['message'], row['timestamp'], row.get('message_id', str(i))) for i, row in conversation_df.iterrows()]
        )
    
    def to_pandas_df(self, file_content: bytes) -> pd.DataFrame:
        # Decode bytes to string for CSV files
        return pd.read_csv(io.StringIO(file_content.decode('utf-8')))

    def get_required_columns(self) -> Dict[str, type]:
        return {
            "conversation_id": str,
            "timestamp": str,
            "is_bot": bool,
            "message": str
        }

    
