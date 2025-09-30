#!/usr/bin/env python3
"""
수동으로 Bedrock Agent 설정 생성
"""

import json
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def create_manual_config():
    """수동으로 Agent 설정 생성"""
    
    print("=== Bedrock Agent 수동 설정 ===")
    print("\nAWS 콘솔에서 Bedrock Agent를 생성하세요:")
    print("1. AWS 콘솔 → Amazon Bedrock → Agents")
    print("2. 'Create Agent' 클릭")
    print("3. 다음 설정 사용:")
    print("   - Agent name: DietCoach")
    print("   - Description: AI 다이어트 코치")
    print("   - Model: Claude 3 Haiku")
    print("   - Instructions: 전문적인 AI 다이어트 코치로서 개인 맞춤형 조언 제공")
    
    print("\n4. Agent 생성 후 다음 정보를 입력하세요:")
    
    # 사용자 입력 받기
    agent_id = input("Agent ID를 입력하세요 (예: ABCD1234EF): ").strip()
    if not agent_id:
        agent_id = "DIETCOACH"  # 기본값
    
    agent_alias_id = input("Agent Alias ID를 입력하세요 (예: TSTALIASID): ").strip()
    if not agent_alias_id:
        agent_alias_id = "TSTALIASID"  # 기본값
    
    # 설정 파일 생성
    config = {
        "agent_id": agent_id,
        "agent_alias_id": agent_alias_id,
        "region": "ap-northeast-2",
        "model": "anthropic.claude-3-haiku-20240307-v1:0"
    }
    
    config_path = '/home/ec2-user/backend/bedrock_agent_config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"\n설정이 저장되었습니다: {config_path}")
    print(f"Agent ID: {agent_id}")
    print(f"Alias ID: {agent_alias_id}")
    
    return config

def create_default_config():
    """기본 설정으로 테스트용 config 생성"""
    
    config = {
        "agent_id": "DIETCOACH",
        "agent_alias_id": "TSTALIASID", 
        "region": "ap-northeast-2",
        "model": "anthropic.claude-3-haiku-20240307-v1:0",
        "note": "테스트용 설정 - 실제 Agent ID로 교체 필요"
    }
    
    config_path = '/home/ec2-user/backend/bedrock_agent_config.json'
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"기본 설정이 생성되었습니다: {config_path}")
    print("실제 Agent를 생성한 후 agent_id와 agent_alias_id를 업데이트하세요.")
    
    return config

if __name__ == "__main__":
    print("1. 수동 입력으로 설정")
    print("2. 기본 설정으로 생성 (나중에 수정)")
    
    choice = input("선택하세요 (1 또는 2): ").strip()
    
    if choice == "1":
        create_manual_config()
    else:
        create_default_config()