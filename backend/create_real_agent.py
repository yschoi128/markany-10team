#!/usr/bin/env python3
"""
실제 Bedrock Agent 생성 스크립트
"""

import boto3
import json
import time
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

def create_iam_role():
    """Bedrock Agent용 IAM 역할 생성"""
    
    iam = boto3.client('iam', region_name='ap-northeast-2')
    sts = boto3.client('sts', region_name='ap-northeast-2')
    
    # 계정 ID 조회
    account_id = sts.get_caller_identity()['Account']
    
    role_name = "AmazonBedrockExecutionRoleForAgents_DietCoach"
    
    # 신뢰 정책
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "bedrock.amazonaws.com"
                },
                "Action": "sts:AssumeRole"
            }
        ]
    }
    
    try:
        # 기존 역할 확인
        try:
            existing_role = iam.get_role(RoleName=role_name)
            role_arn = existing_role['Role']['Arn']
            print(f"기존 IAM 역할 사용: {role_arn}")
            return role_arn
        except iam.exceptions.NoSuchEntityException:
            pass
        
        # IAM 역할 생성
        print("IAM 역할 생성 중...")
        role_response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Execution role for Bedrock Agent - Diet Coach"
        )
        
        role_arn = role_response['Role']['Arn']
        print(f"IAM 역할 생성됨: {role_arn}")
        
        # 기본 Bedrock 정책 연결
        iam.attach_role_policy(
            RoleName=role_name,
            PolicyArn="arn:aws:iam::aws:policy/AmazonBedrockFullAccess"
        )
        
        print("Bedrock 정책 연결됨")
        return role_arn
        
    except Exception as e:
        print(f"IAM 역할 생성 오류: {e}")
        return None

def create_bedrock_agent():
    """실제 Bedrock Agent 생성"""
    
    # IAM 역할 생성
    role_arn = create_iam_role()
    if not role_arn:
        return None
    
    # 역할 전파 대기
    print("IAM 역할 전파 대기 중... (30초)")
    time.sleep(30)
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='ap-northeast-2')
    
    agent_name = "DietCoach"
    foundation_model = "anthropic.claude-3-haiku-20240307-v1:0"
    
    instruction = """
당신은 전문적인 AI 다이어트 코치입니다. 다음 역할을 수행하세요:

1. 개인 맞춤형 식단 조언 제공
2. BMI 계산 및 건강 상태 분석  
3. 칼로리 목표 설정 및 관리
4. 음식 이미지 분석 및 영양 정보 제공
5. 운동 및 생활습관 개선 조언

항상 친근하고 전문적인 톤으로 응답하며, 사용자의 개인 정보를 바탕으로 맞춤형 조언을 제공하세요.
안전하고 건강한 다이어트 방법만을 추천하고, 극단적인 방법은 권하지 마세요.
"""

    try:
        print("Bedrock Agent 생성 중...")
        
        response = bedrock_agent.create_agent(
            agentName=agent_name,
            description="AI 다이어트 코치 - 개인 맞춤형 식단 및 건강 조언 제공",
            foundationModel=foundation_model,
            instruction=instruction,
            agentResourceRoleArn=role_arn,
            idleSessionTTLInSeconds=1800
        )
        
        agent_id = response['agent']['agentId']
        print(f"Agent 생성 완료! ID: {agent_id}")
        
        # Agent 준비
        print("Agent 준비 중...")
        bedrock_agent.prepare_agent(agentId=agent_id)
        
        # 준비 완료 대기
        max_wait = 300  # 5분
        wait_time = 0
        
        while wait_time < max_wait:
            get_response = bedrock_agent.get_agent(agentId=agent_id)
            status = get_response['agent']['agentStatus']
            print(f"Agent 상태: {status}")
            
            if status == 'PREPARED':
                break
            elif status == 'FAILED':
                print("Agent 준비 실패!")
                return None
            
            time.sleep(10)
            wait_time += 10
        
        if wait_time >= max_wait:
            print("Agent 준비 시간 초과")
            return None
        
        # Agent Alias 생성
        print("Agent Alias 생성 중...")
        alias_response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName="DietCoachAlias",
            description="Diet Coach Agent Alias"
        )
        
        agent_alias_id = alias_response['agentAlias']['agentAliasId']
        print(f"Agent Alias 생성 완료! ID: {agent_alias_id}")
        
        # 설정 파일 저장
        config = {
            "agent_id": agent_id,
            "agent_alias_id": agent_alias_id,
            "agent_name": agent_name,
            "region": "ap-northeast-2",
            "model": foundation_model,
            "role_arn": role_arn,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        config_path = '/home/ec2-user/backend/bedrock_agent_config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== Bedrock Agent 생성 완료 ===")
        print(f"Agent ID: {agent_id}")
        print(f"Agent Alias ID: {agent_alias_id}")
        print(f"설정 파일: {config_path}")
        
        return config
        
    except Exception as e:
        print(f"Bedrock Agent 생성 오류: {e}")
        return None

def test_agent(config):
    """생성된 Agent 테스트"""
    
    bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='ap-northeast-2')
    
    try:
        print("\nAgent 테스트 중...")
        
        response = bedrock_agent_runtime.invoke_agent(
            agentId=config['agent_id'],
            agentAliasId=config['agent_alias_id'],
            sessionId='test123',
            inputText='안녕하세요! 다이어트 조언을 부탁드립니다.'
        )
        
        # 응답 처리
        agent_response = ""
        for event in response['completion']:
            if 'chunk' in event:
                chunk = event['chunk']
                if 'bytes' in chunk:
                    agent_response += chunk['bytes'].decode('utf-8')
        
        print(f"Agent 응답: {agent_response[:200]}...")
        print("Agent 테스트 성공!")
        
        return True
        
    except Exception as e:
        print(f"Agent 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("=== Bedrock Agent 생성 시작 ===")
    
    config = create_bedrock_agent()
    
    if config:
        print("\n=== Agent 테스트 ===")
        test_success = test_agent(config)
        
        if test_success:
            print("\n✅ Bedrock Agent 설정 완료!")
            print("이제 애플리케이션에서 Agent를 사용할 수 있습니다.")
        else:
            print("\n⚠️ Agent는 생성되었지만 테스트에 실패했습니다.")
    else:
        print("\n❌ Agent 생성에 실패했습니다.")