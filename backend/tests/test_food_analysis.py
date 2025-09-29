"""
음식 분석 파이프라인 테스트
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from src.pipelines.food_analysis_pipeline import FoodAnalysisPipeline
from src.models.data_models import FoodItem, NutritionInfo, MealRecord


class TestFoodAnalysisPipeline:
    """음식 분석 파이프라인 테스트 클래스"""
    
    @pytest.fixture
    def pipeline(self):
        """테스트용 파이프라인 인스턴스"""
        return FoodAnalysisPipeline()
    
    @pytest.fixture
    def sample_food_item(self):
        """샘플 음식 항목"""
        return FoodItem(
            name="김치찌개",
            quantity="1인분",
            nutrition=NutritionInfo(
                calories=250.0,
                carbohydrates=15.0,
                protein=20.0,
                fat=10.0
            ),
            confidence=0.9
        )
    
    def test_calculate_total_nutrition(self, pipeline, sample_food_item):
        """총 영양소 계산 테스트"""
        food_items = [sample_food_item, sample_food_item]  # 2개 항목
        
        total_nutrition = pipeline._calculate_total_nutrition(food_items)
        
        assert total_nutrition.calories == 500.0
        assert total_nutrition.carbohydrates == 30.0
        assert total_nutrition.protein == 40.0
        assert total_nutrition.fat == 20.0
    
    def test_create_default_food_item(self, pipeline):
        """기본 음식 항목 생성 테스트"""
        default_item = pipeline._create_default_food_item()
        
        assert default_item.name == "분석되지 않은 음식"
        assert default_item.confidence == 0.1
        assert default_item.nutrition.calories > 0
    
    @pytest.mark.asyncio
    async def test_process_meal_image_success(self, pipeline):
        """식사 이미지 처리 성공 테스트"""
        # Mock 설정
        pipeline.s3_service.upload_image = AsyncMock(return_value="https://s3.amazonaws.com/test.jpg")
        pipeline.bedrock_service.analyze_food_image = AsyncMock(return_value=[sample_food_item])
        pipeline.dynamodb_service.save_meal_record = AsyncMock(return_value=True)
        
        # 테스트 실행
        result = await pipeline.process_meal_image(
            user_id="test_user",
            image_data=b"fake_image_data",
            filename="test.jpg",
            meal_type="점심"
        )
        
        # 검증
        assert result is not None
        assert isinstance(result, MealRecord)
        assert result.user_id == "test_user"
        assert result.meal_type == "점심"
    
    @pytest.mark.asyncio
    async def test_process_meal_image_s3_failure(self, pipeline):
        """S3 업로드 실패 테스트"""
        # Mock 설정
        pipeline.s3_service.upload_image = AsyncMock(return_value=None)
        
        # 테스트 실행
        result = await pipeline.process_meal_image(
            user_id="test_user",
            image_data=b"fake_image_data",
            filename="test.jpg",
            meal_type="점심"
        )
        
        # 검증
        assert result is None