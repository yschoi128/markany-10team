"""
AI 코칭 파이프라인
개인 맞춤형 코칭 메시지 생성 및 관리
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..models.data_models import (
    UserProfile, MealRecord, CoachingMessage, 
    ExerciseRecommendation, DietRecommendation, DailyReport
)
from ..services.bedrock_service import bedrock_service
from ..services.dynamodb_service import dynamodb_service
from ..utils.logger import setup_logger
from ..utils.helpers import generate_unique_id, calculate_bmr, calculate_tdee

logger = setup_logger(__name__)


class CoachingPipeline:
    """AI 코칭 파이프라인 클래스"""
    
    def __init__(self):
        """파이프라인 초기화"""
        self.bedrock_service = bedrock_service
        self.dynamodb_service = dynamodb_service
    
    async def generate_daily_coaching(
        self,
        user_id: str,
        context: Optional[str] = None
    ) -> Optional[CoachingMessage]:
        """
        일일 코칭 메시지 생성
        
        Args:
            user_id: 사용자 ID
            context: 추가 컨텍스트 정보
        
        Returns:
            생성된 코칭 메시지
        """
        try:
            logger.info(f"Generating daily coaching for user: {user_id}")
            
            # 1. 사용자 프로필 조회
            user_profile = await self.dynamodb_service.get_user_profile(user_id)
            if not user_profile:
                logger.error(f"User profile not found: {user_id}")
                return None
            
            # 2. 최근 식사 기록 조회 (최근 3일)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=3)
            recent_meals = await self.dynamodb_service.get_user_meals(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                limit=20
            )
            
            # 3. 식사 기록을 딕셔너리 형태로 변환
            meals_data = []
            for meal in recent_meals:
                meals_data.append({
                    "meal_type": meal.meal_type,
                    "timestamp": meal.timestamp.isoformat(),
                    "total_calories": meal.total_nutrition.calories,
                    "foods": [food.name for food in meal.foods]
                })
            
            # 4. Bedrock으로 코칭 메시지 생성
            coaching_message = await self.bedrock_service.generate_coaching_message(
                user_profile=user_profile,
                recent_meals=meals_data,
                context=context or ""
            )
            
            logger.info(f"Successfully generated daily coaching: {coaching_message.message_id}")
            return coaching_message
            
        except Exception as e:
            logger.error(f"Error generating daily coaching: {e}")
            return None
    
    async def generate_meal_feedback(
        self,
        user_id: str,
        meal_record: MealRecord
    ) -> Optional[CoachingMessage]:
        """
        식사 후 즉시 피드백 생성
        
        Args:
            user_id: 사용자 ID
            meal_record: 식사 기록
        
        Returns:
            생성된 피드백 메시지
        """
        try:
            logger.info(f"Generating meal feedback for meal: {meal_record.meal_id}")
            
            # 1. 사용자 프로필 조회
            user_profile = await self.dynamodb_service.get_user_profile(user_id)
            if not user_profile:
                logger.error(f"User profile not found: {user_id}")
                return None
            
            # 2. 오늘의 영양소 섭취 현황 조회
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            daily_summary = await self.dynamodb_service.get_daily_nutrition_summary(
                user_id=user_id,
                date=today
            )
            
            # 3. 목표 대비 현재 섭취량 분석
            target_calories = user_profile.target_calories or self._calculate_target_calories(user_profile)
            current_calories = daily_summary.get('total_nutrition', {}).get('calories', 0)
            
            # 4. 컨텍스트 구성
            context = f"""
