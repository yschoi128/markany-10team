"""
Agentic AI Diet Coach API
단일 엔드포인트로 모든 기능을 처리하는 Agentic API
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
from datetime import datetime

from agents.core.bedrock_agent import bedrock_agent_coach
from src.models.data_models import APIResponse
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

app = FastAPI(
    title="Agentic AI Diet Coach",
    description="LLM이 자율적으로 판단하여 모든 기능을 처리하는 AI 식단 코치",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    """서비스의 상태를 확인하는 헬스체크 엔드포인트.
    
    서비스가 정상적으로 동작하고 있는지 확인하기 위한 간단한 엔드포인트입니다.
    로드밸런서나 모니터링 시스템에서 사용할 수 있습니다.
    
    Returns:
        Dict[str, str]: 서비스 상태와 현재 시간
    """
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@app.post("/chat", response_model=APIResponse)
async def chat_with_agent(
    user_id: str = Form(...),
    message: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    """사용자와 Agentic AI 간의 대화를 처리하는 메인 엔드포인트.
    
    이 단일 엔드포인트로 모든 기능을 처리할 수 있습니다. LLM이 사용자 입력을
    분석하여 적절한 도구들을 자율적으로 선택하고 실행합니다.
    
    Args:
        user_id (str): 사용자 고유 식별자
        message (str): 사용자의 텍스트 메시지
        image (Optional[UploadFile]): 업로드된 이미지 파일 (선택사항)
    
    Returns:
        APIResponse: 처리 결과를 포함한 응답
    
    Raises:
        HTTPException: 이미지 파일 형식 오류 또는 처리 실패 시
    """
    try:
        print(f"Chat endpoint called with user_id: {user_id}, message: {message}")
        context = {}
        
        if image and image.filename:
            print(f"Image received: {image.filename}, content_type: {image.content_type}")
            # 파일 확장자로 이미지 파일 검증
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
            file_ext = image.filename.lower().split('.')[-1] if '.' in image.filename else ''
            if not any(image.filename.lower().endswith(ext) for ext in allowed_extensions):
                raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
            
            image_data = await image.read()
            print(f"Image data read: {len(image_data)} bytes")
            context["image_data"] = image_data
            context["image_filename"] = image.filename
        elif image:
            print("Image received but no filename")
        else:
            print("No image received")
        
        result = await bedrock_agent_coach.process_input(
            user_input=message,
            user_id=user_id,
            context=context
        )
        
        return APIResponse(
            success=result["success"],
            message="요청이 처리되었습니다.",
            data=result
        )
            
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return APIResponse(
            success=False,
            message="오류가 발생했습니다.",
            data={"error": str(e)}
        )


@app.post("/demo", response_model=APIResponse)
async def demo_scenarios(scenario: str = Form(...), user_id: str = Form("demo_user")):
    """미리 정의된 데모 시나리오를 실행하여 Agentic AI의 기능을 시연합니다.
    
    다양한 상황에서의 AI 동작을 테스트하고 시연할 수 있는 데모 시나리오들을
    제공합니다. 각 시나리오는 다른 유형의 사용자 요청을 시뮤레이션합니다.
    
    Args:
        scenario (str): 실행할 데모 시나리오 이름
        user_id (str): 데모용 사용자 ID. Defaults to "demo_user".
    
    Returns:
        APIResponse: 데모 시나리오 실행 결과
    
    Raises:
        HTTPException: 유효하지 않은 시나리오 이름일 경우
    """
    scenarios = {
        "morning": "안녕하세요! 오늘 아침 식사 추천해주세요.",
        "food_question": "치킨 먹어도 될까요?",
        "exercise": "어제 회식에서 많이 먹었는데 운동 추천해주세요.",
        "progress": "이번 주 식단 관리 확인해주세요."
    }
    
    if scenario not in scenarios:
        raise HTTPException(status_code=400, detail=f"사용 가능한 시나리오: {list(scenarios.keys())}")
    
    result = await bedrock_agent_coach.process_input(
        user_input=scenarios[scenario],
        user_id=user_id,
        context={"demo_mode": True}
    )
    
    return APIResponse(
        success=True,
        message=f"데모 시나리오 '{scenario}' 실행 완료",
        data=result
    )


if __name__ == "__main__":
    uvicorn.run(
        "agents.api.agent_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )