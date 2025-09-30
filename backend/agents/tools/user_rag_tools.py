"""
개인화된 유저 정보 RAG 도구들
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from src.services.dynamodb_service import dynamodb_service
from src.models.data_models import UserProfile, HealthGoal, ExerciseType
from src.utils.helpers import generate_unique_id

async def create_user_profile(
    user_id: str,
    name: str,
    age: int,
    gender: str,
    height: float,
    weight: float,
    health_goal: str = "health_maintenance",
    activity_level: str = "MODERATE"
) -> Dict[str, Any]:
    """유저 프로필 생성 및 BMI 계산"""
    try:
        # BMI 계산
        height_m = height / 100  # cm to m
        bmi = weight / (height_m ** 2)
        
        # BMI 분류
        if bmi < 18.5:
            bmi_category = "저체중"
        elif bmi < 25:
            bmi_category = "정상"
        elif bmi < 30:
            bmi_category = "과체중"
        else:
            bmi_category = "비만"
        
        # 목표 칼로리 계산 (Harris-Benedict 공식)
        if gender.lower() == "male":
            bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
        else:
            bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
        
        # 활동 수준에 따른 TDEE 계산
        activity_multipliers = {
            "SEDENTARY": 1.2,
            "LIGHT": 1.375,
            "MODERATE": 1.55,
            "ACTIVE": 1.725,
            "VERY_ACTIVE": 1.9
        }
        
        tdee = bmr * activity_multipliers.get(activity_level, 1.55)
        
        # 목표에 따른 칼로리 조정
        if health_goal == "weight_loss":
            target_calories = tdee * 0.8
        elif health_goal == "muscle_gain":
            target_calories = tdee * 1.1
        else:
            target_calories = tdee
        
        # UserProfile 객체 생성
        user_profile = UserProfile(
            user_id=user_id,
            name=name,
            age=age,
            gender=gender,
            height=height,
            weight=weight,
            health_goal=HealthGoal(health_goal),
            preferred_exercises=[],
            disliked_exercises=[],
            activity_level=activity_level,
            dietary_restrictions=[],
            target_calories=target_calories,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # DynamoDB에 저장
        success = await dynamodb_service.save_user_profile(user_profile)
        
        if success:
            return {
                "success": True,
                "user_id": user_id,
                "bmi": round(bmi, 1),
                "bmi_category": bmi_category,
                "bmr": round(bmr, 0),
                "target_calories": round(target_calories, 0),
                "message": f"{name}님의 프로필이 생성되었습니다."
            }
        else:
            return {"error": "프로필 저장에 실패했습니다."}
            
    except Exception as e:
        return {"error": f"프로필 생성 중 오류: {str(e)}"}

async def get_personalized_user_context(user_id: str) -> Dict[str, Any]:
    """개인화된 유저 컨텍스트 조회 (RAG용)"""
    try:
        # 유저 프로필 조회
        user_profile = await dynamodb_service.get_user_profile(user_id)
        if not user_profile:
            return {"error": "사용자 프로필을 찾을 수 없습니다."}
        
        # BMI 계산
        height_m = user_profile.height / 100
        bmi = user_profile.weight / (height_m ** 2)
        
        # 최근 7일 식사 기록
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        recent_meals = await dynamodb_service.get_user_meals(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=20
        )
        
        # 평균 일일 칼로리 계산
        if recent_meals:
            total_calories = sum(meal.total_nutrition.calories for meal in recent_meals)
            avg_daily_calories = total_calories / 7
        else:
            avg_daily_calories = 0
        
        # 개인화된 컨텍스트 구성
        context = {
            "user_info": {
                "name": user_profile.name,
                "age": user_profile.age,
                "gender": user_profile.gender,
                "height": user_profile.height,
                "weight": user_profile.weight,
                "bmi": round(bmi, 1),
                "health_goal": user_profile.health_goal.value,
                "activity_level": user_profile.activity_level,
                "target_calories": user_profile.target_calories,
                "dietary_restrictions": user_profile.dietary_restrictions
            },
            "recent_activity": {
                "meals_last_7_days": len(recent_meals),
                "avg_daily_calories": round(avg_daily_calories, 0),
                "calorie_goal_achievement": round((avg_daily_calories / user_profile.target_calories) * 100, 1) if user_profile.target_calories else 0
            },
            "personalized_insights": _generate_insights(user_profile, bmi, avg_daily_calories, recent_meals)
        }
        
        return context
        
    except Exception as e:
        return {"error": f"컨텍스트 조회 중 오류: {str(e)}"}

async def update_user_weight(user_id: str, new_weight: float) -> Dict[str, Any]:
    """체중 업데이트 및 BMI 재계산"""
    try:
        user_profile = await dynamodb_service.get_user_profile(user_id)
        if not user_profile:
            return {"error": "사용자를 찾을 수 없습니다."}
        
        old_weight = user_profile.weight
        old_bmi = old_weight / ((user_profile.height / 100) ** 2)
        
        # 체중 업데이트
        user_profile.weight = new_weight
        user_profile.updated_at = datetime.now()
        
        # 새 BMI 계산
        new_bmi = new_weight / ((user_profile.height / 100) ** 2)
        weight_change = new_weight - old_weight
        
        # 저장
        success = await dynamodb_service.save_user_profile(user_profile)
        
        if success:
            return {
                "success": True,
                "old_weight": old_weight,
                "new_weight": new_weight,
                "weight_change": round(weight_change, 1),
                "old_bmi": round(old_bmi, 1),
                "new_bmi": round(new_bmi, 1),
                "message": f"체중이 {weight_change:+.1f}kg 변경되었습니다."
            }
        else:
            return {"error": "체중 업데이트에 실패했습니다."}
            
    except Exception as e:
        return {"error": f"체중 업데이트 중 오류: {str(e)}"}

def _generate_insights(user_profile: UserProfile, bmi: float, avg_calories: float, recent_meals) -> Dict[str, str]:
    """개인화된 인사이트 생성"""
    insights = {}
    
    # BMI 기반 인사이트
    if bmi < 18.5:
        insights["bmi_advice"] = "저체중입니다. 건강한 체중 증가를 위해 영양가 높은 음식 섭취를 권장합니다."
    elif bmi >= 25:
        insights["bmi_advice"] = "과체중입니다. 균형 잡힌 식단과 규칙적인 운동을 권장합니다."
    else:
        insights["bmi_advice"] = "정상 체중을 유지하고 계십니다. 현재 생활 패턴을 유지하세요."
    
    # 칼로리 섭취 패턴 분석
    if user_profile.target_calories:
        calorie_ratio = avg_calories / user_profile.target_calories
        if calorie_ratio < 0.8:
            insights["calorie_advice"] = "목표 칼로리보다 적게 섭취하고 있습니다. 충분한 영양 섭취를 권장합니다."
        elif calorie_ratio > 1.2:
            insights["calorie_advice"] = "목표 칼로리를 초과하고 있습니다. 식단 조절을 고려해보세요."
        else:
            insights["calorie_advice"] = "목표 칼로리에 맞게 잘 섭취하고 계십니다."
    
    # 식사 빈도 분석
    if len(recent_meals) < 14:  # 7일간 14끼 미만
        insights["meal_frequency"] = "식사 빈도가 낮습니다. 규칙적인 식사를 권장합니다."
    
    return insights