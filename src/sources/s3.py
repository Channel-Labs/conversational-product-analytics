from typing import List
import io
import boto3
import pandas as pd
import re

from models.conversation import Conversation, Message, ROLE
from sources.source import Source


class S3Source(Source):

    def __init__(self, s3_client: boto3.client, s3_uri: str):
        self.s3_client = s3_client

        # Parse s3 URI (s3://bucket-name/path/to/files)
        uri_pattern = r"s3://([^/]+)/?(.*)"
        match = re.match(uri_pattern, s3_uri)
        
        if not match:
            raise ValueError(f"Invalid S3 URI format: {s3_uri}. Expected format: s3://bucket-name/path")
            
        self.s3_bucket = match.group(1)
        self.s3_path = match.group(2)

    def get_conversations(self) -> List[Conversation]:
        # List all objects under the given path
        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.s3_bucket, Prefix=self.s3_path)
        
        conversations = []
        
        # Process each file in the S3 bucket
        for page in pages:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                file_key = obj['Key']
                
                # Skip directories or non-CSV files
                if file_key.endswith('/') or not file_key.lower().endswith('.csv'):
                    continue
                
                conversations.extend(self._process_s3_file(file_key))
                
        return conversations
    
    def _process_s3_file(self, file_key: str) -> List[Conversation]:
        """Process a single S3 CSV file into Conversation objects"""
        # Get file content from S3
        response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=file_key)
        file_content = response['Body'].read()
        
        # Parse CSV content
        conversation_df = pd.read_csv(io.BytesIO(file_content))
        
        # Either user_id or conversation_id is required
        user_id_column = "user_id" if "user_id" in conversation_df.columns else "conversation_id"
        conversation_id_column = "conversation_id" if "conversation_id" in conversation_df.columns else "user_id"
        
        # Convert timestamps to datetime before creating Message objects
        conversation_df['timestamp'] = pd.to_datetime(conversation_df['timestamp'])
        
        file_conversations = []
        for conversation_id, group_df in conversation_df.groupby(conversation_id_column):
            # Ensure index is reset to ensure messages contain correct message_id
            group_df = group_df.reset_index(drop=True)
            
            conversation = Conversation(
                id=conversation_id,
                user_id=group_df.iloc[0][user_id_column],
                messages=[Message(ROLE[row['role']], row['content'], row['timestamp'], row.get('message_id', str(i))) for i, row in group_df.iterrows()]
            )
            file_conversations.append(conversation)
            
        return file_conversations