"""
데이터 모델 정의 모듈
Pydantic을 사용한 타입 안전성과 데이터 검증
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class HealthGoal(str, Enum):
    """건강 목표 열거형"""
    WEIGHT_LOSS = "weight_loss"
    MUSCLE_GAIN = "muscle_gain"
    BODY_PROFILE = "body_profile"
    HEALTH_MAINTENANCE = "health_maintenance"


class ExerciseType(str, Enum):
    """운동 종류 열거형"""
    GYM = "gym"
    YOGA = "yoga"
    RUNNING = "running"
    SWIMMING = "swimming"
    CYCLING = "cycling"
    PILATES = "pilates"


class NutritionInfo(BaseModel):
    """영양소 정보 모델"""
    calories: float = Field(..., description="칼로리 (kcal)")
    carbohydrates: float = Field(..., description="탄수화물 (g)")
    protein: float = Field(..., description="단백질 (g)")
    fat: float = Field(..., description="지방 (g)")
    fiber: Optional[float] = Field(None, description="식이섬유 (g)")
    sodium: Optional[float] = Field(None, description="나트륨 (mg)")


class FoodItem(BaseModel):
    """음식 항목 모델"""
    name: str = Field(..., description="음식명")
    quantity: str = Field(..., description="섭취량 (예: 1인분, 200g)")
    nutrition: NutritionInfo = Field(..., description="영양소 정보")
    confidence: float = Field(..., ge=0, le=1, description="분석 신뢰도")


class MealRecord(BaseModel):
    """식사 기록 모델"""
    user_id: str = Field(..., description="사용자 ID")
    meal_id: str = Field(..., description="식사 ID")
    timestamp: datetime = Field(..., description="식사 시간")
    meal_type: str = Field(..., description="식사 종류 (아침/점심/저녁/간식)")
    image_url: Optional[str] = Field(None, description="식사 이미지 S3 URL")
    foods: List[FoodItem] = Field(..., description="음식 목록")
    total_nutrition: NutritionInfo = Field(..., description="총 영양소")
    people_count: int = Field(1, ge=1, description="함께 식사한 인원 수")
    notes: Optional[str] = Field(None, description="추가 메모")


class UserProfile(BaseModel):
    """사용자 프로필 모델"""
    user_id: str = Field(..., description="사용자 ID")
    name: str = Field(..., description="사용자 이름")
    age: int = Field(..., ge=1, le=120, description="나이")
    gender: str = Field(..., description="성별")
    height: float = Field(..., gt=0, description="신장 (cm)")
    weight: float = Field(..., gt=0, description="체중 (kg)")
    health_goal: HealthGoal = Field(..., description="건강 목표")
    preferred_exercises: List[ExerciseType] = Field(..., description="선호 운동")
    disliked_exercises: List[ExerciseType] = Field(default=[], description="비선호 운동")
    activity_level: str = Field(..., description="활동량 (low/moderate/high)")
    dietary_restrictions: List[str] = Field(default=[], description="식이 제한사항")
    target_calories: Optional[float] = Field(None, description="목표 칼로리")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ScheduleEvent(BaseModel):
    """스케줄 이벤트 모델"""
    event_id: str = Field(..., description="이벤트 ID")
    user_id: str = Field(..., description="사용자 ID")
    title: str = Field(..., description="이벤트 제목")
    event_type: str = Field(..., description="이벤트 종류 (회식/약속 등)")
    start_time: datetime = Field(..., description="시작 시간")
    end_time: Optional[datetime] = Field(None, description="종료 시간")
    location: Optional[str] = Field(None, description="장소")
    participants: Optional[int] = Field(None, description="참석 인원")
    notes: Optional[str] = Field(None, description="메모")
    is_processed: bool = Field(False, description="처리 완료 여부")


class CoachingMessage(BaseModel):
    """코칭 메시지 모델"""
    message_id: str = Field(..., description="메시지 ID")
    user_id: str = Field(..., description="사용자 ID")
    message_type: str = Field(..., description="메시지 종류 (advice/encouragement/warning)")
    content: str = Field(..., description="메시지 내용")
    timestamp: datetime = Field(default_factory=datetime.now)
    is_voice: bool = Field(False, description="음성 메시지 여부")
    priority: str = Field("normal", description="우선순위 (low/normal/high)")


class ExerciseRecommendation(BaseModel):
    """운동 추천 모델"""
    exercise_type: ExerciseType = Field(..., description="운동 종류")
    duration: int = Field(..., gt=0, description="운동 시간 (분)")
    intensity: str = Field(..., description="강도 (low/moderate/high)")
    calories_burn: float = Field(..., description="예상 소모 칼로리")
    description: str = Field(..., description="운동 설명")


class DietRecommendation(BaseModel):
    """식단 추천 모델"""
    meal_type: str = Field(..., description="식사 종류")
    recommended_foods: List[str] = Field(..., description="추천 음식 목록")
    target_nutrition: NutritionInfo = Field(..., description="목표 영양소")
    preparation_time: Optional[int] = Field(None, description="조리 시간 (분)")
    difficulty: Optional[str] = Field(None, description="조리 난이도")


class DailyReport(BaseModel):
    """일일 리포트 모델"""
    user_id: str = Field(..., description="사용자 ID")
    date: str = Field(..., description="날짜 (YYYY-MM-DD)")
    total_nutrition: NutritionInfo = Field(..., description="총 섭취 영양소")
    target_nutrition: NutritionInfo = Field(..., description="목표 영양소")
    achievement_rate: float = Field(..., ge=0, le=1, description="목표 달성률")
    meal_count: int = Field(..., description="식사 횟수")
    exercise_recommendations: List[ExerciseRecommendation] = Field(..., description="운동 추천")
    diet_recommendations: List[DietRecommendation] = Field(..., description="식단 추천")
    coaching_messages: List[str] = Field(..., description="코칭 메시지")


class ConversationContext(BaseModel):
    """대화 컨텍스트 모델"""
    user_id: str = Field(..., description="사용자 ID")
    session_id: str = Field(..., description="세션 ID")
    messages: List[Dict[str, Any]] = Field(..., description="대화 기록")
    context_data: Dict[str, Any] = Field(default={}, description="컨텍스트 데이터")
    last_updated: datetime = Field(default_factory=datetime.now)


class APIResponse(BaseModel):
    """API 응답 모델"""
    success: bool = Field(..., description="성공 여부")
    message: str = Field(..., description="응답 메시지")
    data: Optional[Any] = Field(None, description="응답 데이터")
    error_code: Optional[str] = Field(None, description="에러 코드")
    timestamp: datetime = Field(default_factory=datetime.now)