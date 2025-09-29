"""
Coaching Tools for Agentic AI
개인 맞춤형 코칭, 운동 추천 등 코칭 관련 도구들
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.services.bedrock_service import bedrock_service
from src.services.dynamodb_service import dynamodb_service
from src.utils.helpers import calculate_bmr, calculate_tdee


async def generate_personalized_advice(
    user_id: str,
    context: str = ""
) -> Dict[str, Any]:
    """
    개인 맞춤형 조언 생성 도구 (간단한 폴백 버전)
    """
    try:
        # 간단한 조언 생성
        advice_templates = [
            "건강한 식습관을 유지하세요! 규칙적인 식사가 중요합니다.",
            "오늘도 좋은 하루 보내세요! 충분한 수분 섭취를 잊지 마세요.",
            "균형 잡힌 식단으로 건강을 챙기세요. 야채와 단백질을 충분히 드세요.",
            "적당한 운동과 함께 건강한 식단을 유지하시길 바랍니다."
        ]
        
        import random
        advice = random.choice(advice_templates)
        
        return {
            "advice": advice,
            "message_type": "general",
            "priority": "normal",
            "generated_at": datetime.now().isoformat(),
            "context_considered": f"사용자 {user_id}에 대한 일반 조언"
        }
        
    except Exception as e:
        return {"error": f"조언 생성 중 오류 발생: {str(e)}"}


async def recommend_exercise(
    user_id: str,
    current_activity: str = ""
) -> Dict[str, Any]:
    """
    운동 추천 도구 (간단한 폴백 버전)
    """
    try:
        # 간단한 운동 추천
        exercise_recommendations = [
            {"exercise": "산책", "duration": 30, "calories_burn": 150, "reason": "가벼운 유산소 운동"},
            {"exercise": "스트레칭", "duration": 15, "calories_burn": 50, "reason": "근육 이완"},
            {"exercise": "계단 오르기", "duration": 10, "calories_burn": 80, "reason": "일상 속 운동"}
        ]
        
        return {
            "recommendations": exercise_recommendations,
            "current_status": {
                "calories_today": 0,
                "target_calories": 2000,
                "calorie_balance": -2000
            },
            "health_goal": "건강 유지",
            "preferred_exercises": ["걷기", "요가"],
            "advice": "규칙적인 운동으로 건강을 유지하세요!"
        }
        
    except Exception as e:
        return {"error": f"운동 추천 생성 중 오류 발생: {str(e)}"}


async def check_health_progress(
    user_id: str,
    period: str = "week"
) -> Dict[str, Any]:
    """
    건강 진행상황 확인 도구
    
    Args:
        user_id: 사용자 ID
        period: 확인 기간 (week/month)
    
    Returns:
        건강 진행상황
    """
    try:
        # 기간 설정
        if period == "month":
            days = 30
        else:
            days = 7
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 사용자 프로필 조회
        user_profile = await dynamodb_service.get_user_profile(user_id)
        if not user_profile:
            return {"error": "사용자 프로필을 찾을 수 없습니다"}
        
        # 기간 내 식사 기록 조회
        meals = await dynamodb_service.get_user_meals(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not meals:
            return {"message": f"최근 {period} 식사 기록이 없습니다"}
        
        # 목표 칼로리 계산
        bmr = calculate_bmr(
            user_profile.weight,
            user_profile.height,
            user_profile.age,
            user_profile.gender
        )
        daily_target = calculate_tdee(bmr, user_profile.activity_level)
        
        # 건강 목표에 따른 조정
        if user_profile.health_goal.value == "weight_loss":
            daily_target *= 0.8
        elif user_profile.health_goal.value == "muscle_gain":
            daily_target *= 1.1
        
        # 통계 계산
        total_calories = sum(meal.total_nutrition.calories for meal in meals)
        avg_daily_calories = total_calories / days
        target_total = daily_target * days
        
        achievement_rate = (total_calories / target_total) * 100
        
        # 진행상황 평가
        if 90 <= achievement_rate <= 110:
            status = "목표 달성 중"
            feedback = "훌륭합니다! 목표에 맞게 잘 관리하고 계십니다."
        elif achievement_rate < 90:
            status = "목표 미달"
            feedback = "칼로리 섭취가 부족합니다. 영양가 있는 식사를 늘려보세요."
        else:
            status = "목표 초과"
            feedback = "칼로리 섭취가 많습니다. 식사량을 조절해보세요."
        
        return {
            "period": f"{period} ({days}일간)",
            "total_meals": len(meals),
            "calories": {
                "total_consumed": round(total_calories, 0),
                "daily_average": round(avg_daily_calories, 0),
                "daily_target": round(daily_target, 0),
                "achievement_rate": round(achievement_rate, 1)
            },
            "status": status,
            "feedback": feedback,
            "health_goal": user_profile.health_goal.value,
            "recommendations": _generate_progress_recommendations(achievement_rate, user_profile.health_goal.value)
        }
        
    except Exception as e:
        return {"error": f"건강 진행상황 확인 중 오류 발생: {str(e)}"}


async def create_meal_plan(
    user_id: str,
    duration: str = "day",
    preferences: List[str] = None
) -> Dict[str, Any]:
    """
    식단 계획 생성 도구
    
    Args:
        user_id: 사용자 ID
        duration: 계획 기간 (day/week)
        preferences: 음식 선호도
    
    Returns:
        식단 계획
    """
    try:
        # 사용자 프로필 조회
        user_profile = await dynamodb_service.get_user_profile(user_id)
        if not user_profile:
            return {"error": "사용자 프로필을 찾을 수 없습니다"}
        
        # 목표 칼로리 계산
        bmr = calculate_bmr(
            user_profile.weight,
            user_profile.height,
            user_profile.age,
            user_profile.gender
        )
        daily_calories = calculate_tdee(bmr, user_profile.activity_level)
        
        # 건강 목표에 따른 조정
        if user_profile.health_goal.value == "weight_loss":
            daily_calories *= 0.8
        elif user_profile.health_goal.value == "muscle_gain":
            daily_calories *= 1.1
        
        # 식단 계획 생성
        if duration == "week":
            days = 7
        else:
            days = 1
        
        meal_plan = {}
        
        for day in range(days):
            date_key = (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d")
            
            # 하루 식단 구성 (아침 30%, 점심 40%, 저녁 30%)
            breakfast_calories = daily_calories * 0.3
            lunch_calories = daily_calories * 0.4
            dinner_calories = daily_calories * 0.3
            
            meal_plan[date_key] = {
                "아침": await _generate_meal_suggestion("아침", breakfast_calories, user_profile, preferences),
                "점심": await _generate_meal_suggestion("점심", lunch_calories, user_profile, preferences),
                "저녁": await _generate_meal_suggestion("저녁", dinner_calories, user_profile, preferences),
                "daily_total": daily_calories
            }
        
        return {
            "duration": f"{duration} ({days}일간)",
            "daily_target_calories": round(daily_calories, 0),
            "health_goal": user_profile.health_goal.value,
            "meal_plan": meal_plan,
            "dietary_restrictions": user_profile.dietary_restrictions,
            "notes": f"{user_profile.health_goal.value} 목표에 맞춘 식단 계획입니다."
        }
        
    except Exception as e:
        return {"error": f"식단 계획 생성 중 오류 발생: {str(e)}"}


async def _generate_dynamic_exercise_recommendations(
    user_profile,
    current_calories: float,
    target_calories: float,
    current_activity: str
) -> List[Dict[str, Any]]:
    """
    AI 기반 동적 운동 추천 생성
    
    NOTE: AI 추천 실패 시 하드코딩된 폴백 사용
    """
    try:
        from ...src.services.bedrock_service import bedrock_service
        
        calorie_diff = current_calories - target_calories
        
        recommendation_prompt = f"""
