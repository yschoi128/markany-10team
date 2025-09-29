# 🤖 Agentic AI Diet Coach

**진정한 Agentic AI 시스템** - LLM이 스스로 판단하여 도구를 선택하고 실행하는 자율적 AI 식단 코치

## 🎯 Agentic AI의 핵심 특징

### ✅ **자율적 의사결정**
- LLM이 사용자 입력을 분석하여 **스스로** 적절한 도구 선택
- 고정된 플로우가 아닌 **상황별 동적 판단**

### ✅ **다단계 추론**
- 복잡한 요청을 여러 단계로 분해하여 처리
- 이전 결과를 바탕으로 다음 행동 결정

### ✅ **컨텍스트 유지**
- 대화 기록과 사용자 상태를 메모리로 관리
- 개인화된 연속적 상호작용

## 🏗️ 아키텍처

```
agents/
├── core/
│   └── agent.py              # 핵심 Agent 로직
├── tools/
│   ├── tool_registry.py      # 도구 등록 시스템
│   ├── diet_tools.py         # 식단 관련 도구들
│   ├── coaching_tools.py     # 코칭 관련 도구들
│   ├── schedule_tools.py     # 스케줄 관리 도구들
│   └── user_tools.py         # 사용자 관리 도구들
├── memory/
│   └── conversation_memory.py # 대화 기록 관리
└── api/
    └── agent_api.py          # 단일 API 엔드포인트
```

## 🚀 사용법

### 1. Agent 서버 실행
```bash
python run_agent.py
```

### 2. 단일 엔드포인트로 모든 기능 사용
```bash
# 일반 대화
curl -X POST "http://localhost:8001/chat" \
  -F "user_id=user123" \
  -F "message=오늘 아침 뭐 먹을까요?"

# 이미지와 함께 대화
curl -X POST "http://localhost:8001/chat" \
  -F "user_id=user123" \
  -F "message=이 음식 칼로리 알려주세요" \
  -F "image=@food.jpg"

# 데모 시나리오
curl -X POST "http://localhost:8001/demo" \
  -F "scenario=morning" \
  -F "user_id=demo_user"
```

## 🧠 Agent 동작 원리

### 1. **완전 동적 처리**
```
사용자: "어제 회식에서 많이 먹었는데 오늘 뭐 먹을까?"

Agent 분석 (AI 기반):
- 의도 분석: AI가 자연어로 의도 파악
- 음식 추출: AI가 "회식" 컨텍스트에서 관련 음식 추론
- 도구 선택: AI가 상황에 맞는 최적 도구 조합 결정
- 추천 생성: AI가 개인 프로필 기반 맞춤 추천
```

### 2. **도구 선택 및 실행**
```json
{
  "actions": [
    {
      "action": "get_nutrition_history",
      "parameters": {"user_id": "user123", "days": 1},
      "reason": "어제 섭취량 확인"
    },
    {
      "action": "generate_personalized_advice", 
      "parameters": {"user_id": "user123", "context": "어제 과식"},
      "reason": "맞춤형 식단 조언"
    }
  ]
}
```

### 3. **결과 종합 및 응답**
```
"어제 회식에서 2,100kcal 섭취하셨네요! 목표보다 500kcal 많습니다. 
오늘은 가벼운 샐러드와 단백질 위주로 드시고, 
30분 정도 산책하시면 좋겠어요. 🥗"
```

## 🛠️ 사용 가능한 도구들

### 📊 **식단 관리**
- `analyze_food_image`: 음식 사진 분석
- `get_nutrition_history`: 영양 섭취 기록 조회
- `calculate_daily_nutrition`: 일일 영양소 계산
- `save_meal_record`: 식사 기록 저장

### 🏃 **코칭 & 운동**
- `generate_personalized_advice`: 개인 맞춤 조언
- `recommend_exercise`: 운동 추천
- `check_health_progress`: 건강 진행상황 확인
- `create_meal_plan`: 식단 계획 생성

### 📅 **스케줄 관리**
- `check_upcoming_events`: 예정된 이벤트 확인
- `set_meal_reminder`: 식사 알림 설정
- `analyze_schedule_impact`: 일정의 식단 영향 분석

