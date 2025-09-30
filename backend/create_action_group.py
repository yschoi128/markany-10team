#!/usr/bin/env python3
"""
Bedrock Agent용 Action Group 생성
"""

import boto3
import json
from dotenv import load_dotenv

load_dotenv()

def create_action_group():
    agent_client = boto3.client('bedrock-agent', region_name='ap-northeast-2')
    
    # Action Group API Schema 정의
    api_schema = {
        "openapi": "3.0.0",
        "info": {
            "title": "Diet Coach API",
            "version": "1.0.0",
            "description": "AI 다이어트 코치 도구들"
        },
        "paths": {
            "/get_user_profile": {
                "post": {
                    "description": "사용자 프로필 조회",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "query",
                            "required": True,
                            "schema": {"type": "string"},
                            "description": "사용자 ID"
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "사용자 프로필 정보",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "name": {"type": "string"},
                                            "age": {"type": "integer"},
                                            "height": {"type": "number"},
                                            "weight": {"type": "number"},
                                            "bmi": {"type": "number"},
                                            "target_calories": {"type": "number"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    try:
        # Action Group 생성
        response = agent_client.create_agent_action_group(
            agentId='RYOWPEXFEG',
            agentVersion='DRAFT',
            actionGroupName='DietCoachTools',
            description='AI 다이어트 코치 도구들',
            actionGroupExecutor={
                'lambda': 'arn:aws:lambda:ap-northeast-2:322569618444:function:diet-coach-tools'
            },
            apiSchema={
                'payload': json.dumps(api_schema)
            },
            actionGroupState='ENABLED'
        )
        
        print("✅ Action Group 생성 성공!")
        print(f"Action Group ID: {response['agentActionGroup']['actionGroupId']}")
        
        # Agent 준비
        prepare_response = agent_client.prepare_agent(agentId='RYOWPEXFEG')
        print("✅ Agent 준비 완료!")
        
    except Exception as e:
        print(f"❌ Action Group 생성 실패: {e}")

if __name__ == "__main__":
    create_action_group()