현재 식사: {meal_record.meal_type} - {meal_record.total_nutrition.calories}kcal
오늘 총 섭취: {current_calories}kcal / 목표: {target_calories}kcal
섭취 음식: {', '.join([food.name for food in meal_record.foods])}
"""
            
            # 5. 피드백 메시지 생성
            feedback_message = await self.bedrock_service.generate_coaching_message(
                user_profile=user_profile,
                recent_meals=[{
                    "meal_type": meal_record.meal_type,
                    "total_calories": meal_record.total_nutrition.calories,
                    "foods": [food.name for food in meal_record.foods]
                }],
                context=context
            )
            
            # 6. 메시지 타입 조정
            feedback_message.message_type = "meal_feedback"
            feedback_message.priority = "high" if current_calories > target_calories * 1.2 else "normal"
            
            logger.info(f"Successfully generated meal feedback: {feedback_message.message_id}")
            return feedback_message
            
        except Exception as e:
            logger.error(f"Error generating meal feedback: {e}")
            return None
    
    async def generate_weekly_report(
        self,
        user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        주간 리포트 생성
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            주간 리포트 데이터
        """
        try:
            logger.info(f"Generating weekly report for user: {user_id}")
            
            # 1. 사용자 프로필 조회
            user_profile = await self.dynamodb_service.get_user_profile(user_id)
            if not user_profile:
                logger.error(f"User profile not found: {user_id}")
                return None
            
            # 2. 지난 주 식사 기록 조회
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            weekly_meals = await self.dynamodb_service.get_user_meals(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            # 3. 주간 통계 계산
            weekly_stats = self._calculate_weekly_stats(weekly_meals, user_profile)
            
            # 4. 운동 추천 생성
            exercise_recommendations = await self._generate_exercise_recommendations(
                user_profile, weekly_stats
            )
            
            # 5. 식단 개선 제안 생성
            diet_improvements = await self._generate_diet_improvements(
                user_profile, weekly_stats
            )
            
            # 6. 주간 리포트 구성
            weekly_report = {
                "user_id": user_id,
                "report_period": {
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d")
                },
                "statistics": weekly_stats,
                "exercise_recommendations": exercise_recommendations,
                "diet_improvements": diet_improvements,
                "overall_assessment": self._generate_overall_assessment(weekly_stats),
                "generated_at": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully generated weekly report for user: {user_id}")
            return weekly_report
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return None
    
    async def process_user_conversation(
        self,
        user_id: str,
        user_input: str,
        conversation_history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        사용자 대화 처리 및 응답 생성
        
        Args:
            user_id: 사용자 ID
            user_input: 사용자 입력
            conversation_history: 대화 기록
        
        Returns:
            처리 결과 및 응답
        """
        try:
            logger.info(f"Processing user conversation: {user_input[:50]}...")
            
            # 1. 사용자 프로필 조회
            user_profile = await self.dynamodb_service.get_user_profile(user_id)
            if not user_profile:
                logger.error(f"User profile not found: {user_id}")
                return {"error": "사용자 정보를 찾을 수 없습니다."}
            
            # 2. 자연어 처리
            nlp_result = await self.bedrock_service.process_natural_language(
                user_input=user_input,
                user_profile=user_profile,
                conversation_history=conversation_history
            )
            
            # 3. 의도에 따른 추가 처리
            response_data = await self._handle_user_intent(
                user_id=user_id,
                intent=nlp_result.get("intent"),
                entities=nlp_result.get("entities", {}),
                user_profile=user_profile
            )
            
            # 4. 최종 응답 구성
            result = {
                "intent": nlp_result.get("intent"),
                "response": nlp_result.get("response"),
                "confidence": nlp_result.get("confidence"),
                "additional_data": response_data,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Successfully processed user conversation with intent: {nlp_result.get('intent')}")
            return result
            
        except Exception as e:
            logger.error(f"Error processing user conversation: {e}")
            return {"error": "대화 처리 중 오류가 발생했습니다."}
    
    def _calculate_target_calories(self, user_profile: UserProfile) -> float:
        """목표 칼로리 계산"""
        bmr = calculate_bmr(
            weight=user_profile.weight,
            height=user_profile.height,
            age=user_profile.age,
            gender=user_profile.gender
        )
        
        tdee = calculate_tdee(bmr, user_profile.activity_level)
        
        # 건강 목표에 따른 조정
        if user_profile.health_goal.value == "weight_loss":
            return tdee * 0.8  # 20% 감소
        elif user_profile.health_goal.value == "muscle_gain":
            return tdee * 1.1  # 10% 증가
        else:
            return tdee
    
    def _calculate_weekly_stats(
        self,
        meals: List[MealRecord],
        user_profile: UserProfile
    ) -> Dict[str, Any]:
        """주간 통계 계산"""
        if not meals:
            return {"message": "분석할 식사 기록이 없습니다."}
        
        total_calories = sum(meal.total_nutrition.calories for meal in meals)
        total_protein = sum(meal.total_nutrition.protein for meal in meals)
        total_carbs = sum(meal.total_nutrition.carbohydrates for meal in meals)
        total_fat = sum(meal.total_nutrition.fat for meal in meals)
        
        target_calories = self._calculate_target_calories(user_profile)
        target_weekly_calories = target_calories * 7
        
        return {
            "total_meals": len(meals),
            "average_meals_per_day": len(meals) / 7,
            "total_calories": round(total_calories, 2),
            "average_calories_per_day": round(total_calories / 7, 2),
            "target_calories_per_day": round(target_calories, 2),
            "calorie_achievement_rate": round((total_calories / target_weekly_calories) * 100, 1),
            "macronutrients": {
                "protein": round(total_protein, 2),
                "carbohydrates": round(total_carbs, 2),
                "fat": round(total_fat, 2)
            },
            "meal_frequency_by_type": self._analyze_meal_frequency(meals)
        }
    
    def _analyze_meal_frequency(self, meals: List[MealRecord]) -> Dict[str, int]:
        """식사 종류별 빈도 분석"""
        frequency = {}
        for meal in meals:
            meal_type = meal.meal_type
            frequency[meal_type] = frequency.get(meal_type, 0) + 1
        return frequency
    
    async def _generate_exercise_recommendations(
        self,
        user_profile: UserProfile,
        weekly_stats: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """운동 추천 생성"""
        recommendations = []
        
        # 선호 운동 기반 추천
        for exercise_type in user_profile.preferred_exercises[:3]:  # 상위 3개
            if user_profile.health_goal.value == "weight_loss":
                duration = 45
                intensity = "moderate"
                calories_burn = 300
            elif user_profile.health_goal.value == "muscle_gain":
                duration = 60
                intensity = "high"
                calories_burn = 250
            else:
                duration = 30
                intensity = "low"
                calories_burn = 200
            
            recommendations.append({
                "exercise_type": exercise_type.value,
                "duration": duration,
                "intensity": intensity,
                "calories_burn": calories_burn,
                "description": f"{exercise_type.value} {duration}분, {intensity} 강도"
            })
        
        return recommendations
    
    async def _generate_diet_improvements(
        self,
        user_profile: UserProfile,
        weekly_stats: Dict[str, Any]
    ) -> List[str]:
        """식단 개선 제안 생성"""
        improvements = []
        
        calorie_rate = weekly_stats.get("calorie_achievement_rate", 100)
        
        if calorie_rate > 120:
            improvements.append("칼로리 섭취량이 목표보다 높습니다. 간식을 줄이고 식사량을 조절해보세요.")
        elif calorie_rate < 80:
            improvements.append("칼로리 섭취량이 부족합니다. 영양가 있는 간식을 추가해보세요.")
        
        meal_frequency = weekly_stats.get("meal_frequency_by_type", {})
        if meal_frequency.get("아침", 0) < 5:
            improvements.append("아침 식사를 더 규칙적으로 드시는 것을 권장합니다.")
        
        if not improvements:
            improvements.append("현재 식습관을 잘 유지하고 계십니다!")
        
        return improvements
    
    def _generate_overall_assessment(self, weekly_stats: Dict[str, Any]) -> str:
        """전체적인 평가 생성"""
        calorie_rate = weekly_stats.get("calorie_achievement_rate", 100)
        meal_count = weekly_stats.get("total_meals", 0)
        
        if calorie_rate >= 90 and calorie_rate <= 110 and meal_count >= 14:
            return "훌륭합니다! 목표에 맞는 균형잡힌 식습관을 유지하고 계십니다."
        elif calorie_rate >= 80 and calorie_rate <= 120:
            return "좋은 진전을 보이고 있습니다. 조금만 더 신경쓰시면 완벽해질 것 같아요."
        else:
            return "식습관 개선이 필요합니다. 목표에 맞는 식단 계획을 세워보세요."
    
    async def _handle_user_intent(
        self,
        user_id: str,
        intent: str,
        entities: Dict[str, Any],
        user_profile: UserProfile
    ) -> Dict[str, Any]:
        """사용자 의도에 따른 추가 처리"""
        additional_data = {}
        
        if intent == "progress_check":
            # 진행상황 조회
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            daily_summary = await self.dynamodb_service.get_daily_nutrition_summary(
                user_id=user_id,
                date=today
            )
            additional_data["daily_summary"] = daily_summary
            
        elif intent == "food_inquiry":
            # 음식 관련 질문
            food_items = entities.get("food_items", [])
            if food_items:
                additional_data["mentioned_foods"] = food_items
                # 여기에 음식별 영양 정보 조회 로직 추가 가능
        
        elif intent == "exercise_advice":
            # 운동 조언
            exercise_types = entities.get("exercise_types", [])
            if exercise_types:
                additional_data["mentioned_exercises"] = exercise_types
        
        return additional_data


# 전역 인스턴스
coaching_pipeline = CoachingPipeline()