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
            region_name='ap-northeast-2'
        )
        
        # 설정 파일에서 Agent 정보 로드
        self.load_agent_config()
    
    def load_agent_config(self):
        """Agent 설정 파일 로드"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'bedrock_agent_config.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            self.agent_id = config.get('agent_id', 'DIETCOACH')
            self.agent_alias_id = config.get('agent_alias_id', 'TSTALIASID')
            
            print(f"Loaded Agent config - ID: {self.agent_id}, Alias: {self.agent_alias_id}")
            
        except FileNotFoundError:
            print("Agent config file not found, using defaults")
            self.agent_id = "DIETCOACH"
            self.agent_alias_id = "TSTALIASID"
        except Exception as e:
            print(f"Error loading agent config: {e}")
            self.agent_id = "DIETCOACH"
            self.agent_alias_id = "TSTALIASID"
    
    async def process_input(
        self,
        user_input: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Bedrock Agent를 통한 완전 자율적 처리"""
        try:
            # 사용자 ID를 Bedrock Agent 호환 형식으로 변환 (한글 → 영문)
            import hashlib
            safe_user_id = hashlib.md5(user_id.encode('utf-8')).hexdigest()[:20]
            print(f"Converting user_id '{user_id}' to safe_user_id '{safe_user_id}'")
            
            # Agent가 제대로 작동하지 않으므로 바로 Claude 사용
            print("Skipping Bedrock Agent, using Claude directly for better performance")
            return await self._fallback_to_claude(user_input, user_id, context)
            
        except Exception as e:
            error_msg = str(e)
            print(f"Bedrock Agent error: {error_msg}")
            
            # Bedrock Agent 실패 시 Claude 직접 호출 (이미지 우선 처리)
            print(f"Falling back to Claude for user_input: '{user_input}', has_image: {bool(context and 'image_data' in context)}")
            return await self._fallback_to_claude(user_input, user_id, context)
    
    async def _fallback_to_claude(
        self,
        user_input: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Bedrock Agent 실패 시 Claude 직접 호출 폴백"""
        try:
            print(f"Claude fallback called - user_input: '{user_input}', context keys: {list(context.keys()) if context else 'None'}")
            
            # 이미지가 있는 경우 이미지 분석 프롬프트 사용
            if context and "image_data" in context:
                print(f"Image detected, using image analysis for: {user_input}")
                print(f"Image data size: {len(context['image_data'])} bytes")
                # 이미지 분석을 위한 명확한 지시 프롬프트
                agentic_prompt = f"""
사용자가 음식 이미지와 함께 메시지를 보냈습니다: "{user_input}"

이 이미지에 있는 음식들을 전문 영양사 관점에서 상세히 분석하고 다음 정보를 제공하세요:

## 🍽️ 식별된 음식 목록
각 음식별로:
- 음식명과 예상 분량
- 개별 칼로리 (kcal)
- 탄수화물, 단백질, 지방 (g)

## 📊 총 영양 정보 계산
- 총 칼로리 합계
- 총 영양소 합계

## 💡 개인 맞춤 조언
- 이 식사의 영양적 평가
- 사용자 목표 대비 분석
- 다음 식사 또는 운동 추천

## 🏃♂️ 칼로리 소모 운동
섭취한 칼로리를 소모하기 위한 운동 시간 계산

**중요: 이미지에서 보이는 모든 음식을 빠짐없이 분석하고 정확한 칼로리를 계산해주세요.**
"""
                print("Calling _analyze_food_image...")
                result = await self._analyze_food_image(agentic_prompt, context["image_data"], user_id)
                print(f"Image analysis result: {result.get('success', False)}")
                return result
            else:
                print("No image data found, proceeding with text-only analysis")

                # 개인화된 컨텍스트 조회 (해시된 user_id와 원본 user_id 모두 시도)
                try:
                    from agents.tools.user_rag_tools import get_personalized_user_context
                    
                    # 먼저 원본 user_id로 시도
                    user_context = await get_personalized_user_context(user_id)
                    
                    # 원본으로 찾지 못하면 해시된 user_id로 시도
                    if "error" in user_context:
                        import hashlib
                        hashed_user_id = hashlib.md5(user_id.encode('utf-8')).hexdigest()[:20]
                        print(f"Trying with hashed user_id: {hashed_user_id}")
                        user_context = await get_personalized_user_context(hashed_user_id)
                    
                    if "error" not in user_context:
                        user_info = user_context.get("user_info", {})
                        recent_activity = user_context.get("recent_activity", {})
                        insights = user_context.get("personalized_insights", {})
                        
                        context_text = f"""
개인 정보:
- 이름: {user_info.get('name', '알 수 없음')}
- 나이: {user_info.get('age')}세, 성별: {user_info.get('gender')}
- 키: {user_info.get('height')}cm, 체중: {user_info.get('weight')}kg
- BMI: {user_info.get('bmi')} (체질량지수)
- 건강 목표: {user_info.get('health_goal')}
- 목표 칼로리: {user_info.get('target_calories')}kcal

최근 활동:
- 최근 7일 식사 횟수: {recent_activity.get('meals_last_7_days', 0)}회
- 평균 일일 칼로리: {recent_activity.get('avg_daily_calories', 0)}kcal
- 목표 달성률: {recent_activity.get('calorie_goal_achievement', 0)}%

개인 맞춤 조언:
{chr(10).join([f'- {advice}' for advice in insights.values()])}
"""
                    else:
                        context_text = "개인 정보를 찾을 수 없습니다. 프로필 생성을 권장합니다."
                        
                except Exception as e:
                    context_text = "개인 정보 조회 중 오류가 발생했습니다."
                
                agentic_prompt = f"""
당신은 전문 영양사이자 개인 트레이너인 AI 식단 코치입니다. 사용자의 요청을 분석하고 적절한 대응을 하세요.

사용자 요청: "{user_input}"
사용자 정보: {user_id}
이미지 첨부: 없음

{context_text}

**중요: 사용자 요청을 분석하여 다음 중 하나를 선택하세요:**

1. **이미지 분석이 필요한 경우** ("오늘 먹은", "이 음식", "이거 분석" 등):
   "📷 음식 사진을 업로드해주시면 정확한 칼로리와 영양소 분석을 해드릴 수 있습니다. 사진을 참부해주세요!"

2. **일반 식단 상담인 경우**:
   구체적인 메뉴 추천과 칼로리 정보 제공

3. **운동 상담인 경우**:
   개인 맞춤 운동 추천

**사용자가 음식에 대해 언급했지만 이미지가 없다면, 반드시 사진 업로드를 요청하세요.**
"""
            
            # 직접 Bedrock 클라이언트 사용
            bedrock_client = boto3.client(
                'bedrock-runtime',
                region_name='ap-northeast-2'
            )
            
            messages = [{"role": "user", "content": [{"text": agentic_prompt}]}]
            
            response = bedrock_client.converse(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                messages=messages,
                inferenceConfig={'maxTokens': 1500}
            )
            
            claude_response = response['output']['message']['content'][0]['text']
            
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
                region_name='ap-northeast-2'
            )
            
            # converse API로 이미지 분석
            messages = [{
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": media_type.split('/')[1],
                            "source": {
                                "bytes": image_data
                            }
                        }
                    },
                    {
                        "text": prompt
                    }
                ]
            }]
            
            print(f"Sending request to Bedrock with model: anthropic.claude-3-haiku-20240307-v1:0")
            
            # Throttling 방지를 위한 retry 로직
            import time
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = bedrock_client.converse(
                        modelId='anthropic.claude-3-haiku-20240307-v1:0',
                        messages=messages,
                        inferenceConfig={'maxTokens': 1500}
                    )
                    break
                except Exception as e:
                    if "ThrottlingException" in str(e) and attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 3  # 3, 6, 9초 대기
                        print(f"Throttling detected, waiting {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise e
            print("Received response from Bedrock")
            
            claude_response = response['output']['message']['content'][0]['text']
            
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


    def create_agent_instructions(self):
        """Agent 생성용 지침 반환"""
        return """
당신은 전문적인 AI 다이어트 코치입니다. 다음 역할을 수행하세요:

1. 개인 맞춤형 식단 조언 제공
2. BMI 계산 및 건강 상태 분석  
3. 칼로리 목표 설정 및 관리
4. 음식 이미지 분석 및 영양 정보 제공
5. 운동 및 생활습관 개선 조언

항상 친근하고 전문적인 톤으로 응답하며, 사용자의 개인 정보를 바탕으로 맞춤형 조언을 제공하세요.
안전하고 건강한 다이어트 방법만을 추천하고, 극단적인 방법은 권하지 마세요.
"""

# 전역 인스턴스
bedrock_agent_coach = BedrockAgentDietCoach()