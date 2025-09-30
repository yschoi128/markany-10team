"""
Conversation Memory System
대화 기록 관리 및 컨텍스트 유지
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json


class ConversationMemory:
    """대화 기록 및 컨텍스트 관리 클래스.
    
    사용자와 AI 간의 대화 기록을 저장하고 관리하며, 컨텍스트 분석을 통해
    사용자의 관심사, 기분, 언급된 음식 등을 추출하여 개인화된 서비스를 제공합니다.
    
    Attributes:
        max_history (int): 유지할 최대 대화 기록 수
        conversations (Dict[str, List[Dict]]): 사용자별 대화 기록
        user_contexts (Dict[str, Dict]): 사용자별 컨텍스트 정보
    """
    
    def __init__(self, max_history: int = 20):
        """
        Args:
            max_history: 유지할 최대 대화 기록 수
        """
        self.max_history = max_history
        self.conversations: Dict[str, List[Dict[str, Any]]] = {}
        self.user_contexts: Dict[str, Dict[str, Any]] = {}
    
    async def save_conversation(
        self,
        user_id: str,
        user_message: str,
        assistant_response: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """사용자와 AI 간의 대화를 저장합니다.
        
        대화 기록을 시간순으로 저장하고, 최대 기록 수를 초과하면
        오래된 기록을 자동으로 삭제하여 메모리 효율성을 유지합니다.
        
        Args:
            user_id (str): 사용자 고유 식별자
            user_message (str): 사용자가 입력한 메시지
            assistant_response (str): AI가 생성한 응답
            metadata (Optional[Dict[str, Any]]): 추가 메타데이터 (이미지 정보 등)
        """
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user_message,
            "assistant": assistant_response,
            "metadata": metadata or {}
        }
        
        self.conversations[user_id].append(conversation_entry)
        
        # 최대 기록 수 제한
        if len(self.conversations[user_id]) > self.max_history:
            self.conversations[user_id] = self.conversations[user_id][-self.max_history:]
    
    async def get_conversation_history(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        대화 기록 조회
        
        Args:
            user_id: 사용자 ID
            limit: 조회할 대화 수
        
        Returns:
            대화 기록 리스트
        """
        if user_id not in self.conversations:
            return []
        
        return self.conversations[user_id][-limit:]
    
    async def get_recent_context(
        self,
        user_id: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        최근 컨텍스트 조회
        
        Args:
            user_id: 사용자 ID
            hours: 조회할 시간 범위
        
        Returns:
            최근 컨텍스트 정보
        """
        if user_id not in self.conversations:
            return {}
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_conversations = []
        
        for conv in self.conversations[user_id]:
            conv_time = datetime.fromisoformat(conv["timestamp"])
            if conv_time >= cutoff_time:
                recent_conversations.append(conv)
        
        # 컨텍스트 분석
        context = {
            "recent_topics": await self._extract_topics(recent_conversations),
            "user_mood": self._analyze_mood(recent_conversations),
            "mentioned_foods": await self._extract_foods(recent_conversations),
            "conversation_count": len(recent_conversations),
            "time_range": f"최근 {hours}시간"
        }
        
        return context
    
    async def update_user_context(
        self,
        user_id: str,
        context_key: str,
        context_value: Any
    ) -> None:
        """
        사용자 컨텍스트 업데이트
        
        Args:
            user_id: 사용자 ID
            context_key: 컨텍스트 키
            context_value: 컨텍스트 값
        """
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = {}
        
        self.user_contexts[user_id][context_key] = {
            "value": context_value,
            "updated_at": datetime.now().isoformat()
        }
    
    async def get_user_context(
        self,
        user_id: str,
        context_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        사용자 컨텍스트 조회
        
        Args:
            user_id: 사용자 ID
            context_key: 특정 컨텍스트 키 (None이면 전체 조회)
        
        Returns:
            컨텍스트 정보
        """
        if user_id not in self.user_contexts:
            return {}
        
        if context_key:
            return self.user_contexts[user_id].get(context_key, {})
        else:
            return self.user_contexts[user_id]
    
    async def clear_old_conversations(
        self,
        days: int = 30
    ) -> int:
        """
        오래된 대화 기록 정리
        
        Args:
            days: 보관할 일수
        
        Returns:
            정리된 대화 수
        """
        cutoff_time = datetime.now() - timedelta(days=days)
        cleared_count = 0
        
        for user_id in list(self.conversations.keys()):
            original_count = len(self.conversations[user_id])
            
            # 최근 대화만 유지
            self.conversations[user_id] = [
                conv for conv in self.conversations[user_id]
                if datetime.fromisoformat(conv["timestamp"]) >= cutoff_time
            ]
            
            cleared_count += original_count - len(self.conversations[user_id])
            
            # 빈 대화 기록 제거
            if not self.conversations[user_id]:
                del self.conversations[user_id]
        
        return cleared_count
    
    async def _extract_topics(self, conversations: List[Dict[str, Any]]) -> List[str]:
        """대화에서 주요 토픽 동적 추출 (AI 기반)"""
        try:
            from src.services.bedrock_service import bedrock_service
            
            # 최근 대화 텍스트 결합
            conversation_text = " ".join([
                conv["user"] for conv in conversations[-10:]  # 최근 10개 대화
            ])
            
            if not conversation_text.strip():
                return []
            
            # AI에게 토픽 추출 요청
            topic_prompt = f"""
다음 대화에서 주요 토픽들을 추출해주세요:

"{conversation_text}"

가능한 토픽: 식단, 운동, 체중관리, 스케줄, 건강, 영양, 스트레스, 수면, 기타

응답 형식: ["토픽1", "토픽2", "토픽3"]
토픽이 없으면 빈 배열 []로 응답하세요.
"""
            
            response = await bedrock_service.process_natural_language(
                user_input=topic_prompt,
                user_profile=None,
                conversation_history=[]
            )
            
            # JSON 파싱 시도
            import re
            import json
            
            response_text = response.get("response", "") if isinstance(response, dict) else str(response)
            
            array_match = re.search(r'\[.*?\]', response_text)
            if array_match:
                try:
                    topics = json.loads(array_match.group())
                    return topics[:5] if isinstance(topics, list) else []
                except:
                    pass
            
            # AI 추출 실패 시 폴백
            return self._extract_topics_fallback(conversations)
            
        except Exception:
            # 모든 오류 시 폴백
            return self._extract_topics_fallback(conversations)
    
    def _extract_topics_fallback(self, conversations: List[Dict[str, Any]]) -> List[str]:
        """
        폴백: 하드코딩된 토픽 추출
        
        NOTE: AI 추출 실패 시 사용되는 하드코딩된 폴백입니다.
        한국어 키워드 기반으로 구성되었으며, 필요시 키워드를 추가/수정할 수 있습니다.
        
        TODO: 더 정교한 NLP 모델이나 토픽 모델링으로 대체 가능
        """
        topics = []
        
        for conv in conversations:
            user_msg = conv["user"].lower()
            
            # HARDCODED: 한국어 키워드 기반 토픽 분류 (정확성을 위한 의도적 하드코딩)
            if any(word in user_msg for word in ["음식", "식사", "먹", "칼로리", "영양", "메뉴"]):
                topics.append("식단")
            if any(word in user_msg for word in ["운동", "헬스", "요가", "달리기", "헬스장", "조깅"]):
                topics.append("운동")
            if any(word in user_msg for word in ["체중", "살", "다이어트", "감량", "비만"]):
                topics.append("체중관리")
            if any(word in user_msg for word in ["회식", "약속", "일정", "스케줄", "모임"]):
                topics.append("스케줄")
            if any(word in user_msg for word in ["건강", "질병", "아프", "피로", "컨디션"]):
                topics.append("건강")
            if any(word in user_msg for word in ["스트레스", "힘들", "우울", "불안", "기분"]):
                topics.append("스트레스")
        
        # 중복 제거 및 빈도순 정렬
        unique_topics = list(set(topics))
        return unique_topics[:5]  # 상위 5개만 반환
    
    def _analyze_mood(self, conversations: List[Dict[str, Any]]) -> str:
        """대화에서 사용자 기분 분석"""
        positive_words = ["좋", "감사", "훌륭", "완벽", "성공", "기쁘"]
        negative_words = ["힘들", "어려", "실패", "포기", "스트레스", "걱정"]
        
        positive_count = 0
        negative_count = 0
        
        for conv in conversations:
            user_msg = conv["user"].lower()
            
            positive_count += sum(1 for word in positive_words if word in user_msg)
            negative_count += sum(1 for word in negative_words if word in user_msg)
        
        if positive_count > negative_count:
            return "긍정적"
        elif negative_count > positive_count:
            return "부정적"
        else:
            return "중립적"
    
    async def _extract_foods(self, conversations: List[Dict[str, Any]]) -> List[str]:
        """대화에서 언급된 음식들 동적 추출 (AI 기반)"""
        try:
            # AI를 통한 동적 음식 추출
            from src.services.bedrock_service import bedrock_service
            
            # 최근 대화 텍스트 결합
            conversation_text = " ".join([
                conv["user"] for conv in conversations[-5:]  # 최근 5개 대화만
            ])
            
            if not conversation_text.strip():
                return []
            
            # AI에게 음식 추출 요청
            extraction_prompt = f"""
다음 대화에서 언급된 모든 음식, 요리, 음료를 추출해주세요:

"{conversation_text}"

응답 형식: ["음식1", "음식2", "음식3"]
음식이 없으면 빈 배열 []로 응답하세요.
"""
            
            response = await bedrock_service.process_natural_language(
                user_input=extraction_prompt,
                user_profile=None,
                conversation_history=[]
            )
            
            # JSON 파싱 시도
            import re
            import json
            
            response_text = response.get("response", "") if isinstance(response, dict) else str(response)
            
            # 배열 패턴 찾기
            array_match = re.search(r'\[.*?\]', response_text)
            if array_match:
                try:
                    foods = json.loads(array_match.group())
                    return foods if isinstance(foods, list) else []
                except:
                    pass
            
            # AI 추출 실패 시 폴백: 기본 키워드 매칭
            return self._extract_foods_fallback(conversations)
            
        except Exception:
            # 모든 오류 시 폴백 사용
            return self._extract_foods_fallback(conversations)
    
    def _extract_foods_fallback(self, conversations: List[Dict[str, Any]]) -> List[str]:
        """
        폴백: 하드코딩된 음식 키워드 매칭
        
        NOTE: 이 부분은 AI 추출 실패 시 사용되는 하드코딩된 폴백입니다.
        정확성을 위해 한국 음식 위주로 구성되었으며, 필요시 키워드를 추가/수정할 수 있습니다.
        
        TODO: 향후 음식 데이터베이스나 더 정교한 NER 모델로 대체 가능
        """
        foods = []
        
        # HARDCODED: 한국 음식 위주 키워드 (정확성을 위한 의도적 하드코딩)
        food_keywords = [
            # 주식류
            "밥", "쌀", "현미", "잡곡", "죽", "누룽지",
            # 국물류
            "국", "찌개", "탕", "전골", "수프", "라면", "우동", "냉면",
            # 반찬류
            "김치", "나물", "무침", "조림", "볶음", "구이",
            # 육류
            "고기", "소고기", "돼지고기", "닭고기", "치킨", "삼겹살", "갈비",
            # 해산물
            "생선", "연어", "고등어", "참치", "새우", "오징어", "조개",
            # 서양음식
            "피자", "햄버거", "파스타", "스테이크", "샐러드", "샌드위치",
            # 기타
            "계란", "두부", "우유", "빵", "과일", "야채", "견과류"
        ]
        
        for conv in conversations:
            user_msg = conv["user"].lower()
            
            for food in food_keywords:
                if food in user_msg:
                    foods.append(food)
        
        return list(set(foods))
    
    async def get_conversation_summary(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        대화 요약 정보 생성
        
        Args:
            user_id: 사용자 ID
            days: 요약할 일수
        
        Returns:
            대화 요약 정보
        """
        if user_id not in self.conversations:
            return {"message": "대화 기록이 없습니다"}
        
        cutoff_time = datetime.now() - timedelta(days=days)
        recent_conversations = [
            conv for conv in self.conversations[user_id]
            if datetime.fromisoformat(conv["timestamp"]) >= cutoff_time
        ]
        
        if not recent_conversations:
            return {"message": f"최근 {days}일간 대화 기록이 없습니다"}
        
        # 요약 통계
        total_conversations = len(recent_conversations)
        topics = await self._extract_topics(recent_conversations)
        mood = self._analyze_mood(recent_conversations)
        mentioned_foods = await self._extract_foods(recent_conversations)
        
        # 가장 최근 대화
        latest_conversation = recent_conversations[-1]
        
        return {
            "period": f"최근 {days}일간",
            "total_conversations": total_conversations,
            "main_topics": topics,
            "overall_mood": mood,
            "mentioned_foods": mentioned_foods,
            "latest_conversation": {
                "timestamp": latest_conversation["timestamp"],
                "user_message": latest_conversation["user"][:100] + "..." if len(latest_conversation["user"]) > 100 else latest_conversation["user"]
            },
            "engagement_level": "높음" if total_conversations > 10 else "보통" if total_conversations > 3 else "낮음"
        }