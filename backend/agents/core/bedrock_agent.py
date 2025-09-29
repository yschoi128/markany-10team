"""
AWS Bedrock Agent를 사용한 진짜 Agentic AI Diet Coach
"""

import boto3
import json
from typing import Dict, Any, Optional
from datetime import datetime
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from src.services.bedrock_service import BedrockService

class BedrockAgentDietCoach:
    """AWS Bedrock Agent 기반 자율적 AI 식단 코치"""
    
    def __init__(self):
        self.bedrock_agent = boto3.client(
            'bedrock-agent-runtime',
            region_name='us-east-1'
        )
        
        # Bedrock Agent ID (실제 생성된 Agent ID로 교체 필요)
        self.agent_id = "DIET_COACH_AGENT"
        self.agent_alias_id = "TSTALIASID"
    
    async def process_input(
        self,
        user_input: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Bedrock Agent를 통한 완전 자율적 처리"""
        try:
            # Bedrock Agent 호출
            response = self.bedrock_agent.invoke_agent(
                agentId=self.agent_id,
                agentAliasId=self.agent_alias_id,
                sessionId=user_id,
                inputText=user_input
            )
            
            # 응답 스트림 처리
            agent_response = ""
            for event in response['completion']:
                if 'chunk' in event:
                    chunk = event['chunk']
                    if 'bytes' in chunk:
                        agent_response += chunk['bytes'].decode('utf-8')
            
            return {
                "success": True,
                "response": agent_response,
                "agent_used": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            # Bedrock Agent 실패 시 Claude 직접 호출
            return await self._fallback_to_claude(user_input, user_id, context)
    
    async def _fallback_to_claude(
        self,
        user_input: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """최적화된 Claude 호출 폴백"""
        try:
            # 이미지가 있는 경우 이미지 분석 프롬프트 사용
            if context and "image_data" in context:
                agentic_prompt = f"""
당신은 AI 식단 코치 에이전트입니다. 사용자가 업로드한 음식 이미지를 분석하고 영양 정보를 제공하세요.

사용자 메시지: "{user_input}"
이미지 파일명: {context.get('image_filename', '알 수 없음')}

이미지를 분석하여 다음 정보를 제공하세요:
1. 음식 종류 식별
2. 예상 칼로리 및 영양소
3. 건강한 식사를 위한 조언
4. 대체 메뉴 제안

친근하고 전문적인 톤으로 응답하세요.
"""
                return await self._analyze_food_image(agentic_prompt, context["image_data"], user_id)
            else:
                # 텍스트 전용 프롬프트
                agentic_prompt = f"""
당신은 AI 식단 코치 에이전트입니다. 사용자의 요청을 분석하고 적절한 조치를 취하세요.

사용자 요청: "{user_input}"
사용자 ID: {user_id}

다음 중 적절한 행동을 선택하고 실행하세요:
1. 식단 추천 - 건강한 메뉴 제안
2. 운동 조언 - 적절한 운동 추천  
3. 영양 분석 - 칼로리/영양소 정보 제공
4. 일반 상담 - 건강 관련 조언

응답은 친근하고 전문적으로 작성하세요.
"""
            
            # 직접 Bedrock 클라이언트 사용
            bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name='us-east-1'
            )
            
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": agentic_prompt
                    }
                ]
            }
            
            response = bedrock_client.invoke_model(
                modelId='us.anthropic.claude-3-5-sonnet-20240620-v1:0',
                body=json.dumps(body)
            )
            
            response_body = json.loads(response['body'].read())
            claude_response = response_body['content'][0]['text']
            
            return {
                "success": True,
                "response": claude_response,
                "agent_used": False,
                "fallback": "claude",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "죄송합니다. 현재 서비스에 문제가 있습니다.",
                "timestamp": datetime.now().isoformat()
            }

    async def _analyze_food_image(
        self,
        prompt: str,
        image_data: bytes,
        user_id: str
    ) -> Dict[str, Any]:
        """음식 이미지 분석"""
        try:
            print(f"Starting image analysis for user: {user_id}")
            print(f"Image data size: {len(image_data)} bytes")
            import base64
            
            # 이미지 타입 감지
            media_type = "image/jpeg"
            if image_data.startswith(b'\x89PNG'):
                media_type = "image/png"
            elif image_data.startswith(b'\xff\xd8\xff'):
                media_type = "image/jpeg"
            elif image_data.startswith(b'GIF'):
                media_type = "image/gif"
            
            print(f"Detected media type: {media_type}")
            
            # 이미지를 base64로 인코딩
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            print(f"Base64 encoded image length: {len(image_base64)}")
            
            bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name='us-east-1'
            )
            
            # Claude 3 Sonnet 이미지 분석을 위한 올바른 형식
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            }
            
            print(f"Sending request to Bedrock with model: anthropic.claude-3-5-sonnet-20240620-v1:0")
            response = bedrock_client.invoke_model(
                modelId='anthropic.claude-3-5-sonnet-20240620-v1:0',
                body=json.dumps(body)
            )
            print("Received response from Bedrock")
            
            response_body = json.loads(response['body'].read())
            claude_response = response_body['content'][0]['text']
            
            return {
                "success": True,
                "response": claude_response,
                "agent_used": False,
                "image_analyzed": True,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            import traceback
            error_msg = f"Image analysis error: {str(e)}\nTraceback: {traceback.format_exc()}"
            print(error_msg)  # 콘솔에 출력
            return {
                "success": False,
                "error": str(e),
                "response": "이미지 분석에 실패했습니다. 다시 시도해 주세요.",
                "timestamp": datetime.now().isoformat()
            }


# 전역 인스턴스
bedrock_agent_coach = BedrockAgentDietCoach()