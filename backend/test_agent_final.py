#!/usr/bin/env python3
"""
최종 Agent 테스트
"""

import boto3
import json
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def test_bedrock_agent():
    """Bedrock Agent 최종 테스트"""
    
    # 설정 파일 로드
    with open('/home/ec2-user/backend/bedrock_agent_config.json', 'r') as f:
        config = json.load(f)
    
    print(f"Agent ID: {config['agent_id']}")
    print(f"Agent Alias ID: {config['agent_alias_id']}")
    
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='ap-northeast-2')
    
    try:
        print("\nAgent 테스트 중...")
        
        response = bedrock_agent_runtime.invoke_agent(
            agentId=config['agent_id'],
            agentAliasId=config['agent_alias_id'],
            sessionId='testuser123',
            inputText='안녕하세요! 저는 키 170cm, 몸무게 70kg입니다. 다이어트 조언을 부탁드립니다.'
        )
        
        # 응답 처리
        agent_response = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    agent_response += chunk['bytes'].decode('utf-8')
        
        print("✅ Bedrock Agent 테스트 성공!")
        print(f"\nAgent 응답:\n{agent_response}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent 테스트 실패: {e}")
        
        # Claude 직접 호출로 폴백 테스트
        print("\nClaude 직접 호출 테스트...")
        try:
            bedrock_runtime = boto3.client('bedrock-runtime', region_name='ap-northeast-2')
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": "안녕하세요! 저는 키 170cm, 몸무게 70kg입니다. 다이어트 조언을 부탁드립니다."
                    }
                ]
            }
            
            response = bedrock_runtime.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            claude_response = response_body['content'][0]['text']
            
            print("✅ Claude 직접 호출 성공!")
            print(f"\nClaude 응답:\n{claude_response}")
            
            return False  # Agent는 실패했지만 Claude는 성공
            
        except Exception as claude_error:
            print(f"❌ Claude 직접 호출도 실패: {claude_error}")
            return False

if __name__ == "__main__":
    print("=== Bedrock Agent 최종 테스트 ===")
    test_bedrock_agent()