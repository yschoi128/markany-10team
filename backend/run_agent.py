"""
Agentic AI Diet Coach 실행 스크립트
"""

import uvicorn
import os
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("AGENT_PORT", 8001))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    
    print("🤖 Agentic AI Diet Coach 시작 중...")
    print(f"📡 서버 주소: http://{host}:{port}")
    print(f"📚 API 문서: http://{host}:{port}/docs")
    
    uvicorn.run(
        "agents.api.agent_api:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )