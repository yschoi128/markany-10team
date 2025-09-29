"""
Diet-related Tools for Agentic AI
식단 분석, 영양소 계산 등 식단 관련 도구들
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import base64

from src.services.s3_service import s3_service
from src.services.bedrock_service import bedrock_service
from src.services.dynamodb_service import dynamodb_service
from src.models.data_models import MealRecord, FoodItem, NutritionInfo
from src.utils.helpers import generate_unique_id


async def analyze_food_image(
    user_id: str,
    image_data: bytes,
    meal_type: str = "식사",
    people_count: int = 1
) -> Dict[str, Any]:
    """
    음식 이미지 분석 도구
    
    Args:
        user_id: 사용자 ID
        image_data: 이미지 바이트 데이터
        meal_type: 식사 종류
        people_count: 함께 식사한 인원 수
    
    Returns:
        분석 결과
    """
    try:
        # 1. S3에 이미지 업로드
        meal_id = generate_unique_id("meal")
        image_url = await s3_service.upload_image(
            image_data=image_data,
            user_id=user_id,
            filename=f"meal_{meal_id}.jpg",
            meal_id=meal_id
        )
        
        if not image_url:
            return {"error": "이미지 업로드에 실패했습니다"}
        
        # 2. Bedrock으로 음식 분석
        food_items = await bedrock_service.analyze_food_image(
            image_data=image_data,
            people_count=people_count
        )
        
        if not food_items:
            return {"error": "음식을 인식할 수 없습니다"}
        
        # 3. 총 영양소 계산
        total_calories = sum(food.nutrition.calories for food in food_items)
        total_carbs = sum(food.nutrition.carbohydrates for food in food_items)
        total_protein = sum(food.nutrition.protein for food in food_items)
        total_fat = sum(food.nutrition.fat for food in food_items)
        
        # 4. 식사 기록 생성 및 저장
        meal_record = MealRecord(
            user_id=user_id,
            meal_id=meal_id,
            timestamp=datetime.now(),
            meal_type=meal_type,
            image_url=image_url,
            foods=food_items,
            total_nutrition=NutritionInfo(
                calories=total_calories,
                carbohydrates=total_carbs,
                protein=total_protein,
                fat=total_fat
            ),
            people_count=people_count
        )
        
        # 5. DynamoDB에 저장
        await dynamodb_service.save_meal_record(meal_record)
        
        return {
            "meal_id": meal_id,
            "foods": [
                {
                    "name": food.name,
                    "quantity": food.quantity,
                    "calories": food.nutrition.calories,
                    "confidence": food.confidence
                }
                for food in food_items
            ],
            "total_nutrition": {
                "calories": total_calories,
                "carbohydrates": total_carbs,
                "protein": total_protein,
                "fat": total_fat
            },
            "image_url": image_url,
            "analysis_time": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {"error": f"음식 분석 중 오류 발생: {str(e)}"}


async def get_nutrition_history(
    user_id: str,
    days: int = 7
) -> Dict[str, Any]:
    """
    영양 섭취 기록 조회 도구
    
    Args:
        user_id: 사용자 ID
        days: 조회할 일수
    
    Returns:
        영양 섭취 기록
    """
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        meals = await dynamodb_service.get_user_meals(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not meals:
            return {"message": f"최근 {days}일간 식사 기록이 없습니다"}
        
        # 일별 영양소 집계
        daily_nutrition = {}
        for meal in meals:
            date_key = meal.timestamp.strftime("%Y-%m-%d")
            
            if date_key not in daily_nutrition:
                daily_nutrition[date_key] = {
                    "calories": 0,
                    "carbohydrates": 0,
                    "protein": 0,
                    "fat": 0,
                    "meal_count": 0
                }
            
            daily_nutrition[date_key]["calories"] += meal.total_nutrition.calories
            daily_nutrition[date_key]["carbohydrates"] += meal.total_nutrition.carbohydrates
            daily_nutrition[date_key]["protein"] += meal.total_nutrition.protein
            daily_nutrition[date_key]["fat"] += meal.total_nutrition.fat
            daily_nutrition[date_key]["meal_count"] += 1
        
        # 평균 계산
        total_days = len(daily_nutrition)
        avg_calories = sum(day["calories"] for day in daily_nutrition.values()) / total_days
        avg_protein = sum(day["protein"] for day in daily_nutrition.values()) / total_days
        
        return {
            "period": f"{days}일간",
            "total_meals": len(meals),
            "daily_nutrition": daily_nutrition,
            "averages": {
                "calories_per_day": round(avg_calories, 1),
                "protein_per_day": round(avg_protein, 1),
                "meals_per_day": round(len(meals) / total_days, 1)
            },
            "summary": f"최근 {days}일간 총 {len(meals)}회 식사, 일평균 {round(avg_calories, 0)}kcal 섭취"
        }
        
    except Exception as e:
        return {"error": f"영양 기록 조회 중 오류 발생: {str(e)}"}


async def calculate_daily_nutrition(
    user_id: str,
    date: str = None
) -> Dict[str, Any]:
    """
    특정 날짜의 영양소 계산 도구
    
    Args:
        user_id: 사용자 ID
        date: 날짜 (YYYY-MM-DD, 기본값: 오늘)
    
    Returns:
        일일 영양소 정보
    """
    try:
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            target_date = datetime.now()
        
        summary = await dynamodb_service.get_daily_nutrition_summary(
            user_id=user_id,
            date=target_date
        )
        
        if not summary:
            return {"message": f"{target_date.strftime('%Y-%m-%d')} 식사 기록이 없습니다"}
        
        return {
            "date": target_date.strftime("%Y-%m-%d"),
            "nutrition": summary.get("total_nutrition", {}),
            "meal_count": summary.get("meal_count", 0),
            "meals_by_type": summary.get("meals_by_type", {}),
            "summary": f"{target_date.strftime('%m월 %d일')} 총 {summary.get('meal_count', 0)}회 식사, {summary.get('total_nutrition', {}).get('calories', 0):.0f}kcal 섭취"
        }
        
    except Exception as e:
        return {"error": f"일일 영양소 계산 중 오류 발생: {str(e)}"}


async def save_meal_record(
    user_id: str,
    meal_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    식사 기록 저장 도구
    
    Args:
        user_id: 사용자 ID
        meal_data: 식사 데이터
    
    Returns:
        저장 결과
    """
    try:
        # 식사 기록 객체 생성
        meal_record = MealRecord(
            user_id=user_id,
            meal_id=generate_unique_id("meal"),
            timestamp=datetime.now(),
            meal_type=meal_data.get("meal_type", "식사"),
            foods=[
                FoodItem(
                    name=food["name"],
                    quantity=food["quantity"],
                    nutrition=NutritionInfo(**food["nutrition"]),
                    confidence=food.get("confidence", 0.8)
                )
                for food in meal_data.get("foods", [])
            ],
            total_nutrition=NutritionInfo(**meal_data.get("total_nutrition", {})),
            people_count=meal_data.get("people_count", 1),
            notes=meal_data.get("notes")
        )
        
        # DynamoDB에 저장
        success = await dynamodb_service.save_meal_record(meal_record)
        
        if success:
            return {
                "meal_id": meal_record.meal_id,
                "message": "식사 기록이 저장되었습니다",
                "timestamp": meal_record.timestamp.isoformat()
            }
        else:
            return {"error": "식사 기록 저장에 실패했습니다"}
            
    except Exception as e:
        return {"error": f"식사 기록 저장 중 오류 발생: {str(e)}"}


