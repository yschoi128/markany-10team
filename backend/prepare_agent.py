#!/usr/bin/env python3
"""
생성된 Agent 준비 및 설정 완료
"""

import boto3
import json
import time
from dotenv import load_dotenv

load_dotenv()

def prepare_existing_agent():
    """기존 생성된 Agent 준비"""
    
    bedrock_agent = boto3.client('bedrock-agent', region_name='ap-northeast-2')
    
    # 생성된 Agent ID
    agent_id = "RYOWPEXFEG"
    
    try:
        # Agent 상태 확인
        get_response = bedrock_agent.get_agent(agentId=agent_id)
        status = get_response['agent']['agentStatus']
        print(f"현재 Agent 상태: {status}")
        
        if status == 'NOT_PREPARED':
            print("Agent 준비 시작...")
            bedrock_agent.prepare_agent(agentId=agent_id)
        
        # 준비 완료 대기
        max_wait = 300  # 5분
        wait_time = 0
        
        while wait_time < max_wait:
            get_response = bedrock_agent.get_agent(agentId=agent_id)
            status = get_response['agent']['agentStatus']
            print(f"Agent 상태: {status} (대기 시간: {wait_time}초)")
            
            if status == 'PREPARED':
                print("Agent 준비 완료!")
                break
            elif status == 'FAILED':
                print("Agent 준비 실패!")
                return None
            
            time.sleep(10)
            wait_time += 10
        
        if status != 'PREPARED':
            print("Agent 준비 시간 초과")
            return None
        
        # Agent Alias 생성
        print("Agent Alias 생성 중...")
        try:
            alias_response = bedrock_agent.create_agent_alias(
                agentId=agent_id,
                agentAliasName="DietCoachAlias",
                description="Diet Coach Agent Alias"
            )
            agent_alias_id = alias_response['agentAlias']['agentAliasId']
            print(f"Agent Alias 생성 완료! ID: {agent_alias_id}")
        except Exception as e:
            if "already exists" in str(e):
                # 기존 Alias 조회
                aliases = bedrock_agent.list_agent_aliases(agentId=agent_id)
                agent_alias_id = aliases['agentAliasSummaries'][0]['agentAliasId']
                print(f"기존 Agent Alias 사용: {agent_alias_id}")
            else:
                raise e
        
        # 설정 파일 저장
        config = {
            "agent_id": agent_id,
            "agent_alias_id": agent_alias_id,
            "agent_name": "DietCoach",
            "region": "ap-northeast-2",
            "model": "anthropic.claude-3-haiku-20240307-v1:0",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        config_path = '/home/ec2-user/backend/bedrock_agent_config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"\n=== Bedrock Agent 설정 완료 ===")
        print(f"Agent ID: {agent_id}")
        print(f"Agent Alias ID: {agent_alias_id}")
        print(f"설정 파일: {config_path}")
        
        return config
        
    except Exception as e:
        print(f"Agent 준비 오류: {e}")
        return None

def test_agent(config):
    """Agent 테스트"""
    
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
        print("✅ Agent 테스트 성공!")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    print("=== Bedrock Agent 준비 시작 ===")
    
    config = prepare_existing_agent()
    
    if config:
        test_success = test_agent(config)
        
        if test_success:
            print("\n🎉 Bedrock Agent 완전히 설정 완료!")
            print("이제 애플리케이션에서 Agent를 사용할 수 있습니다.")
        else:
            print("\n⚠️ Agent는 준비되었지만 테스트에 실패했습니다.")
    else:
        print("\n❌ Agent 준비에 실패했습니다.")