#!/usr/bin/env python3
"""
간단한 Bedrock Agent 설정 스크립트
"""

import boto3
import json

def get_account_id():
    """현재 AWS 계정 ID 조회"""
    sts = boto3.client('sts')
    return sts.get_caller_identity()['Account']

def setup_agent_config():
    """기존 Agent가 있는지 확인하고 설정 파일 생성"""
    
    account_id = get_account_id()
    print(f"AWS Account ID: {account_id}")
    
    # Bedrock Agent 클라이언트
    bedrock_agent = boto3.client('bedrock-agent', region_name='ap-northeast-2')
    
    try:
        # 기존 Agent 목록 조회
        response = bedrock_agent.list_agents()
        agents = response.get('agentSummaries', [])
        
        print(f"Found {len(agents)} existing agents:")
        for agent in agents:
            print(f"- {agent['agentName']} (ID: {agent['agentId']}, Status: {agent['agentStatus']})")
        
        # Diet Coach Agent 찾기
        diet_coach_agent = None
        for agent in agents:
            if 'diet' in agent['agentName'].lower() or 'coach' in agent['agentName'].lower():
                diet_coach_agent = agent
                break
        
        if diet_coach_agent:
            agent_id = diet_coach_agent['agentId']
            print(f"\nFound Diet Coach Agent: {agent_id}")
            
            # Agent Alias 조회
            aliases_response = bedrock_agent.list_agent_aliases(agentId=agent_id)
            aliases = aliases_response.get('agentAliasSummaries', [])
            
            if aliases:
                agent_alias_id = aliases[0]['agentAliasId']
                print(f"Found Agent Alias: {agent_alias_id}")
            else:
                print("No aliases found. Creating new alias...")
                alias_response = bedrock_agent.create_agent_alias(
                    agentId=agent_id,
                    agentAliasName="DietCoachAlias"
                )
                agent_alias_id = alias_response['agentAlias']['agentAliasId']
                print(f"Created new alias: {agent_alias_id}")
            
            # 설정 파일 생성
            config = {
                "agent_id": agent_id,
                "agent_alias_id": agent_alias_id,
                "region": "ap-northeast-2"
            }
            
            with open('/home/ec2-user/backend/bedrock_agent_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"\n설정 완료!")
            print(f"Agent ID: {agent_id}")
            print(f"Alias ID: {agent_alias_id}")
            
            return config
        else:
            print("\nDiet Coach Agent를 찾을 수 없습니다.")
            print("AWS 콘솔에서 수동으로 Agent를 생성하거나 create_bedrock_agent.py를 실행하세요.")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    setup_agent_config()