"""
Schedule Management Tools
스케줄 관리 및 알림 관련 도구들
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

from src.services.dynamodb_service import dynamodb_service
from src.utils.helpers import generate_unique_id


async def check_upcoming_events(
    user_id: str,
    days_ahead: int = 7
) -> Dict[str, Any]:
    """
    예정된 이벤트 확인 도구
    
    Args:
        user_id: 사용자 ID
        days_ahead: 확인할 일수
    
    Returns:
        예정된 이벤트 목록
    """
    try:
        events = await dynamodb_service.get_upcoming_events(
            user_id=user_id,
            days_ahead=days_ahead
        )
        
        if not events:
            return {"message": f"향후 {days_ahead}일간 예정된 이벤트가 없습니다"}
        
        # 이벤트 분류
        meal_events = []
        other_events = []
        
        for event in events:
            event_data = {
                "title": event.title,
                "date": event.start_time.strftime("%Y-%m-%d"),
                "time": event.start_time.strftime("%H:%M"),
                "type": event.event_type,
                "location": event.location,
                "participants": event.participants
            }
            
            if "회식" in event.event_type or "식사" in event.event_type:
                meal_events.append(event_data)
            else:
                other_events.append(event_data)
        
        return {
            "total_events": len(events),
            "meal_events": meal_events,
            "other_events": other_events,
            "period": f"향후 {days_ahead}일간",
            "advice": _generate_schedule_advice(meal_events)
        }
        
    except Exception as e:
        return {"error": f"일정 확인 중 오류 발생: {str(e)}"}


async def set_meal_reminder(
    user_id: str,
    meal_type: str,
    time: str
) -> Dict[str, Any]:
    """
    식사 알림 설정 도구
    
    Args:
        user_id: 사용자 ID
        meal_type: 식사 종류
        time: 알림 시간 (HH:MM)
    
    Returns:
        알림 설정 결과
    """
    try:
        from src.models.data_models import ScheduleEvent
        
        # 알림 이벤트 생성
        reminder_time = datetime.strptime(time, "%H:%M").time()
        tomorrow = datetime.now().date() + timedelta(days=1)
        reminder_datetime = datetime.combine(tomorrow, reminder_time)
        
        reminder_event = ScheduleEvent(
            event_id=generate_unique_id("reminder"),
            user_id=user_id,
            title=f"{meal_type} 시간 알림",
            event_type="meal_reminder",
            start_time=reminder_datetime,
            notes=f"{meal_type} 시간입니다!"
        )
        
        # DynamoDB에 저장
        success = await dynamodb_service.save_schedule_event(reminder_event)
        
        if success:
            return {
                "reminder_id": reminder_event.event_id,
                "meal_type": meal_type,
                "reminder_time": time,
                "date": tomorrow.strftime("%Y-%m-%d"),
                "message": f"{meal_type} 알림이 {time}에 설정되었습니다"
            }
        else:
            return {"error": "알림 설정에 실패했습니다"}
            
    except Exception as e:
        return {"error": f"알림 설정 중 오류 발생: {str(e)}"}


async def analyze_schedule_impact(
    user_id: str,
    event_type: str,
    date: str
) -> Dict[str, Any]:
    """
    일정이 식단에 미치는 영향 분석 도구
    
    Args:
        user_id: 사용자 ID
        event_type: 이벤트 종류
        date: 날짜 (YYYY-MM-DD)
    
    Returns:
        영향 분석 결과
    """
    try:
        # 해당 날짜의 식사 기록 조회
        target_date = datetime.strptime(date, "%Y-%m-%d")
        daily_summary = await dynamodb_service.get_daily_nutrition_summary(
            user_id=user_id,
            date=target_date
        )
        
        # 사용자 프로필 조회
        user_profile = await dynamodb_service.get_user_profile(user_id)
        if not user_profile:
            return {"error": "사용자 프로필을 찾을 수 없습니다"}
        
        # 목표 칼로리 계산
        from src.utils.helpers import calculate_bmr, calculate_tdee
        bmr = calculate_bmr(
            user_profile.weight,
            user_profile.height,
            user_profile.age,
            user_profile.gender
        )
        target_calories = calculate_tdee(bmr, user_profile.activity_level)
        
        current_calories = daily_summary.get('total_nutrition', {}).get('calories', 0)
        
        # 이벤트 타입별 분석
        impact_analysis = {}
        
        if "회식" in event_type:
            expected_calories = 800  # 회식 예상 칼로리
            total_expected = current_calories + expected_calories
            
            impact_analysis = {
                "event_impact": "회식으로 인한 고칼로리 섭취 예상",
                "expected_additional_calories": expected_calories,
                "total_expected_calories": total_expected,
                "target_calories": target_calories,
                "excess_calories": max(0, total_expected - target_calories),
                "recommendations": _generate_event_recommendations("회식", total_expected, target_calories)
            }
        
        elif "운동" in event_type:
            calories_burned = 300  # 운동 예상 소모 칼로리
            net_calories = current_calories - calories_burned
            
            impact_analysis = {
                "event_impact": "운동으로 인한 칼로리 소모 예상",
                "expected_calories_burned": calories_burned,
                "net_calories": net_calories,
                "target_calories": target_calories,
                "calorie_deficit": max(0, target_calories - net_calories),
                "recommendations": _generate_event_recommendations("운동", net_calories, target_calories)
            }
        
        else:
            impact_analysis = {
                "event_impact": "일반적인 일정으로 식단에 큰 영향 없음",
                "recommendations": ["평소와 같은 식단 패턴을 유지하세요"]
            }
        
        return {
            "date": date,
            "event_type": event_type,
            "current_calories": current_calories,
            "analysis": impact_analysis,
            "health_goal": user_profile.health_goal.value
        }
        
    except Exception as e:
        return {"error": f"일정 영향 분석 중 오류 발생: {str(e)}"}


def _generate_schedule_advice(meal_events: List[Dict[str, Any]]) -> List[str]:
    """스케줄 기반 조언 생성"""
    advice = []
    
    if not meal_events:
        advice.append("예정된 식사 일정이 없습니다. 규칙적인 식사를 계획해보세요.")
        return advice
    
    for event in meal_events:
        if "회식" in event["type"]:
            advice.append(f"{event['date']} 회식 예정입니다. 당일 점심은 가볍게 드세요.")
        elif "식사" in event["type"]:
            advice.append(f"{event['date']} 식사 약속이 있습니다. 다른 끼니를 조절해보세요.")
    
    return advice


def _generate_event_recommendations(event_type: str, calories: float, target: float) -> List[str]:
    """이벤트별 추천사항 생성"""
    recommendations = []
    
    if event_type == "회식":
        if calories > target * 1.2:
            recommendations.extend([
                "회식 전 가벼운 샐러드로 배를 채우세요",
                "알코올 섭취를 줄이고 물을 많이 드세요",
                "다음날 아침은 가볍게 드세요",
                "내일 추가 운동을 계획해보세요"
            ])
        else:
            recommendations.extend([
                "적당한 양으로 즐기세요",
                "야채 위주로 선택하세요"
            ])
    
    elif event_type == "운동":
        if calories < target * 0.8:
            recommendations.extend([
                "운동 후 단백질 보충을 하세요",
                "충분한 수분 섭취를 하세요",
                "운동 전후 간식을 추가하세요"
            ])
        else:
            recommendations.extend([
                "운동 후 가벼운 식사를 하세요",
                "근육 회복을 위해 단백질을 섭취하세요"
            ])
    
    return recommendations