def get_nutrition_recommendations(
    current_nutrition: Dict[str, float],
    target_nutrition: Dict[str, float]
) -> Dict[str, Any]:
    """
    영양소 기반 추천 도구
    
    Args:
        current_nutrition: 현재 섭취 영양소
        target_nutrition: 목표 영양소
    
    Returns:
        영양소 추천
    """
    try:
        recommendations = []
        
        # 칼로리 분석
        calorie_diff = target_nutrition.get("calories", 0) - current_nutrition.get("calories", 0)
        if calorie_diff > 100:
            recommendations.append(f"칼로리를 {calorie_diff:.0f}kcal 더 섭취하세요")
        elif calorie_diff < -100:
            recommendations.append(f"칼로리를 {abs(calorie_diff):.0f}kcal 줄이세요")
        
        # 단백질 분석
        protein_diff = target_nutrition.get("protein", 0) - current_nutrition.get("protein", 0)
        if protein_diff > 10:
            recommendations.append(f"단백질을 {protein_diff:.0f}g 더 섭취하세요 (닭가슴살, 계란, 두부 추천)")
        
        # 탄수화물 분석
        carb_diff = target_nutrition.get("carbohydrates", 0) - current_nutrition.get("carbohydrates", 0)
        if carb_diff > 20:
            recommendations.append(f"탄수화물을 {carb_diff:.0f}g 더 섭취하세요 (현미, 고구마 추천)")
        elif carb_diff < -20:
            recommendations.append(f"탄수화물을 {abs(carb_diff):.0f}g 줄이세요")
        
        if not recommendations:
            recommendations.append("현재 영양 섭취가 목표에 적합합니다!")
        
        return {
            "recommendations": recommendations,
            "calorie_status": "적정" if abs(calorie_diff) <= 100 else ("부족" if calorie_diff > 0 else "과다"),
            "protein_status": "적정" if abs(protein_diff) <= 10 else ("부족" if protein_diff > 0 else "과다")
        }
        
    except Exception as e:
        return {"error": f"영양소 추천 생성 중 오류 발생: {str(e)}"}