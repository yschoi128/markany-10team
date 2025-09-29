"""
음식 분석 파이프라인
이미지 업로드부터 영양소 분석까지의 전체 프로세스
"""

from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.data_models import MealRecord, FoodItem, NutritionInfo
from ..services.s3_service import s3_service
from ..services.bedrock_service import bedrock_service
from ..services.dynamodb_service import dynamodb_service
from ..utils.logger import setup_logger
from ..utils.helpers import generate_unique_id

logger = setup_logger(__name__)


class FoodAnalysisPipeline:
    """음식 분석 파이프라인 클래스"""
    
    def __init__(self):
        """파이프라인 초기화"""
        self.s3_service = s3_service
        self.bedrock_service = bedrock_service
        self.dynamodb_service = dynamodb_service
    
    async def process_meal_image(
        self,
        user_id: str,
        image_data: bytes,
        filename: str,
        meal_type: str,
        people_count: int = 1,
        notes: Optional[str] = None
    ) -> Optional[MealRecord]:
        """
        식사 이미지 전체 처리 파이프라인
        
        Args:
            user_id: 사용자 ID
            image_data: 이미지 바이트 데이터
            filename: 원본 파일명
            meal_type: 식사 종류 (아침/점심/저녁/간식)
            people_count: 함께 식사한 인원 수
            notes: 추가 메모
        
        Returns:
            처리된 식사 기록 또는 None
        """
        try:
            logger.info(f"Starting meal image processing for user: {user_id}")
            
            # 1. 고유 식사 ID 생성
            meal_id = generate_unique_id("meal")
            
            # 2. S3에 이미지 업로드
            logger.info("Uploading image to S3...")
            image_url = await self.s3_service.upload_image(
                image_data=image_data,
                user_id=user_id,
                filename=filename,
                meal_id=meal_id
            )
            
            if not image_url:
                logger.error("Failed to upload image to S3")
                return None
            
            # 3. Bedrock으로 음식 분석
            logger.info("Analyzing food image with Bedrock...")
            food_items = await self.bedrock_service.analyze_food_image(
                image_data=image_data,
                people_count=people_count
            )
            
            if not food_items:
                logger.warning("No food items detected in image")
                # 기본 음식 항목 생성
                food_items = [self._create_default_food_item()]
            
            # 4. 총 영양소 계산
            total_nutrition = self._calculate_total_nutrition(food_items)
            
            # 5. 식사 기록 객체 생성
            meal_record = MealRecord(
                user_id=user_id,
                meal_id=meal_id,
                timestamp=datetime.now(),
                meal_type=meal_type,
                image_url=image_url,
                foods=food_items,
                total_nutrition=total_nutrition,
                people_count=people_count,
                notes=notes
            )
            
            # 6. DynamoDB에 저장
            logger.info("Saving meal record to DynamoDB...")
            success = await self.dynamodb_service.save_meal_record(meal_record)
            
            if not success:
                logger.error("Failed to save meal record to DynamoDB")
                # S3에서 이미지 삭제 (롤백)
                await self.s3_service.delete_image(image_url)
                return None
            
            logger.info(f"Successfully processed meal image: {meal_id}")
            return meal_record
            
        except Exception as e:
            logger.error(f"Error in meal image processing pipeline: {e}")
            return None
    
    async def reanalyze_meal(
        self,
        meal_id: str,
        user_id: str,
        people_count: Optional[int] = None
    ) -> Optional[MealRecord]:
        """
        기존 식사 기록 재분석
        
        Args:
            meal_id: 식사 ID
            user_id: 사용자 ID
            people_count: 새로운 인원 수 (선택사항)
        
        Returns:
            재분석된 식사 기록 또는 None
        """
        try:
            logger.info(f"Starting meal reanalysis: {meal_id}")
            
            # 1. 기존 식사 기록 조회
            meals = await self.dynamodb_service.get_user_meals(user_id, limit=100)
            existing_meal = next((meal for meal in meals if meal.meal_id == meal_id), None)
            
            if not existing_meal:
                logger.error(f"Meal record not found: {meal_id}")
                return None
            
            if not existing_meal.image_url:
                logger.error(f"No image URL found for meal: {meal_id}")
                return None
            
            # 2. S3에서 이미지 다운로드
            logger.info("Downloading image from S3...")
            image_data = await self.s3_service.download_image(existing_meal.image_url)
            
            if not image_data:
                logger.error("Failed to download image from S3")
                return None
            
            # 3. 새로운 인원 수 적용
            new_people_count = people_count or existing_meal.people_count
            
            # 4. Bedrock으로 재분석
            logger.info("Reanalyzing food image with Bedrock...")
            food_items = await self.bedrock_service.analyze_food_image(
                image_data=image_data,
                people_count=new_people_count
            )
            
            if not food_items:
                logger.warning("No food items detected in reanalysis")
                return existing_meal
            
            # 5. 총 영양소 재계산
            total_nutrition = self._calculate_total_nutrition(food_items)
            
            # 6. 식사 기록 업데이트
            updated_meal = MealRecord(
                user_id=existing_meal.user_id,
                meal_id=existing_meal.meal_id,
                timestamp=existing_meal.timestamp,
                meal_type=existing_meal.meal_type,
                image_url=existing_meal.image_url,
                foods=food_items,
                total_nutrition=total_nutrition,
                people_count=new_people_count,
                notes=existing_meal.notes
            )
            
            # 7. DynamoDB에 업데이트 저장
            logger.info("Updating meal record in DynamoDB...")
            success = await self.dynamodb_service.save_meal_record(updated_meal)
            
            if not success:
                logger.error("Failed to update meal record in DynamoDB")
                return None
            
            logger.info(f"Successfully reanalyzed meal: {meal_id}")
            return updated_meal
            
        except Exception as e:
            logger.error(f"Error in meal reanalysis pipeline: {e}")
            return None
    
    async def batch_process_images(
        self,
        user_id: str,
        image_batch: List[Dict[str, Any]]
    ) -> List[Optional[MealRecord]]:
        """
        여러 이미지 일괄 처리
        
        Args:
            user_id: 사용자 ID
            image_batch: 이미지 배치 정보 리스트
                [{"image_data": bytes, "filename": str, "meal_type": str, ...}, ...]
        
        Returns:
            처리된 식사 기록 리스트
        """
        try:
            logger.info(f"Starting batch processing of {len(image_batch)} images")
            
            results = []
            
            for i, image_info in enumerate(image_batch):
                logger.info(f"Processing image {i+1}/{len(image_batch)}")
                
                meal_record = await self.process_meal_image(
                    user_id=user_id,
                    image_data=image_info["image_data"],
                    filename=image_info["filename"],
                    meal_type=image_info["meal_type"],
                    people_count=image_info.get("people_count", 1),
                    notes=image_info.get("notes")
                )
                
                results.append(meal_record)
            
            successful_count = sum(1 for result in results if result is not None)
            logger.info(f"Batch processing completed: {successful_count}/{len(image_batch)} successful")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in batch image processing: {e}")
            return []
    
    def _calculate_total_nutrition(self, food_items: List[FoodItem]) -> NutritionInfo:
        """
        음식 항목들의 총 영양소 계산
        
        Args:
            food_items: 음식 항목 리스트
        
        Returns:
            총 영양소 정보
        """
        total_calories = sum(food.nutrition.calories for food in food_items)
        total_carbs = sum(food.nutrition.carbohydrates for food in food_items)
        total_protein = sum(food.nutrition.protein for food in food_items)
        total_fat = sum(food.nutrition.fat for food in food_items)
        total_fiber = sum(food.nutrition.fiber or 0 for food in food_items)
        total_sodium = sum(food.nutrition.sodium or 0 for food in food_items)
        
        return NutritionInfo(
            calories=round(total_calories, 2),
            carbohydrates=round(total_carbs, 2),
            protein=round(total_protein, 2),
            fat=round(total_fat, 2),
            fiber=round(total_fiber, 2) if total_fiber > 0 else None,
            sodium=round(total_sodium, 2) if total_sodium > 0 else None
        )
    
    def _create_default_food_item(self) -> FoodItem:
        """
        기본 음식 항목 생성 (분석 실패 시 사용)
        
        Returns:
            기본 음식 항목
        """
        return FoodItem(
            name="분석되지 않은 음식",
            quantity="1인분",
            nutrition=NutritionInfo(
                calories=300.0,
                carbohydrates=30.0,
                protein=15.0,
                fat=10.0
            ),
            confidence=0.1
        )
    
    async def get_meal_analysis_summary(
        self,
        user_id: str,
        date_range_days: int = 7
    ) -> Dict[str, Any]:
        """
        식사 분석 요약 정보 조회
        
        Args:
            user_id: 사용자 ID
            date_range_days: 조회할 일수
        
        Returns:
            분석 요약 정보
        """
        try:
            # 지정된 기간의 식사 기록 조회
            end_date = datetime.now()
            start_date = end_date - timedelta(days=date_range_days)
            
            meals = await self.dynamodb_service.get_user_meals(
                user_id=user_id,
                start_date=start_date,
                end_date=end_date
            )
            
            if not meals:
                return {"message": "분석할 식사 기록이 없습니다."}
            
            # 통계 계산
            total_meals = len(meals)
            avg_calories = sum(meal.total_nutrition.calories for meal in meals) / total_meals
            avg_protein = sum(meal.total_nutrition.protein for meal in meals) / total_meals
            
            # 식사 종류별 분석
            meal_types = {}
            for meal in meals:
                meal_type = meal.meal_type
                if meal_type not in meal_types:
                    meal_types[meal_type] = {"count": 0, "total_calories": 0}
                meal_types[meal_type]["count"] += 1
                meal_types[meal_type]["total_calories"] += meal.total_nutrition.calories
            
            # 가장 자주 먹은 음식
            food_frequency = {}
            for meal in meals:
                for food in meal.foods:
                    food_name = food.name
                    food_frequency[food_name] = food_frequency.get(food_name, 0) + 1
            
            most_frequent_foods = sorted(
                food_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            summary = {
                "period": f"{date_range_days}일간",
                "total_meals": total_meals,
                "average_calories_per_meal": round(avg_calories, 2),
                "average_protein_per_meal": round(avg_protein, 2),
                "meal_types_distribution": meal_types,
                "most_frequent_foods": most_frequent_foods,
                "analysis_date": datetime.now().isoformat()
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating meal analysis summary: {e}")
            return {"error": "분석 요약 생성 중 오류가 발생했습니다."}


# 전역 인스턴스
food_analysis_pipeline = FoodAnalysisPipeline()