#!/usr/bin/env python3
"""
Bedrock Agent 생성 스크립트
"""

import boto3
import json
import time
from datetime import datetime

def create_bedrock_agent():
    """AI 다이어트 코치 Bedrock Agent 생성"""
    
    # Bedrock Agent 클라이언트
    bedrock_agent = boto3.client('bedrock-agent', region_name='ap-northeast-2')
    
    # Agent 설정
    agent_name = "DietCoach"
    agent_description = "AI 다이어트 코치 - 개인 맞춤형 식단 및 건강 조언 제공"
    
    # Foundation Model ARN (Claude 3 Haiku)
    foundation_model = "anthropic.claude-3-haiku-20240307-v1:0"
    
    # Agent 역할 ARN (미리 생성된 IAM 역할 필요)
    agent_role_arn = "arn:aws:iam::YOUR_ACCOUNT_ID:role/AmazonBedrockExecutionRoleForAgents_DietCoach"
    
    # Agent 지침
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
        # Agent 생성
        print("Creating Bedrock Agent...")
        response = bedrock_agent.create_agent(
            agentName=agent_name,
            description=agent_description,
            foundationModel=foundation_model,
            instruction=instruction,
            agentResourceRoleArn=agent_role_arn,
            idleSessionTTLInSeconds=1800,  # 30분
            tags={
                'Project': 'AI-Diet-Coach',
                'Environment': 'Development'
            }
        )
        
        agent_id = response['agent']['agentId']
        print(f"Agent created successfully! Agent ID: {agent_id}")
        
        # Agent 준비 (Prepare)
        print("Preparing agent...")
        prepare_response = bedrock_agent.prepare_agent(agentId=agent_id)
        print(f"Agent preparation status: {prepare_response['agentStatus']}")
        
        # Agent 준비 완료 대기
        while True:
            get_response = bedrock_agent.get_agent(agentId=agent_id)
            status = get_response['agent']['agentStatus']
            print(f"Current status: {status}")
            
            if status == 'PREPARED':
                break
            elif status == 'FAILED':
                print("Agent preparation failed!")
                return None
            
            time.sleep(10)
        
        # Agent Alias 생성
        print("Creating agent alias...")
        alias_response = bedrock_agent.create_agent_alias(
            agentId=agent_id,
            agentAliasName="DietCoachAlias",
            description="Diet Coach Agent Alias for production use"
        )
        
        agent_alias_id = alias_response['agentAlias']['agentAliasId']
        print(f"Agent alias created! Alias ID: {agent_alias_id}")
        
        # 설정 파일 생성
        config = {
            "agent_id": agent_id,
            "agent_alias_id": agent_alias_id,
            "agent_name": agent_name,
            "created_at": datetime.now().isoformat(),
            "region": "ap-northeast-2"
        }
        
        with open('/home/ec2-user/backend/bedrock_agent_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("\n=== Bedrock Agent 생성 완료 ===")
        print(f"Agent ID: {agent_id}")
        print(f"Agent Alias ID: {agent_alias_id}")
        print("설정이 bedrock_agent_config.json에 저장되었습니다.")
        
        return {
            "agent_id": agent_id,
            "agent_alias_id": agent_alias_id
        }
        
    except Exception as e:
        print(f"Error creating Bedrock Agent: {e}")
        return None

def create_iam_role():
    """Bedrock Agent용 IAM 역할 생성"""
    
    iam = boto3.client('iam')
    
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
    
    # 권한 정책
    permissions_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "bedrock:InvokeModel",
                    "bedrock:InvokeModelWithResponseStream"
                ],
                "Resource": "*"
            },
            {
                "Effect": "Allow",
                "Action": [
                    "dynamodb:GetItem",
                    "dynamodb:PutItem",
                    "dynamodb:UpdateItem",
                    "dynamodb:Query",
                    "dynamodb:Scan"
                ],
                "Resource": [
                    "arn:aws:dynamodb:ap-northeast-2:*:table/user_profiles",
                    "arn:aws:dynamodb:ap-northeast-2:*:table/diet_records",
                    "arn:aws:dynamodb:ap-northeast-2:*:table/schedule_records"
                ]
            }
        ]
    }
    
    try:
        # IAM 역할 생성
        role_name = "AmazonBedrockExecutionRoleForAgents_DietCoach"
        
        print("Creating IAM role...")
        role_response = iam.create_role(
            RoleName=role_name,
            AssumeRolePolicyDocument=json.dumps(trust_policy),
            Description="Execution role for Bedrock Agent - Diet Coach"
        )
        
        role_arn = role_response['Role']['Arn']
        print(f"IAM role created: {role_arn}")
        
        # 권한 정책 연결
        policy_name = "BedrockAgentDietCoachPolicy"
        iam.put_role_policy(
            RoleName=role_name,
            PolicyName=policy_name,
            PolicyDocument=json.dumps(permissions_policy)
        )
        
        print(f"Policy attached: {policy_name}")
        return role_arn
        
    except Exception as e:
        print(f"Error creating IAM role: {e}")
        return None

if __name__ == "__main__":
    print("=== Bedrock Agent 설정 시작 ===")
    
    # 1. IAM 역할 생성
    print("\n1. IAM 역할 생성...")
    role_arn = create_iam_role()
    
    if role_arn:
        print(f"IAM 역할이 생성되었습니다: {role_arn}")
        print("\n잠시 후 Agent를 생성합니다... (IAM 역할 전파 대기)")
        time.sleep(30)  # IAM 역할 전파 대기
        
        # 2. Bedrock Agent 생성
        print("\n2. Bedrock Agent 생성...")
        result = create_bedrock_agent()
        
        if result:
            print("\n=== 설정 완료 ===")
            print("이제 bedrock_agent.py에서 Agent를 사용할 수 있습니다.")
        else:
            print("Agent 생성에 실패했습니다.")
    else:
        print("IAM 역할 생성에 실패했습니다.")