### 👤 **사용자 관리**
- `get_user_profile`: 사용자 프로필 조회
- `update_user_goals`: 목표 업데이트
- `get_user_preferences`: 선호도 조회

## 💡 예시 대화

### 🌅 **아침 인사**
```
사용자: "안녕하세요! 오늘 아침 뭐 먹을까요?"

Agent 실행:
1. get_user_profile() → 사용자 목표 확인
2. get_nutrition_history(days=1) → 어제 섭취량 확인  
3. create_meal_plan(duration="day") → 오늘 식단 계획

응답: "안녕하세요! 체중 감량 목표에 맞춰 오트밀+베리+아몬드 (250kcal) 추천드려요!"
```

### 🍗 **음식 질문**
```
사용자: "치킨 먹어도 될까요? 점심에 햄버거 먹었어요."

Agent 실행:
1. calculate_daily_nutrition() → 오늘 섭취량 확인
2. get_user_profile() → 목표 칼로리 확인
3. generate_personalized_advice() → 맞춤 조언

응답: "점심 햄버거로 이미 800kcal 섭취하셨네요. 치킨보다는 샐러드나 구운 닭가슴살 어떠세요?"
```

### 📸 **이미지 분석**
```
사용자: [음식 사진 업로드] "이거 칼로리 얼마나 될까요?"

Agent 실행:
1. analyze_food_image() → 이미지 분석 및 저장
2. generate_personalized_advice() → 섭취 후 조언

응답: "김치찌개 1인분으로 약 320kcal입니다. 오늘 목표 칼로리 내에서 적절한 선택이에요!"
```

## 🔄 동적 vs 하드코딩 처리

| 구분 | 하드코딩 방식 | 동적 AI 방식 |
|------|-------------|----------------|
| **음식 인식** | 고정 키워드 리스트 | AI가 컨텍스트로 추론 |
| **토픽 분류** | if-else 분기 | AI가 의미 기반 분류 |
| **운동 추천** | 목표별 고정 메뉴 | AI가 상황 맞춤 생성 |
| **식단 제안** | 하드코딩 메뉴DB | AI가 실시간 개인화 |
| **확장성** | 개발자가 수동 추가 | AI가 자동 학습/적응 |
| **정확성** | 폴백으로 보장 | AI 우선, 실패시 폴백 |

### 🛡️ **안전장치 (Fallback System)**
```python
# AI 우선 처리 → 실패시 하드코딩 폴백
try:
    # AI 기반 동적 처리
    result = await ai_extract_foods(conversation)
except:
    # 하드코딩된 안전장치
    result = fallback_extract_foods(conversation)
```

## 🎮 데모 시나리오

```bash
# 아침 인사
curl -X POST "http://localhost:8001/demo" -F "scenario=morning"

# 음식 질문  
curl -X POST "http://localhost:8001/demo" -F "scenario=food_question"

# 운동 조언
curl -X POST "http://localhost:8001/demo" -F "scenario=exercise"

# 진행상황 확인
curl -X POST "http://localhost:8001/demo" -F "scenario=progress"
```

## 📝 **개발자 가이드**

### 🔧 **하드코딩 부분 수정 방법**

1. **음식 키워드 추가**:
```python
# agents/memory/conversation_memory.py
food_keywords = [
    "새로운음식",  # 여기에 추가
    # 기존 키워드들...
]
```

2. **운동 메뉴 추가**:
```python
# agents/tools/coaching_tools.py
# _generate_exercise_recommendations_fallback() 함수에서
recommendations.append({
    "exercise": "새운동", 
    "duration": 30, 
    "calories_burn": 200
})
```

3. **식단 메뉴 추가**:
```python
# agents/tools/coaching_tools.py
# meal_database에 새 메뉴 추가
```

### ⚡ **성능 최적화**
- AI 호출 실패시 즉시 폴백으로 전환
- 하드코딩 부분은 **의도적 설계**로 안정성 보장
- 필요시 AI 모델을 더 가벼운 모델로 교체 가능

---

**🎯 이제 진정한 Agentic AI와 대화해보세요!** 
**AI 우선 + 안전장치 완비** 🤖✨🛡️