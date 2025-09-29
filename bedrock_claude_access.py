import os
import boto3

# AWS 자격 증명은 환경 변수나 AWS 프로필에서 자동으로 로드됩니다
# .env 파일이나 시스템 환경 변수에서 다음을 설정하세요:
# AWS_ACCESS_KEY_ID=your_access_key
# AWS_SECRET_ACCESS_KEY=your_secret_key
# AWS_DEFAULT_REGION=us-east-1

# Bedrock 클라이언트 생성
client = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-east-1"  # 환경 변수와 일치시킴
)

model_id = "us.anthropic.claude-sonnet-4-20250514-v1:0"
messages = [{"role": "user", "content": [{"text": "Hello"}]}]

try:
    response = client.converse(
        modelId=model_id,
        messages=messages,
    )
    print(response['output']['message']['content'][0]['text'])
except Exception as e:
    print(f"Error: {e}")