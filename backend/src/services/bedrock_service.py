"""
Bedrock 서비스 모듈
AI 모델을 통한 이미지 분석, 자연어 처리, 코칭 메시지 생성
"""

import json
import base64
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError

from ..config.aws_config import aws_config, aws_resources
from ..models.data_models import FoodItem, NutritionInfo, CoachingMessage, UserProfile
from ..utils.logger import setup_logger
from ..utils.helpers import generate_unique_id

logger = setup_logger(__name__)


class BedrockService:
    """Bedrock AI 서비스 관리 클래스"""
    
    def __init__(self):
        """Bedrock 서비스 초기화"""
        self.client = aws_config.bedrock_client
        self.model_id = aws_resources.bedrock_model_id
        self.image_model_id = aws_resources.bedrock_image_model_id
    
    async def analyze_food_image(
        self,
        image_data: bytes,
        people_count: int = 1
    ) -> List[FoodItem]:
        """
        음식 이미지 분석
        
        Args:
            image_data: 이미지 바이트 데이터
            people_count: 함께 식사한 인원 수
        
        Returns:
            분석된 음식 항목 리스트
        """
        try:
            # 이미지를 base64로 인코딩
            image_base64 = base64.b64encode(image_data).decode('utf-8')
            
            # 프롬프트 구성
            prompt = self._create_food_analysis_prompt(people_count)
            
            # Bedrock 호출
            response = await self._invoke_bedrock_with_image(
                prompt=prompt,
                image_base64=image_base64,
                model_id=self.image_model_id
            )
            
            # 응답 파싱
            food_items = self._parse_food_analysis_response(response)
            
            logger.info(f"Successfully analyzed food image: {len(food_items)} items found")
            return food_items
            
        except Exception as e:
            logger.error(f"Failed to analyze food image: {e}")
            return []
    
    async def generate_coaching_message(
        self,
        user_profile: UserProfile,
        recent_meals: List[Dict[str, Any]],
        context: str = ""
    ) -> CoachingMessage:
        """
        개인 맞춤형 코칭 메시지 생성
        
        Args:
            user_profile: 사용자 프로필
            recent_meals: 최근 식사 기록
            context: 추가 컨텍스트
        
        Returns:
            생성된 코칭 메시지
        """
        try:
            # 프롬프트 구성
            prompt = self._create_coaching_prompt(user_profile, recent_meals, context)
            
            # Bedrock 호출
            response = await self._invoke_bedrock_text(prompt)
            
            # 코칭 메시지 생성
            coaching_message = CoachingMessage(
                message_id=generate_unique_id("coaching"),
                user_id=user_profile.user_id,
                message_type="advice",
                content=response.strip(),
                is_voice=False,
                priority="normal"
            )
            
            logger.info(f"Generated coaching message for user: {user_profile.user_id}")
            return coaching_message
            
        except Exception as e:
            logger.error(f"Failed to generate coaching message: {e}")
            # 기본 메시지 반환
            return CoachingMessage(
                message_id=generate_unique_id("coaching"),
                user_id=user_profile.user_id,
                message_type="advice",
                content="건강한 식습관을 유지하세요!",
                is_voice=False,
                priority="normal"
            )
    
    async def process_natural_language(
        self,
        user_input: str,
        user_profile: UserProfile,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        자연어 처리 및 의도 분석
        
        Args:
            user_input: 사용자 입력
            user_profile: 사용자 프로필
            conversation_history: 대화 기록
        
        Returns:
            처리된 결과 (의도, 엔티티, 응답 등)
        """
        try:
            # 프롬프트 구성
            prompt = self._create_nlp_prompt(user_input, user_profile, conversation_history)
            
            # Bedrock 호출
            response = await self._invoke_bedrock_text(prompt)
            
            # 응답 파싱
            result = self._parse_nlp_response(response)
            
            logger.info(f"Processed natural language input: {user_input[:50]}...")
            return result
            
        except Exception as e:
            logger.error(f"Failed to process natural language: {e}")
            return {
                "intent": "unknown",
                "entities": {},
                "response": "죄송합니다. 다시 말씀해 주시겠어요?",
                "confidence": 0.0
            }
    
    async def generate_diet_recommendations(
        self,
        user_profile: UserProfile,
        current_nutrition: NutritionInfo,
        target_nutrition: NutritionInfo
    ) -> List[Dict[str, Any]]:
        """
        개인 맞춤형 식단 추천 생성
        
        Args:
            user_profile: 사용자 프로필
            current_nutrition: 현재 섭취 영양소
            target_nutrition: 목표 영양소
        
        Returns:
            식단 추천 리스트
        """
        try:
            # 프롬프트 구성
            prompt = self._create_diet_recommendation_prompt(
                user_profile, current_nutrition, target_nutrition
            )
            
            # Bedrock 호출
            response = await self._invoke_bedrock_text(prompt)
            
            # 응답 파싱
            recommendations = self._parse_diet_recommendations(response)
            
            logger.info(f"Generated diet recommendations for user: {user_profile.user_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to generate diet recommendations: {e}")
            return []
    
    async def _invoke_bedrock_with_image(
        self,
        prompt: str,
        image_base64: str,
        model_id: str
    ) -> str:
        """
        이미지와 함께 Bedrock 모델 호출
        
        Args:
            prompt: 텍스트 프롬프트
            image_base64: Base64 인코딩된 이미지
            model_id: 사용할 모델 ID
        
        Returns:
            모델 응답
        """
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
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
        
        response = self.client.converse(
            modelId=model_id,
            messages=body['messages']
        )
        
        return response['output']['message']['content'][0]['text']
    
    async def _invoke_bedrock_text(self, prompt: str) -> str:
        """
        텍스트 전용 Bedrock 모델 호출
        
        Args:
            prompt: 텍스트 프롬프트
        
        Returns:
            모델 응답
        """
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = self.client.converse(
            modelId=self.model_id,
            messages=body['messages']
        )
        
        return response['output']['message']['content'][0]['text']
    
    def _create_food_analysis_prompt(self, people_count: int) -> str:
        """음식 분석용 프롬프트 생성"""
        return f"""
이 음식 이미지를 분석하여 다음 정보를 JSON 형태로 제공해주세요:

1. 이미지에서 식별되는 모든 음식 항목
2. 각 음식의 예상 섭취량 (총 {people_count}명이 함께 식사한다고 가정하여 1인분 계산)
3. 각 음식의 영양소 정보 (칼로리, 탄수화물, 단백질, 지방)
4. 분석 신뢰도 (0-1 사이)

응답 형식:
{{
  "foods": [
    {{
      "name": "음식명",
      "quantity": "1인분 섭취량",
      "nutrition": {{
        "calories": 칼로리,
        "carbohydrates": 탄수화물(g),
        "protein": 단백질(g),
        "fat": 지방(g)
      }},
      "confidence": 신뢰도
    }}
  ]
}}

정확한 분석을 위해 한국 음식 기준으로 영양소를 계산해주세요.
"""
    
    def _create_coaching_prompt(
        self,
        user_profile: UserProfile,
        recent_meals: List[Dict[str, Any]],
        context: str
    ) -> str:
        """코칭 메시지 생성용 프롬프트 생성"""
        meals_summary = "\n".join([
            f"- {meal.get('meal_type', '식사')}: {meal.get('total_calories', 0)}kcal"
            for meal in recent_meals[-5:]  # 최근 5끼
        ])
        
        return f"""
사용자 프로필:
- 이름: {user_profile.name}
- 나이: {user_profile.age}세
- 건강 목표: {user_profile.health_goal.value}
- 선호 운동: {', '.join([ex.value for ex in user_profile.preferred_exercises])}
- 목표 칼로리: {user_profile.target_calories}kcal

최근 식사 기록:
{meals_summary}

추가 컨텍스트: {context}

위 정보를 바탕으로 개인 맞춤형 코칭 메시지를 생성해주세요.
- 친근하고 격려하는 톤으로 작성
- 구체적이고 실행 가능한 조언 포함
- 100자 내외로 간결하게 작성
- 사용자의 목표와 현재 상황을 고려한 맞춤형 내용
"""
    
    def _create_nlp_prompt(
        self,
        user_input: str,
        user_profile: UserProfile,
        conversation_history: List[Dict[str, str]]
    ) -> str:
        """자연어 처리용 프롬프트 생성"""
        history_text = ""
        if conversation_history:
            history_text = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history[-5:]  # 최근 5개 대화
            ])
        
        return f"""
사용자 입력: "{user_input}"

사용자 프로필:
- 건강 목표: {user_profile.health_goal.value}
- 선호 운동: {', '.join([ex.value for ex in user_profile.preferred_exercises])}

대화 기록:
{history_text}

다음 형식으로 분석 결과를 JSON으로 제공해주세요:
{{
  "intent": "의도 (food_inquiry, exercise_advice, progress_check, general_chat 등)",
  "entities": {{
    "food_items": ["언급된 음식들"],
    "exercise_types": ["언급된 운동들"],
    "time_references": ["시간 관련 표현들"]
  }},
  "response": "사용자에게 제공할 응답",
  "confidence": 분석_신뢰도
}}

친근하고 도움이 되는 응답을 생성해주세요.
"""
    
    def _create_diet_recommendation_prompt(
        self,
        user_profile: UserProfile,
        current_nutrition: NutritionInfo,
        target_nutrition: NutritionInfo
    ) -> str:
        """식단 추천용 프롬프트 생성"""
        return f"""
사용자 프로필:
- 건강 목표: {user_profile.health_goal.value}
- 식이 제한사항: {', '.join(user_profile.dietary_restrictions) if user_profile.dietary_restrictions else '없음'}

현재 영양소 섭취:
- 칼로리: {current_nutrition.calories}kcal
- 탄수화물: {current_nutrition.carbohydrates}g
- 단백질: {current_nutrition.protein}g
- 지방: {current_nutrition.fat}g

목표 영양소:
- 칼로리: {target_nutrition.calories}kcal
- 탄수화물: {target_nutrition.carbohydrates}g
- 단백질: {target_nutrition.protein}g
- 지방: {target_nutrition.fat}g

부족한 영양소를 보충할 수 있는 식단을 추천해주세요.
다음 형식으로 JSON 응답을 제공해주세요:

{{
  "recommendations": [
    {{
      "meal_type": "식사 종류",
      "foods": ["추천 음식 목록"],
      "nutrition_benefit": "영양학적 이점",
      "preparation_tip": "조리 팁"
    }}
  ]
}}

한국 음식 위주로 실용적인 추천을 해주세요.
"""
    
    def _parse_food_analysis_response(self, response: str) -> List[FoodItem]:
        """음식 분석 응답 파싱"""
        try:
            # JSON 추출
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return []
            
            data = json.loads(json_match.group())
            food_items = []
            
            for food_data in data.get('foods', []):
                nutrition = NutritionInfo(
                    calories=food_data['nutrition']['calories'],
                    carbohydrates=food_data['nutrition']['carbohydrates'],
                    protein=food_data['nutrition']['protein'],
                    fat=food_data['nutrition']['fat']
                )
                
                food_item = FoodItem(
                    name=food_data['name'],
                    quantity=food_data['quantity'],
                    nutrition=nutrition,
                    confidence=food_data['confidence']
                )
                
                food_items.append(food_item)
            
            return food_items
            
        except Exception as e:
            logger.error(f"Failed to parse food analysis response: {e}")
            return []
    
    def _parse_nlp_response(self, response: str) -> Dict[str, Any]:
        """자연어 처리 응답 파싱"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "intent": "general_chat",
                    "entities": {},
                    "response": response.strip(),
                    "confidence": 0.5
                }
        except Exception as e:
            logger.error(f"Failed to parse NLP response: {e}")
            return {
                "intent": "unknown",
                "entities": {},
                "response": "죄송합니다. 다시 말씀해 주시겠어요?",
                "confidence": 0.0
            }
    
    def _parse_diet_recommendations(self, response: str) -> List[Dict[str, Any]]:
        """식단 추천 응답 파싱"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return data.get('recommendations', [])
            else:
                return []
        except Exception as e:
            logger.error(f"Failed to parse diet recommendations: {e}")
            return []


# 전역 인스턴스
bedrock_service = BedrockService()