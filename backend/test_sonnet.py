#!/usr/bin/env python3
"""
Claude Sonnet 4.5 모델 테스트
"""

import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

# AWS 자격 증명 확인
print(f"AWS_ACCESS_KEY_ID: {os.getenv('AWS_ACCESS_KEY_ID')[:10]}...")
print(f"AWS_SECRET_ACCESS_KEY: {os.getenv('AWS_SECRET_ACCESS_KEY')[:10]}...")
print(f"AWS_REGION: {os.getenv('AWS_REGION')}")

def test_sonnet_model():
    """Claude Sonnet 4.5 모델 테스트"""
    
    bedrock_runtime = boto3.client(
        'bedrock-runtime', 
        region_name='ap-northeast-2',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
    )
    
    try:
        print("Claude 3.5 Haiku 모델 테스트 중...")
        
        model_id = "anthropic.claude-3-haiku-20240307-v1:0"
        messages = [{"role": "user", "content": [{"text": "안녕하세요! 저는 키 170cm, 몸무게 70kg입니다. 전문적인 다이어트 조언을 부탁드립니다."}]}]
        
        response = bedrock_runtime.converse(
            modelId=model_id,
            messages=messages,
        )
        
        claude_response = response['output']['message']['content'][0]['text']
        
        print("✅ Claude Sonnet 4.5 테스트 성공!")
        print(f"\n응답:\n{claude_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Claude Sonnet 4.5 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    test_sonnet_model()