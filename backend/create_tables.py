#!/usr/bin/env python3
"""
DynamoDB 테이블 생성 스크립트
"""

import boto3
from botocore.exceptions import ClientError

def create_tables():
    """필요한 DynamoDB 테이블들 생성"""
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    
    tables = [
        {
            'TableName': 'user_profiles',
            'KeySchema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        },
        {
            'TableName': 'diet_records',
            'KeySchema': [
                {'AttributeName': 'user_id', 'KeyType': 'HASH'},
                {'AttributeName': 'meal_id', 'KeyType': 'RANGE'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'user_id', 'AttributeType': 'S'},
                {'AttributeName': 'meal_id', 'AttributeType': 'S'}
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        },
        {
            'TableName': 'schedule_records',
            'KeySchema': [
                {'AttributeName': 'event_id', 'KeyType': 'HASH'}
            ],
            'AttributeDefinitions': [
                {'AttributeName': 'event_id', 'AttributeType': 'S'}
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        }
    ]
    
    for table_config in tables:
        try:
            response = dynamodb.create_table(**table_config)
            print(f"✅ 테이블 생성 중: {table_config['TableName']}")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceInUseException':
                print(f"⚠️  테이블 이미 존재: {table_config['TableName']}")
            else:
                print(f"❌ 테이블 생성 실패: {table_config['TableName']} - {e}")

if __name__ == "__main__":
    create_tables()
    print("🎉 DynamoDB 테이블 설정 완료!")