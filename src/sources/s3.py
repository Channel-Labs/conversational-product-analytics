from typing import List
import io
import boto3
import pandas as pd
import re
import json

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
                
                # Skip directories or non-CSV/JSON files
                if file_key.endswith('/') or not (file_key.lower().endswith('.csv') or file_key.lower().endswith('.json')):
                    continue
                
                conversations.extend(self._process_s3_file(file_key))
                
        return conversations
    
    def _process_s3_file(self, file_key: str) -> List[Conversation]:
        """Process a single S3 CSV file into Conversation objects"""
        # Get file content from S3
        response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=file_key)
        file_content = response['Body'].read()
        bytes_io = io.BytesIO(file_content)
        
        # Parse CSV content
        if file_key.endswith("csv"):
            conversation_df = pd.read_csv(bytes_io)
        else:
            json_data = json.loads(bytes_io.read().decode('utf-8'))
            conversation_df = self._parse_json_data(json_data)
        
        return self._transform_data_frame(conversation_df)