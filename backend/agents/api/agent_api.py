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
from pydantic import BaseModel

from agents.core.bedrock_agent import bedrock_agent_coach
from src.models.data_models import APIResponse
from src.utils.logger import setup_logger
from .mcp_integration import integrate_enhanced_mcp

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

# MCP 성능 개선 통합
app = integrate_enhanced_mcp(app)

class ChatRequest(BaseModel):
    user_id: str
    message: str

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/chat", response_model=APIResponse)
async def chat_with_agent(
    user_id: str = Form(...),
    message: str = Form(...),
    image: Optional[UploadFile] = File(None)
):
    return await _process_chat(user_id, message, image)

@app.post("/chat/json", response_model=APIResponse)
async def chat_with_agent_json(request: ChatRequest):
    return await _process_chat(request.user_id, request.message, None)

async def _process_chat(user_id: str, message: str, image: Optional[UploadFile]):
    try:
        print(f"Chat endpoint called with user_id: {user_id}, message: {message}")
        context = {}
        
        if image and image.filename:
            print(f"Image received: {image.filename}, content_type: {image.content_type}")
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp']
            if not any(image.filename.lower().endswith(ext) for ext in allowed_extensions):
                raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
            
            image_data = await image.read()
            print(f"Image data read: {len(image_data)} bytes")
            context["image_data"] = image_data
            context["image_filename"] = image.filename
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

if __name__ == "__main__":
    uvicorn.run(
        "agents.api.agent_api:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )