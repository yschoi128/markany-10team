"""
AI 식단 코치 메인 애플리케이션
FastAPI 기반 웹 서비스
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional
import uvicorn
from datetime import datetime
import os

from .models.data_models import (
    UserProfile, MealRecord, APIResponse, 
    HealthGoal, ExerciseType
)
from .pipelines.food_analysis_pipeline import food_analysis_pipeline
from .pipelines.coaching_pipeline import coaching_pipeline
from .services.dynamodb_service import dynamodb_service
from .utils.logger import setup_logger
from .utils.helpers import generate_unique_id

# 로거 설정
logger = setup_logger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="AI 식단 코치",
    description="AWS 기반의 개인 맞춤형 식단 관리 AI 솔루션",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """서비스 상태 확인"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# 사용자 관리 엔드포인트
@app.post("/users", response_model=APIResponse)
async def create_user_profile(user_profile: UserProfile):
    """
    사용자 프로필 생성
    
    Args:
        user_profile: 사용자 프로필 정보
    
    Returns:
        생성 결과
    """
    try:
        logger.info(f"Creating user profile: {user_profile.user_id}")
        
        # 사용자 ID가 없으면 생성
        if not user_profile.user_id:
            user_profile.user_id = generate_unique_id("user")
        
        # 목표 칼로리 자동 계산 (설정되지 않은 경우)
        if not user_profile.target_calories:
            from .utils.helpers import calculate_bmr, calculate_tdee
            bmr = calculate_bmr(
                user_profile.weight, 
                user_profile.height, 
                user_profile.age, 
                user_profile.gender
            )
            tdee = calculate_tdee(bmr, user_profile.activity_level)
            
            # 목표에 따른 칼로리 조정
            if user_profile.health_goal == HealthGoal.WEIGHT_LOSS:
                user_profile.target_calories = tdee * 0.8
            elif user_profile.health_goal == HealthGoal.MUSCLE_GAIN:
                user_profile.target_calories = tdee * 1.1
            else:
                user_profile.target_calories = tdee
        
        # DynamoDB에 저장
        success = await dynamodb_service.save_user_profile(user_profile)
        
        if success:
            return APIResponse(
                success=True,
                message="사용자 프로필이 성공적으로 생성되었습니다.",
                data={"user_id": user_profile.user_id}
            )
        else:
            raise HTTPException(status_code=500, detail="사용자 프로필 저장에 실패했습니다.")
            
    except Exception as e:
        logger.error(f"Error creating user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/users/{user_id}", response_model=APIResponse)
async def get_user_profile(user_id: str):
    """
    사용자 프로필 조회
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        사용자 프로필 정보
    """
    try:
        logger.info(f"Getting user profile: {user_id}")
        
        user_profile = await dynamodb_service.get_user_profile(user_id)
        
        if user_profile:
            return APIResponse(
                success=True,
                message="사용자 프로필을 성공적으로 조회했습니다.",
                data=user_profile.dict()
            )
        else:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 식사 분석 엔드포인트
@app.post("/meals/analyze", response_model=APIResponse)
async def analyze_meal_image(
    user_id: str = Form(...),
    meal_type: str = Form(...),
    people_count: int = Form(1),
    notes: Optional[str] = Form(None),
    image: UploadFile = File(...)
):
    """
    식사 이미지 분석
    
    Args:
        user_id: 사용자 ID
        meal_type: 식사 종류 (아침/점심/저녁/간식)
        people_count: 함께 식사한 인원 수
        notes: 추가 메모
        image: 업로드된 이미지 파일
    
    Returns:
        분석된 식사 기록
    """
    try:
        logger.info(f"Analyzing meal image for user: {user_id}")
        
        # 이미지 파일 검증
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
        
        # 이미지 데이터 읽기
        image_data = await image.read()
        
        # 파이프라인으로 처리
        meal_record = await food_analysis_pipeline.process_meal_image(
            user_id=user_id,
            image_data=image_data,
            filename=image.filename,
            meal_type=meal_type,
            people_count=people_count,
            notes=notes
        )
        
        if meal_record:
            # 즉시 피드백 생성
            feedback = await coaching_pipeline.generate_meal_feedback(
                user_id=user_id,
                meal_record=meal_record
            )
            
            response_data = {
                "meal_record": meal_record.dict(),
                "feedback": feedback.dict() if feedback else None
            }
            
            return APIResponse(
                success=True,
                message="식사 이미지 분석이 완료되었습니다.",
                data=response_data
            )
        else:
            raise HTTPException(status_code=500, detail="식사 이미지 분석에 실패했습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing meal image: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/meals/{user_id}", response_model=APIResponse)
