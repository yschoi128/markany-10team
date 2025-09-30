"""
식단 관련 도구들
"""

import boto3
import base64
import json
from typing import Dict, Any
from datetime import datetime

async def analyze_food_image_detailed(user_id: str, image_data: Any, meal_type: str = "저녁") -> Dict[str, Any]:
    """
    음식 이미지를 상세 분석하여 메뉴, 칼로리, 영양소 계산 및 식단 조언 제공
    """
    try:
        # 이미지 데이터 처리
        if isinstance(image_data, str):
            # base64 문자열인 경우
            image_bytes = base64.b64decode(image_data)
        else:
            # bytes인 경우
            image_bytes = image_data
        
        # Bedrock Claude로 이미지 분석
        bedrock_client = boto3.client('bedrock-runtime', region_name='ap-northeast-2')
        
        # 이미지를 base64로 인코딩
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # 상세 분석 프롬프트
        analysis_prompt = f"""
이 음식 이미지를 전문 영양사 관점에서 상세히 분석해주세요.

**반드시 다음 형식으로 답변하세요:**

## 🍽️ 식별된 음식 목록
1. **[음식명1]** - [예상 분량] - [칼로리]kcal
   - 탄수화물: [g], 단백질: [g], 지방: [g]
2. **[음식명2]** - [예상 분량] - [칼로리]kcal
   - 탄수화물: [g], 단백질: [g], 지방: [g]

## 📊 총 영양 정보
- **총 칼로리**: [총합]kcal
- **탄수화물**: [총합]g
- **단백질**: [총합]g  
- **지방**: [총합]g

## 💡 식단 평가 및 조언
- **긍정적인 점**: [구체적 설명]
- **개선점**: [구체적 개선 방안]
- **추천 운동**: [소모 칼로리 기준 운동 추천]

## 🏃‍♂️ 칼로리 소모 운동 추천
이 식사([총 칼로리]kcal)를 소모하려면:
- 빠른 걷기: [시간]분
- 조깅: [시간]분  
- 자전거: [시간]분

가능한 한 정확하고 구체적으로 분석해주세요.
"""

        messages = [{
            "role": "user",
            "content": [
                {
                    "image": {
                        "format": "jpeg",
                        "source": {
                            "bytes": image_bytes
                        }
                    }
                },
                {
                    "text": analysis_prompt
                }
            ]
        }]
        
        response = bedrock_client.converse(
            modelId='anthropic.claude-3-haiku-20240307-v1:0',
            messages=messages,
            inferenceConfig={'maxTokens': 1500}
        )
        
        analysis_result = response['output']['message']['content'][0]['text']
        
        return {
            "success": True,
            "analysis": analysis_result,
            "meal_type": meal_type,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "message": f"{meal_type} 이미지 분석이 완료되었습니다."
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "이미지 분석 중 오류가 발생했습니다."
        }