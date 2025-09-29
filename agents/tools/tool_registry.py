"""
Tool Registry for Agentic AI
LLM이 사용할 수 있는 모든 도구들을 등록하고 관리
"""

from typing import Dict, List, Any, Callable
from dataclasses import dataclass


@dataclass
class Tool:
    """도구 정의 클래스.
    
    Attributes:
        name (str): 도구의 고유 이름
        description (str): 도구의 기능 설명
        parameters (Dict[str, str]): 매개변수 이름과 타입 정보
        function (Callable): 실제 실행될 함수
    """
    name: str
    description: str
    parameters: Dict[str, str]
    function: Callable


class ToolRegistry:
    """도구 레지스트리 - LLM이 사용할 수 있는 모든 도구를 관리하는 중앙 레지스트리.
    
    AI 에이전트가 사용할 수 있는 모든 도구들을 등록, 관리, 실행하는 역할을 합니다.
    식단 분석, 코칭, 스케줄 관리, 사용자 관리 등의 도구들을 포함합니다.
    
    Attributes:
        tools (Dict[str, Tool]): 등록된 도구들의 딕셔너리
    """
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._register_all_tools()
    
    def _register_all_tools(self):
        """모든 도구를 등록"""
        from .diet_tools import (
            analyze_food_image, get_nutrition_history, 
            calculate_daily_nutrition, save_meal_record
        )
        from .coaching_tools import (
            generate_personalized_advice, recommend_exercise,
            check_health_progress, create_meal_plan
        )
        from .schedule_tools import (
            check_upcoming_events, set_meal_reminder,
            analyze_schedule_impact
        )
        from .user_tools import (
            get_user_profile, update_user_goals,
            get_user_preferences
        )
        
        # 식단 관련 도구들
        self._register_tool(
            "analyze_food_image",
            "업로드된 음식 사진을 분석하여 음식 종류, 칼로리, 영양소를 계산합니다",
            {"user_id": "string", "image_data": "bytes", "meal_type": "string"},
            analyze_food_image
        )
        
        self._register_tool(
            "get_nutrition_history",
            "사용자의 과거 N일간 영양 섭취 기록을 조회합니다",
            {"user_id": "string", "days": "integer"},
            get_nutrition_history
        )
        
        self._register_tool(
            "calculate_daily_nutrition",
            "특정 날짜의 총 영양소 섭취량을 계산합니다",
            {"user_id": "string", "date": "string"},
            calculate_daily_nutrition
        )
        
        self._register_tool(
            "save_meal_record",
            "새로운 식사 기록을 저장합니다",
            {"user_id": "string", "meal_data": "dict"},
            save_meal_record
        )
        
        # 코칭 관련 도구들
        self._register_tool(
            "generate_personalized_advice",
            "사용자의 현재 상태를 분석하여 개인 맞춤형 조언을 생성합니다",
            {"user_id": "string", "context": "string"},
            generate_personalized_advice
        )
        
        self._register_tool(
            "recommend_exercise",
            "사용자의 목표와 선호도에 맞는 운동을 추천합니다",
            {"user_id": "string", "current_activity": "string"},
            recommend_exercise
        )
        
        self._register_tool(
            "check_health_progress",
            "사용자의 건강 목표 달성 진행상황을 확인합니다",
            {"user_id": "string", "period": "string"},
            check_health_progress
        )
        
        self._register_tool(
            "create_meal_plan",
            "사용자 목표에 맞는 식단 계획을 생성합니다",
            {"user_id": "string", "duration": "string", "preferences": "list"},
            create_meal_plan
        )
        
        # 스케줄 관련 도구들
        self._register_tool(
            "check_upcoming_events",
            "향후 일정에서 회식, 약속 등을 확인합니다",
            {"user_id": "string", "days_ahead": "integer"},
            check_upcoming_events
        )
        
        self._register_tool(
            "set_meal_reminder",
            "식사 시간 알림을 설정합니다",
            {"user_id": "string", "meal_type": "string", "time": "string"},
            set_meal_reminder
        )
        
        self._register_tool(
            "analyze_schedule_impact",
            "예정된 일정이 식단에 미치는 영향을 분석합니다",
            {"user_id": "string", "event_type": "string", "date": "string"},
            analyze_schedule_impact
        )
        
        # 사용자 관련 도구들
        self._register_tool(
            "get_user_profile",
            "사용자의 프로필 정보를 조회합니다",
            {"user_id": "string"},
            get_user_profile
        )
        
        self._register_tool(
            "update_user_goals",
            "사용자의 건강 목표를 업데이트합니다",
            {"user_id": "string", "new_goals": "dict"},
            update_user_goals
        )
        
        self._register_tool(
            "get_user_preferences",
            "사용자의 음식 및 운동 선호도를 조회합니다",
            {"user_id": "string"},
            get_user_preferences
        )
    
    def _register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, str],
        function: Callable
    ):
        """도구를 레지스트리에 등록합니다.
        
        Args:
            name (str): 도구 이름
            description (str): 도구 설명
            parameters (Dict[str, str]): 매개변수 정보
            function (Callable): 실제 실행될 함수
        """
        tool = Tool(
            name=name,
            description=description,
            parameters=parameters,
            function=function
        )
        self.tools[name] = tool
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """LLM에게 제공할 도구 스키마를 반환합니다.
        
        Returns:
            List[Dict[str, Any]]: 도구들의 이름, 설명, 매개변수 정보
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self.tools.values()
        ]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """지정된 도구를 실행합니다.
        
        Args:
            tool_name (str): 실행할 도구의 이름
            **kwargs: 도구에 전달할 매개변수들
        
        Returns:
            Any: 도구 실행 결과
        
        Raises:
            ValueError: 존재하지 않는 도구명일 경우
        """
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        tool = self.tools[tool_name]
        
        # 비동기 함수인지 확인
        import asyncio
        if asyncio.iscoroutinefunction(tool.function):
            return await tool.function(**kwargs)
        else:
            return tool.function(**kwargs)
    
    def list_available_tools(self) -> List[str]:
        """등록된 모든 도구들의 이름 목록을 반환합니다.
        
        Returns:
            List[str]: 도구 이름들의 목록
        """
        return list(self.tools.keys())
    
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """특정 도구의 상세 정보를 반환합니다.
        
        Args:
            tool_name (str): 정보를 조회할 도구의 이름
        
        Returns:
            Dict[str, Any]: 도구의 상세 정보 또는 에러 메시지
        """
        if tool_name not in self.tools:
            return {"error": f"Tool '{tool_name}' not found"}
        
        tool = self.tools[tool_name]
        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }