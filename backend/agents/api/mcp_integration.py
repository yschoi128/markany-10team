"""
성능 개선된 MCP 통합
"""

from fastapi import FastAPI
from typing import Dict, Any, Optional
import json
import time
import hashlib
import asyncio
from functools import wraps

class PerformanceCache:
    """성능 개선을 위한 캐시 시스템"""
    
    def __init__(self, ttl: int = 300):
        self.cache = {}
        self.ttl = ttl
    
    def _generate_key(self, *args, **kwargs) -> str:
        """캐시 키 생성"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """캐시에서 값 조회"""
        if key in self.cache:
            data, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return data
            else:
                del self.cache[key]
        return None
    
    def set(self, key: str, value: Any):
        """캐시에 값 저장"""
        self.cache[key] = (value, time.time())

class EnhancedMCPIntegration:
    """성능 개선된 MCP 통합"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.tools_cache = PerformanceCache(ttl=600)
        self.response_cache = PerformanceCache(ttl=180)
        self._add_enhanced_endpoints()
    
    def _add_enhanced_endpoints(self):
        """성능 개선된 엔드포인트 추가"""
        
        @self.app.post("/mcp/tools/list")
        async def list_tools():
            cache_key = "tools_list"
            cached = self.tools_cache.get(cache_key)
            if cached:
                return cached
            
            tools = {
                "tools": [
                    {
                        "name": "analyze_food_image",
                        "description": "음식 이미지를 분석하여 메뉴, 칼로리, 영양소를 계산하고 식단 조언 제공",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "user_id": {"type": "string"},
                                "image_data": {"type": "string"},
                                "meal_type": {"type": "string", "default": "저녁"}
                            },
                            "required": ["user_id", "image_data"]
                        }
                    },
                    {
                        "name": "get_nutrition_history",
                        "description": "사용자 영양 섭취 기록 조회",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "user_id": {"type": "string"},
                                "days": {"type": "integer", "default": 7}
                            },
                            "required": ["user_id"]
                        }
                    },
                    {
                        "name": "create_user_profile",
                        "description": "사용자 프로필 생성 및 BMI 계산",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "user_id": {"type": "string"},
                                "name": {"type": "string"},
                                "age": {"type": "integer"},
                                "gender": {"type": "string"},
                                "height": {"type": "number"},
                                "weight": {"type": "number"},
                                "health_goal": {"type": "string", "default": "WEIGHT_MAINTENANCE"},
                                "activity_level": {"type": "string", "default": "MODERATE"}
                            },
                            "required": ["user_id", "name", "age", "gender", "height", "weight"]
                        }
                    },
                    {
                        "name": "get_user_context",
                        "description": "개인화된 사용자 컨텍스트 조회 (RAG용)",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "user_id": {"type": "string"}
                            },
                            "required": ["user_id"]
                        }
                    },
                    {
                        "name": "update_user_weight",
                        "description": "체중 업데이트 및 BMI 재계산",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "user_id": {"type": "string"},
                                "new_weight": {"type": "number"}
                            },
                            "required": ["user_id", "new_weight"]
                        }
                    }
                ]
            }
            
            self.tools_cache.set(cache_key, tools)
            return tools
        
        @self.app.post("/mcp/tools/call")
        async def call_tool_enhanced(request: Dict[str, Any]):
            tool_name = request.get("name")
            args = request.get("arguments", {})
            
            # 응답 캐싱 확인
            cache_key = self.response_cache._generate_key(tool_name, args)
            cached_response = self.response_cache.get(cache_key)
            if cached_response:
                return cached_response
            
            try:
                result = await self._execute_tool_optimized(tool_name, args)
                
                response = {
                    "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
                    "isError": False
                }
                
                if not result.get("error"):
                    self.response_cache.set(cache_key, response)
                
                return response
                
            except Exception as e:
                return {
                    "content": [{"type": "text", "text": f"도구 실행 오류: {str(e)}"}],
                    "isError": True
                }
    
    async def _execute_tool_optimized(self, tool_name: str, args: Dict[str, Any]):
        """최적화된 도구 실행"""
        if tool_name == "analyze_food_image":
            from agents.tools.diet_tools import analyze_food_image_detailed
            return await analyze_food_image_detailed(
                user_id=args["user_id"],
                image_data=args["image_data"],
                meal_type=args.get("meal_type", "저녁")
            )
        
        elif tool_name == "get_nutrition_history":
            from agents.tools.diet_tools import get_nutrition_history
            return await get_nutrition_history(
                user_id=args["user_id"],
                days=args.get("days", 7)
            )
        
        elif tool_name == "create_user_profile":
            from agents.tools.user_rag_tools import create_user_profile
            return await create_user_profile(**args)
        
        elif tool_name == "get_user_context":
            from agents.tools.user_rag_tools import get_personalized_user_context
            return await get_personalized_user_context(args["user_id"])
        
        elif tool_name == "update_user_weight":
            from agents.tools.user_rag_tools import update_user_weight
            return await update_user_weight(
                user_id=args["user_id"],
                new_weight=args["new_weight"]
            )


def integrate_enhanced_mcp(app: FastAPI):
    """성능 개선된 MCP 통합"""
    mcp = EnhancedMCPIntegration(app)
    return app