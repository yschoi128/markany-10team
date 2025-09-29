"""
User Management Tools
사용자 프로필 관리 관련 도구들
"""

from typing import Dict, Any, List
from datetime import datetime

from src.services.dynamodb_service import dynamodb_service
from src.models.data_models import UserProfile, HealthGoal, ExerciseType


async def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    사용자 프로필 조회 도구
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        사용자 프로필 정보
    """
    try:
        user_profile = await dynamodb_service.get_user_profile(user_id)
        
        if not user_profile:
            return {"error": "사용자 프로필을 찾을 수 없습니다"}
        
        # BMI 계산
        from src.utils.helpers import calculate_bmi, get_bmi_category, calculate_bmr, calculate_tdee
        
        bmi = calculate_bmi(user_profile.weight, user_profile.height)
        bmi_category = get_bmi_category(bmi)
        
        bmr = calculate_bmr(
            user_profile.weight,
            user_profile.height,
            user_profile.age,
            user_profile.gender
        )
        
        tdee = calculate_tdee(bmr, user_profile.activity_level)
        
        return {
            "user_id": user_profile.user_id,
            "name": user_profile.name,
            "basic_info": {
                "age": user_profile.age,
                "gender": user_profile.gender,
                "height": user_profile.height,
                "weight": user_profile.weight,
                "bmi": bmi,
                "bmi_category": bmi_category
            },
            "health_metrics": {
                "bmr": round(bmr, 0),
                "tdee": round(tdee, 0),
                "target_calories": user_profile.target_calories
            },
            "goals_and_preferences": {
                "health_goal": user_profile.health_goal.value,
                "activity_level": user_profile.activity_level,
                "preferred_exercises": [ex.value for ex in user_profile.preferred_exercises],
                "disliked_exercises": [ex.value for ex in user_profile.disliked_exercises],
                "dietary_restrictions": user_profile.dietary_restrictions
            },
            "account_info": {
                "created_at": user_profile.created_at.strftime("%Y-%m-%d"),
                "updated_at": user_profile.updated_at.strftime("%Y-%m-%d")
            }
        }
        
    except Exception as e:
        return {"error": f"사용자 프로필 조회 중 오류 발생: {str(e)}"}


async def update_user_goals(
    user_id: str,
    new_goals: Dict[str, Any]
) -> Dict[str, Any]:
    """
    사용자 목표 업데이트 도구
    
    Args:
        user_id: 사용자 ID
        new_goals: 새로운 목표 정보
    
    Returns:
        업데이트 결과
    """
    try:
        # 기존 프로필 조회
        user_profile = await dynamodb_service.get_user_profile(user_id)
        if not user_profile:
            return {"error": "사용자 프로필을 찾을 수 없습니다"}
        
        # 업데이트할 필드들
        updated_fields = []
        
        if "health_goal" in new_goals:
            try:
                user_profile.health_goal = HealthGoal(new_goals["health_goal"])
                updated_fields.append("건강 목표")
            except ValueError:
                return {"error": f"유효하지 않은 건강 목표: {new_goals['health_goal']}"}
        
        if "weight" in new_goals:
            user_profile.weight = float(new_goals["weight"])
            updated_fields.append("체중")
        
        if "activity_level" in new_goals:
            user_profile.activity_level = new_goals["activity_level"]
            updated_fields.append("활동량")
        
        if "preferred_exercises" in new_goals:
            try:
                user_profile.preferred_exercises = [
                    ExerciseType(ex) for ex in new_goals["preferred_exercises"]
                ]
                updated_fields.append("선호 운동")
            except ValueError as e:
                return {"error": f"유효하지 않은 운동 종류: {str(e)}"}
        
        if "dietary_restrictions" in new_goals:
            user_profile.dietary_restrictions = new_goals["dietary_restrictions"]
            updated_fields.append("식이 제한사항")
        
        # 목표 칼로리 재계산
        if any(field in new_goals for field in ["health_goal", "weight", "activity_level"]):
            from src.utils.helpers import calculate_bmr, calculate_tdee
            
            bmr = calculate_bmr(
                user_profile.weight,
                user_profile.height,
                user_profile.age,
                user_profile.gender
            )
            tdee = calculate_tdee(bmr, user_profile.activity_level)
            
            # 건강 목표에 따른 칼로리 조정
            if user_profile.health_goal == HealthGoal.WEIGHT_LOSS:
                user_profile.target_calories = tdee * 0.8
            elif user_profile.health_goal == HealthGoal.MUSCLE_GAIN:
                user_profile.target_calories = tdee * 1.1
            else:
                user_profile.target_calories = tdee
            
            updated_fields.append("목표 칼로리")
        
        # 업데이트 시간 설정
        user_profile.updated_at = datetime.now()
        
        # DynamoDB에 저장
        success = await dynamodb_service.save_user_profile(user_profile)
        
        if success:
            return {
                "message": "사용자 목표가 성공적으로 업데이트되었습니다",
                "updated_fields": updated_fields,
                "new_target_calories": round(user_profile.target_calories, 0) if user_profile.target_calories else None,
                "updated_at": user_profile.updated_at.isoformat()
            }
        else:
            return {"error": "목표 업데이트에 실패했습니다"}
            
    except Exception as e:
        return {"error": f"목표 업데이트 중 오류 발생: {str(e)}"}


async def get_user_preferences(user_id: str) -> Dict[str, Any]:
    """
    사용자 선호도 조회 도구
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        사용자 선호도 정보
    """
    try:
        user_profile = await dynamodb_service.get_user_profile(user_id)
        if not user_profile:
            return {"error": "사용자 프로필을 찾을 수 없습니다"}
        
        # 최근 식사 패턴 분석
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        recent_meals = await dynamodb_service.get_user_meals(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=50
        )
        
        # 자주 먹는 음식 분석
        food_frequency = {}
        meal_time_patterns = {"아침": 0, "점심": 0, "저녁": 0, "간식": 0}
        
        for meal in recent_meals:
            # 음식 빈도
            for food in meal.foods:
                food_name = food.name
                food_frequency[food_name] = food_frequency.get(food_name, 0) + 1
            
            # 식사 시간 패턴
            meal_type = meal.meal_type
            meal_time_patterns[meal_type] = meal_time_patterns.get(meal_type, 0) + 1
        
        # 상위 5개 자주 먹는 음식
        top_foods = sorted(food_frequency.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "user_id": user_id,
            "exercise_preferences": {
                "preferred": [ex.value for ex in user_profile.preferred_exercises],
                "disliked": [ex.value for ex in user_profile.disliked_exercises]
            },
            "dietary_info": {
                "restrictions": user_profile.dietary_restrictions,
                "frequently_eaten_foods": [{"food": food, "count": count} for food, count in top_foods],
                "meal_patterns": meal_time_patterns
            },
            "health_profile": {
                "goal": user_profile.health_goal.value,
                "activity_level": user_profile.activity_level,
                "target_calories": user_profile.target_calories
            },
            "analysis_period": "최근 30일간",
            "total_meals_analyzed": len(recent_meals)
        }
        
    except Exception as e:
        return {"error": f"사용자 선호도 조회 중 오류 발생: {str(e)}"}


def create_user_profile(
    user_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    새 사용자 프로필 생성 도구
    
    Args:
        user_data: 사용자 데이터
    
    Returns:
        생성 결과
    """
    try:
        # 필수 필드 검증
        required_fields = ["user_id", "name", "age", "gender", "height", "weight", "health_goal"]
        missing_fields = [field for field in required_fields if field not in user_data]
        
        if missing_fields:
            return {"error": f"필수 필드가 누락되었습니다: {', '.join(missing_fields)}"}
        
        # 목표 칼로리 계산
        from src.utils.helpers import calculate_bmr, calculate_tdee
        
        bmr = calculate_bmr(
            user_data["weight"],
            user_data["height"],
            user_data["age"],
            user_data["gender"]
        )
        
        activity_level = user_data.get("activity_level", "moderate")
        tdee = calculate_tdee(bmr, activity_level)
        
        # 건강 목표에 따른 칼로리 조정
        health_goal = user_data["health_goal"]
        if health_goal == "weight_loss":
            target_calories = tdee * 0.8
        elif health_goal == "muscle_gain":
            target_calories = tdee * 1.1
        else:
            target_calories = tdee
        
        # UserProfile 객체 생성
        user_profile = UserProfile(
            user_id=user_data["user_id"],
            name=user_data["name"],
            age=user_data["age"],
            gender=user_data["gender"],
            height=user_data["height"],
            weight=user_data["weight"],
            health_goal=HealthGoal(health_goal),
            preferred_exercises=[
                ExerciseType(ex) for ex in user_data.get("preferred_exercises", ["gym"])
            ],
            disliked_exercises=[
                ExerciseType(ex) for ex in user_data.get("disliked_exercises", [])
            ],
            activity_level=activity_level,
            dietary_restrictions=user_data.get("dietary_restrictions", []),
            target_calories=target_calories
        )
        
        return {
            "user_profile": user_profile,
            "calculated_metrics": {
                "bmr": round(bmr, 0),
                "tdee": round(tdee, 0),
                "target_calories": round(target_calories, 0)
            },
            "message": "사용자 프로필이 생성되었습니다"
        }
        
    except Exception as e:
        return {"error": f"사용자 프로필 생성 중 오류 발생: {str(e)}"}