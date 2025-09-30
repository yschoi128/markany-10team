#!/usr/bin/env python3
"""
AI 다이어트 코치 FastAPI 서버
"""

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import os
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# Agent 임포트
from agents.core.bedrock_agent import bedrock_agent_coach
from agents.tools.user_rag_tools import create_user_profile

app = FastAPI(title="AI Diet Coach API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    user_id: str = "web_user"

class ChatResponse(BaseModel):
    response: str
    success: bool
    agent_used: bool = False

class ProfileRequest(BaseModel):
    name: str
    arguments: dict

class ToolResponse(BaseModel):
    content: list

@app.get("/")
async def root():
    return {"message": "AI Diet Coach API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AI Diet Coach"}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """채팅 엔드포인트"""
    try:
        print(f"Chat endpoint called with user_id: {request.user_id}, message: {request.message}")
        
        # Bedrock Agent 호출
        result = await bedrock_agent_coach.process_input(
            user_input=request.message,
            user_id=request.user_id
        )
        
        return ChatResponse(
            response=result["response"],
            success=result["success"],
            agent_used=result.get("agent_used", False)
        )
        
    except Exception as e:
        print(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/image")
async def chat_with_image(
    message: str = Form(...),
    user_id: str = Form("web_user"),
    image: UploadFile = File(...)
):
    """이미지와 함께 채팅"""
    try:
        print(f"Image chat endpoint called with user_id: {user_id}, message: {message}")
        print(f"Image file: {image.filename}, content_type: {image.content_type}")
        
        # 이미지 데이터 읽기
        image_data = await image.read()
        
        # 컨텍스트 생성
        context = {
            "image_data": image_data,
            "image_filename": image.filename
        }
        
        # Bedrock Agent 호출
        result = await bedrock_agent_coach.process_input(
            user_input=message,
            user_id=user_id,
            context=context
        )
        
        return ChatResponse(
            response=result["response"],
            success=result["success"],
            agent_used=result.get("agent_used", False)
        )
        
    except Exception as e:
        print(f"Image chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/tools/call", response_model=ToolResponse)
async def call_tool(request: ProfileRequest):
    """MCP 도구 호출 엔드포인트"""
    try:
        print(f"Tool call: {request.name} with args: {request.arguments}")
        
        if request.name == "create_user_profile":
            result = await create_user_profile(
                user_id=request.arguments["user_id"],
                name=request.arguments["name"],
                age=request.arguments["age"],
                gender=request.arguments["gender"],
                height=request.arguments["height"],
                weight=request.arguments["weight"],
                health_goal=request.arguments["health_goal"]
            )
            
            import json
            return ToolResponse(
                content=[{"text": json.dumps(result)}]
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {request.name}")
            
    except Exception as e:
        print(f"Tool call error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)