다음 조건에 맞는 운동을 추천해주세요:

- 건강 목표: {user_profile.health_goal.value}
- 선호 운동: {', '.join([ex.value for ex in user_profile.preferred_exercises])}
- 오늘 칼로리: {current_calories:.0f}kcal (목표: {target_calories:.0f}kcal, 차이: {calorie_diff:+.0f}kcal)
- 현재 활동: {current_activity}
- 활동 수준: {user_profile.activity_level}

2-3개의 운동을 추천하고 다음 형식으로 응답해주세요:
[
  {{
    "exercise": "운동명",
    "duration": 시간(분),
    "calories_burn": 예상소모칼로리,
    "reason": "추천이유"
  }}
]
"""
        
        response = await bedrock_service.process_natural_language(
            user_input=recommendation_prompt,
            user_profile=user_profile,
            conversation_history=[]
        )
        
        # JSON 파싱 시도
        import re
        import json
        
        response_text = response.get("response", "") if isinstance(response, dict) else str(response)
        
        array_match = re.search(r'\[.*\]', response_text, re.DOTALL)
        if array_match:
            try:
                recommendations = json.loads(array_match.group())
                if isinstance(recommendations, list) and recommendations:
                    return recommendations
            except:
                pass
        
        # AI 추천 실패 시 폴백
        return _generate_exercise_recommendations_fallback(
            user_profile, current_calories, target_calories
        )
        
    except Exception:
        # 모든 오류 시 폴백
        return _generate_exercise_recommendations_fallback(
            user_profile, current_calories, target_calories
        )

def _generate_exercise_recommendations_fallback(
    user_profile,
    current_calories: float,
    target_calories: float
) -> List[Dict[str, Any]]:
    """
    폴백: 하드코딩된 운동 추천
    
    NOTE: AI 추천 실패 시 사용되는 하드코딩된 폴백입니다.
    한국인 운동 패턴과 선호도를 고려하여 구성되었으며, 필요시 운동을 추가/수정할 수 있습니다.
    
    TODO: 피트니스 전문가 감수 운동 데이터베이스나 실시간 운동 API로 대체 가능
    """
    recommendations = []
    
    # HARDCODED: 건강 목표별 운동 추천 (정확성을 위한 의도적 하드코딩)
    if user_profile.health_goal.value == "weight_loss":
        if current_calories > target_calories:
            recommendations.extend([
                {"exercise": "빠른 걷기", "duration": 40, "calories_burn": 180, "reason": "과다 칼로리 소모 필요"},
                {"exercise": "자전거 타기", "duration": 30, "calories_burn": 220, "reason": "효과적인 유산소 운동"},
                {"exercise": "계단 오르기", "duration": 15, "calories_burn": 120, "reason": "일상 속 고강도 운동"}
            ])
        else:
            recommendations.extend([
                {"exercise": "가벼운 요가", "duration": 25, "calories_burn": 90, "reason": "적정 칼로리 유지"},
                {"exercise": "스트레칭", "duration": 20, "calories_burn": 60, "reason": "근육 이완 및 유연성"}
            ])
    
    elif user_profile.health_goal.value == "muscle_gain":
        recommendations.extend([
            {"exercise": "웨이트 트레이닝", "duration": 50, "calories_burn": 280, "reason": "근육량 증가"},
            {"exercise": "푸시업", "duration": 20, "calories_burn": 120, "reason": "상체 근력 강화"},
            {"exercise": "스쿼트", "duration": 15, "calories_burn": 100, "reason": "하체 근력 강화"}
        ])
    
    else:  # health_maintenance
        recommendations.extend([
            {"exercise": "산책", "duration": 35, "calories_burn": 140, "reason": "건강 유지"},
            {"exercise": "라디오 체조", "duration": 15, "calories_burn": 70, "reason": "전신 운동"},
            {"exercise": "가벼운 조깅", "duration": 20, "calories_burn": 160, "reason": "심폐 기능 향상"}
        ])
    
    return recommendations

def _generate_progress_recommendations(achievement_rate: float, health_goal: str) -> List[str]:
    """진행상황 기반 추천 생성"""
    recommendations = []
    
    if achievement_rate < 90:
        if health_goal == "weight_loss":
            recommendations.append("목표보다 적게 드시고 계십니다. 건강한 간식을 추가해보세요.")
        else:
            recommendations.append("칼로리 섭취를 늘려 목표에 맞춰보세요.")
    elif achievement_rate > 110:
        recommendations.append("칼로리 섭취가 많습니다. 식사량을 조절해보세요.")
        recommendations.append("간식을 줄이고 물을 더 많이 드세요.")
    else:
        recommendations.append("목표에 맞게 잘 관리하고 계십니다!")
        recommendations.append("현재 패턴을 유지하세요.")
    
    return recommendations


async def _generate_meal_suggestion(meal_type: str, target_calories: float, user_profile, preferences: List[str]) -> Dict[str, Any]:
    """식사별 메뉴 제안 생성 (AI 기반 동적 추천)"""
    try:
        from ...src.services.bedrock_service import bedrock_service
        
        # AI를 통한 동적 메뉴 추천
        recommendation_prompt = f"""
다음 조건에 맞는 {meal_type} 메뉴를 추천해주세요:

- 목표 칼로리: {target_calories:.0f}kcal
- 건강 목표: {user_profile.health_goal.value if user_profile else '건강 유지'}
- 선호도: {', '.join(preferences) if preferences else '없음'}
- 식이 제한: {', '.join(user_profile.dietary_restrictions) if user_profile and user_profile.dietary_restrictions else '없음'}

응답 형식:
{{
  "menu": "메뉴명",
  "calories": 칼로리수치,
  "protein": 단백질수치,
  "carbohydrates": 탄수화물수치,
  "reason": "추천 이유"
}}
"""
        
        response = await bedrock_service.process_natural_language(
            user_input=recommendation_prompt,
            user_profile=user_profile,
            conversation_history=[]
        )
        
        # JSON 파싱 시도
        import re
        import json
        
        response_text = response.get("response", "") if isinstance(response, dict) else str(response)
        
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            try:
                suggestion = json.loads(json_match.group())
                return {
                    "menu": suggestion.get("menu", f"{meal_type} 메뉴"),
                    "calories": suggestion.get("calories", target_calories),
                    "protein": suggestion.get("protein", target_calories * 0.15 / 4),  # 15% 단백질
                    "carbohydrates": suggestion.get("carbohydrates", target_calories * 0.5 / 4),  # 50% 탄수화물
                    "notes": suggestion.get("reason", f"AI 추천 {meal_type} 메뉴")
                }
            except:
                pass
        
        # AI 추천 실패 시 폴백
        return _generate_meal_suggestion_fallback(meal_type, target_calories, user_profile, preferences)
        
    except Exception:
        # 모든 오류 시 폴백
        return _generate_meal_suggestion_fallback(meal_type, target_calories, user_profile, preferences)

def _generate_meal_suggestion_fallback(meal_type: str, target_calories: float, user_profile, preferences: List[str]) -> Dict[str, Any]:
    """
    폴백: 하드코딩된 메뉴 데이터베이스
    
    NOTE: AI 추천 실패 시 사용되는 하드코딩된 폴백입니다.
    한국인 식단 패턴을 고려하여 구성되었으며, 필요시 메뉴를 추가/수정할 수 있습니다.
    
    TODO: 영양사 감수 메뉴 데이터베이스나 실시간 음식 API로 대체 가능
    """
    
    # HARDCODED: 한국인 식단 패턴 기반 메뉴 데이터베이스
    meal_database = {
        "아침": [
            {"name": "오트밀 + 베리 + 아몬드", "calories": 280, "protein": 10, "carbs": 45},
            {"name": "계란 토스트 + 샐러드", "calories": 320, "protein": 18, "carbs": 30},
            {"name": "그릭요거트 + 견과류", "calories": 220, "protein": 15, "carbs": 20},
            {"name": "현미밥 + 김치 + 계란국", "calories": 350, "protein": 12, "carbs": 55}
        ],
        "점심": [
            {"name": "닭가슴살 샐러드 + 현미밥", "calories": 380, "protein": 35, "carbs": 40},
            {"name": "된장찌개 + 현미밥", "calories": 420, "protein": 22, "carbs": 60},
            {"name": "연어 덮밥 + 미소국", "calories": 480, "protein": 28, "carbs": 65},
            {"name": "비빔밥 + 나물반찬", "calories": 450, "protein": 15, "carbs": 75}
        ],
        "저녁": [
            {"name": "구이 생선 + 상추 샐러드", "calories": 320, "protein": 28, "carbs": 15},
            {"name": "두부 스테이크 + 브로콜리", "calories": 280, "protein": 25, "carbs": 12},
            {"name": "닭가슴살 + 고구마", "calories": 380, "protein": 32, "carbs": 35},
            {"name": "삼계탕 + 현미밥 소량", "calories": 350, "protein": 20, "carbs": 30}
        ]
    }
    
    # 목표 칼로리에 가장 가까운 메뉴 선택
    available_meals = meal_database.get(meal_type, meal_database["점심"])  # 기본값으로 점심 사용
    best_meal = min(available_meals, key=lambda x: abs(x["calories"] - target_calories))
    
    return {
        "menu": best_meal["name"],
        "calories": best_meal["calories"],
        "protein": best_meal["protein"],
        "carbohydrates": best_meal["carbs"],
        "notes": f"{meal_type} 추천 메뉴 (폴백)"
    }