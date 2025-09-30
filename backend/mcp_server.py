"""
독립적인 MCP 서버 (포트 8002)
"""

import asyncio
import json
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# MCP 서버 생성
server = Server("ai-diet-coach")

@server.list_tools()
async def list_tools() -> list[Tool]:
    """사용 가능한 도구 목록"""
    return [
        Tool(
            name="analyze_food",
            description="음식 이미지 분석 및 영양소 계산",
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "image_data": {"type": "string"}
                }
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """도구 실행"""
    if name == "analyze_food":
        # 기존 함수 호출
        from agents.tools.diet_tools import analyze_food_image
        result = await analyze_food_image(**arguments)
        return [TextContent(type="text", text=json.dumps(result))]
    
    raise ValueError(f"Unknown tool: {name}")

async def main():
    """MCP 서버 실행"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())