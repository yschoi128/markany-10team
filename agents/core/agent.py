"""
Agentic AI Diet Coach
LLM이 스스로 판단하여 도구를 선택하고 실행하는 자율적 에이전트
"""

import json
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime

from agents.tools.tool_registry import ToolRegistry
from agents.memory.conversation_memory import ConversationMemory
from src.services.bedrock_service import bedrock_service


class AgenticDietCoach:
    """자율적 AI 식단 코치 에이전트.
    
    LLM이 스스로 판단하여 도구를 선택하고 실행하는 완전 자율적 AI 시스템.
    사용자의 식단, 운동, 건강 관리를 위한 개인 맞춤형 코칭을 제공합니다.
    
    Attributes:
        tool_registry (ToolRegistry): 사용 가능한 도구들을 관리하는 레지스트리
        memory (ConversationMemory): 대화 기록 및 컨텍스트 관리
        bedrock (BedrockService): AWS Bedrock AI 서비스
        system_prompt (str): AI 에이전트의 기본 시스템 프롬프트
    """
    
    def __init__(self):
        self.tool_registry = ToolRegistry()
        self.memory = ConversationMemory()
        self.bedrock = bedrock_service
        
        # 시스템 프롬프트 정의
        self.system_prompt = """
당신은 AI 식단 코치 에이전트입니다. 사용자의 건강한 식습관을 돕는 것이 목표입니다.

**핵심 역할:**
1. 식사 이미지 분석 및 영양소 계산
2. 개인 맞춤형 식단/운동 추천
3. 스케줄 기반 식사 계획
4. 실시간 코칭 및 조언

**사용 가능한 도구들:**
{tools_description}

**중요한 원칙:**
- 사용자 입력을 분석하여 적절한 도구를 선택하세요
- 복잡한 요청은 여러 도구를 순차적으로 사용하세요
- 항상 사용자의 건강 목표와 선호도를 고려하세요
- 친근하고 격려하는 톤으로 대화하세요

도구 사용 시 다음 형식을 따르세요:
```json
{
  "action": "tool_name",
  "parameters": {"param1": "value1", "param2": "value2"}
}
```

여러 도구를 사용해야 할 때는 단계별로 실행하고 결과를 종합하여 답변하세요.
"""
    
    async def process_input(
        self,
        user_input: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """간단한 사용자 입력 처리 (폴백 버전)"""
        try:
            # 간단한 키워드 기반 응답
            user_input_lower = user_input.lower()
            
            if any(word in user_input_lower for word in ["추천", "식사", "아침", "점심", "저녁"]):
                response = "건강한 식단을 추천드립니다! 균형 잡힌 영양소 섭취를 위해 야채, 단백질, 탄수화물을 골고루 드세요."
            elif any(word in user_input_lower for word in ["운동", "헬스", "다이어트"]):
                response = "규칙적인 운동을 추천합니다! 하루 30분 걷기부터 시작해보세요."
            elif any(word in user_input_lower for word in ["안녕", "hello", "hi"]):
                response = "안녕하세요! AI 식단 코치입니다. 건강한 식습관과 운동에 대해 도움을 드릴 수 있습니다."
            else:
                response = "무엇을 도와드릴까요? 식단 추천, 운동 조언 등에 대해 질문해주세요!"
            
            return {
                "success": True,
                "response": response,
                "actions_taken": [{"action": "simple_response", "success": True}],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "죄송합니다. 처리 중 오류가 발생했습니다. 다시 시도해주세요.",
                "timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_and_plan(
        self,
        user_input: str,
        system_prompt: str,
        conversation_history: List[Dict],
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """사용자 입력을 분석하고 실행할 도구들의 계획을 수립합니다.
        
        Args:
            user_input (str): 사용자 입력
            system_prompt (str): 시스템 프롬프트
            conversation_history (List[Dict]): 최근 대화 기록
            context (Optional[Dict[str, Any]]): 추가 컨텍스트
        
        Returns:
            Dict[str, Any]: 분석 결과 및 실행 계획
                - intent (str): 사용자 의도
                - actions (List[Dict]): 실행할 도구들의 목록
        """
        
        # 컨텍스트 정보 추가
        context_info = ""
        if context and context.get("image_data"):
            context_info = "\n[이미지가 첨부되었습니다]"
        
        # 대화 기록 포맷팅
        history_text = "\n".join([
            f"사용자: {msg['user']}\n코치: {msg['assistant']}"
            for msg in conversation_history[-3:]  # 최근 3개 대화
        ])
        
        planning_prompt = f"""
사용자 입력: "{user_input}"{context_info}

최근 대화:
{history_text}

위 입력을 분석하여 다음을 결정하세요:
1. 사용자의 의도는 무엇인가?
2. 어떤 도구들을 어떤 순서로 사용해야 하는가?
3. 각 도구에 필요한 매개변수는 무엇인가?

응답 형식:
{{
  "intent": "사용자 의도 분석",
  "actions": [
    {{
      "action": "도구명",
      "parameters": {{"매개변수": "값"}},
      "reason": "이 도구를 사용하는 이유"
    }}
  ]
}}
"""
        
        response = await self.bedrock.process_natural_language(
            user_input=planning_prompt,
            user_profile=None,  # 필요시 사용자 프로필 조회
            conversation_history=[]
        )
        
        # 기본 응답 처리 - JSON 파싱 없이 간단한 액션 생성
        try:
            user_input_lower = user_input.lower()
            
            # 간단한 키워드 기반 액션 결정
            if any(word in user_input_lower for word in ["추천", "식사", "아침", "점심", "저녁"]):
                return {
                    "intent": "meal_recommendation",
                    "actions": [{
                        "action": "generate_personalized_advice",
                        "parameters": {"user_id": "demo_user", "context": user_input},
                        "reason": "식사 추천 요청"
                    }]
                }
            elif any(word in user_input_lower for word in ["운동", "헬스", "다이어트"]):
                return {
                    "intent": "exercise_recommendation", 
                    "actions": [{
                        "action": "recommend_exercise",
                        "parameters": {"user_id": "demo_user"},
                        "reason": "운동 추천 요청"
                    }]
                }
            else:
                return {
                    "intent": "general_chat",
                    "actions": [{
                        "action": "generate_personalized_advice",
                        "parameters": {"user_id": "demo_user", "context": user_input},
                        "reason": "일반 상담"
                    }]
                }
        except:
            return {"intent": "general_chat", "actions": []}
    
    async def _execute_planned_actions(
        self,
        actions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """계획된 도구들을 순차적으로 실행합니다.
        
        Args:
            actions (List[Dict[str, Any]]): 실행할 도구들의 목록
        
        Returns:
            List[Dict[str, Any]]: 각 도구의 실행 결과 목록
        """
        
        results = []
        
        for action in actions:
            try:
                action_name = action.get("action")
                parameters = action.get("parameters", {})
                
                if action_name in self.tool_registry.tools:
                    result = await self.tool_registry.execute_tool(
                        action_name, **parameters
                    )
                    
                    results.append({
                        "action": action_name,
                        "parameters": parameters,
                        "result": result,
                        "success": True
                    })
                else:
                    results.append({
                        "action": action_name,
                        "parameters": parameters,
                        "error": f"Unknown tool: {action_name}",
                        "success": False
                    })
                    
            except Exception as e:
                results.append({
                    "action": action.get("action", "unknown"),
                    "parameters": action.get("parameters", {}),
                    "error": str(e),
                    "success": False
                })
        
        return results
    
    async def _generate_final_response(
        self,
        user_input: str,
        execution_results: List[Dict[str, Any]],
        system_prompt: str
    ) -> Dict[str, Any]:
        """도구 실행 결과를 종합하여 사용자에게 제공할 최종 응답을 생성합니다.
        
        Args:
            user_input (str): 원본 사용자 입력
            execution_results (List[Dict[str, Any]]): 도구 실행 결과들
            system_prompt (str): 시스템 프롬프트
        
        Returns:
            Dict[str, Any]: 최종 응답 메시지
        """
        
        # 간단한 결과 요약
        success_actions = [r for r in execution_results if r.get("success", False)]
        failed_actions = [r for r in execution_results if not r.get("success", False)]
        
        # 간단한 응답 생성
        if success_actions:
            return {"response": f"요청을 처리했습니다! {len(success_actions)}개의 작업을 성공적으로 수행했습니다."}
        elif failed_actions:
            return {"response": "죄송합니다. 작업 수행 중 오류가 발생했습니다."}
        else:
            return {"response": "안녕하세요! 무엇을 도와드릴까요?"}
    
    def _format_tools_description(self) -> str:
        """사용 가능한 도구들의 설명을 AI가 이해할 수 있는 형태로 포맷팅합니다.
        
        Returns:
            str: 포맷팅된 도구 설명 문자열
        """
        tools_schema = self.tool_registry.get_tools_schema()
        
        descriptions = []
        for tool in tools_schema:
            params = ", ".join([f"{k}: {v}" for k, v in tool["parameters"].items()])
            descriptions.append(f"- {tool['name']}: {tool['description']} (매개변수: {params})")
        
        return "\n".join(descriptions)


# 전역 에이전트 인스턴스
diet_coach_agent = AgenticDietCoach()