async def get_user_meals(
    user_id: str,
    days: int = 7,
    limit: int = 50
):
    """
    사용자 식사 기록 조회
    
    Args:
        user_id: 사용자 ID
        days: 조회할 일수
        limit: 최대 조회 개수
    
    Returns:
        식사 기록 리스트
    """
    try:
        logger.info(f"Getting meals for user: {user_id}")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        meals = await dynamodb_service.get_user_meals(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        meals_data = [meal.dict() for meal in meals]
        
        return APIResponse(
            success=True,
            message=f"{len(meals)}개의 식사 기록을 조회했습니다.",
            data={"meals": meals_data}
        )
        
    except Exception as e:
        logger.error(f"Error getting user meals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 코칭 엔드포인트
@app.post("/coaching/daily/{user_id}", response_model=APIResponse)
async def generate_daily_coaching(user_id: str, context: Optional[str] = None):
    """
    일일 코칭 메시지 생성
    
    Args:
        user_id: 사용자 ID
        context: 추가 컨텍스트
    
    Returns:
        생성된 코칭 메시지
    """
    try:
        logger.info(f"Generating daily coaching for user: {user_id}")
        
        coaching_message = await coaching_pipeline.generate_daily_coaching(
            user_id=user_id,
            context=context
        )
        
        if coaching_message:
            return APIResponse(
                success=True,
                message="일일 코칭 메시지가 생성되었습니다.",
                data=coaching_message.dict()
            )
        else:
            raise HTTPException(status_code=500, detail="코칭 메시지 생성에 실패했습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating daily coaching: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/coaching/chat/{user_id}", response_model=APIResponse)
async def chat_with_coach(
    user_id: str,
    message: str = Form(...),
    conversation_history: Optional[List[dict]] = None
):
    """
    AI 코치와 대화
    
    Args:
        user_id: 사용자 ID
        message: 사용자 메시지
        conversation_history: 대화 기록
    
    Returns:
        AI 코치 응답
    """
    try:
        logger.info(f"Processing chat for user: {user_id}")
        
        result = await coaching_pipeline.process_user_conversation(
            user_id=user_id,
            user_input=message,
            conversation_history=conversation_history or []
        )
        
        return APIResponse(
            success=True,
            message="대화가 처리되었습니다.",
            data=result
        )
        
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/weekly/{user_id}", response_model=APIResponse)
async def get_weekly_report(user_id: str):
    """
    주간 리포트 조회
    
    Args:
        user_id: 사용자 ID
    
    Returns:
        주간 리포트 데이터
    """
    try:
        logger.info(f"Generating weekly report for user: {user_id}")
        
        report = await coaching_pipeline.generate_weekly_report(user_id)
        
        if report:
            return APIResponse(
                success=True,
                message="주간 리포트가 생성되었습니다.",
                data=report
            )
        else:
            raise HTTPException(status_code=500, detail="주간 리포트 생성에 실패했습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating weekly report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/nutrition/daily/{user_id}", response_model=APIResponse)
async def get_daily_nutrition(user_id: str, date: Optional[str] = None):
    """
    일일 영양소 섭취 현황 조회
    
    Args:
        user_id: 사용자 ID
        date: 조회할 날짜 (YYYY-MM-DD, 기본값: 오늘)
    
    Returns:
        일일 영양소 섭취 현황
    """
    try:
        logger.info(f"Getting daily nutrition for user: {user_id}")
        
        if date:
            target_date = datetime.strptime(date, "%Y-%m-%d")
        else:
            target_date = datetime.now()
        
        summary = await dynamodb_service.get_daily_nutrition_summary(
            user_id=user_id,
            date=target_date
        )
        
        return APIResponse(
            success=True,
            message="일일 영양소 현황을 조회했습니다.",
            data=summary
        )
        
    except Exception as e:
        logger.error(f"Error getting daily nutrition: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 에러 핸들러
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """HTTP 예외 처리"""
    return JSONResponse(
        status_code=exc.status_code,
        content=APIResponse(
            success=False,
            message=exc.detail,
            error_code=str(exc.status_code)
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """일반 예외 처리"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content=APIResponse(
            success=False,
            message="서버 내부 오류가 발생했습니다.",
            error_code="500"
        ).dict()
    )


# 애플리케이션 시작 이벤트
@app.on_event("startup")
async def startup_event():
    """애플리케이션 시작 시 실행"""
    logger.info("AI 식단 코치 애플리케이션이 시작되었습니다.")


@app.on_event("shutdown")
async def shutdown_event():
    """애플리케이션 종료 시 실행"""
    logger.info("AI 식단 코치 애플리케이션이 종료되었습니다.")


if __name__ == "__main__":
    # 개발 서버 실행
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )