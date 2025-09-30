#!/usr/bin/env python3
"""
Agentic AI Diet Coach API 테스트 스크립트
"""

import requests
import json

BASE_URL = "http://localhost:8001"

def test_health():
    """헬스체크 테스트"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health Check: {response.json()}")

def test_chat(user_id="test_user", message="안녕하세요! 오늘 아침 식사 추천해주세요."):
    """채팅 테스트"""
    data = {
        "user_id": user_id,
        "message": message
    }
    response = requests.post(f"{BASE_URL}/chat", data=data)
    result = response.json()
    print(f"Chat input: {json.dumps(data, indent=2, ensure_ascii=False)}")
    print(f"Chat Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
    print()

def test_image_chat(user_id="test_user", message="어제 저녁에 먹은 사진이야. 두명이서 먹었어.", image_path="chiken_beer.png"):
    """이미지와 함께 채팅 테스트"""
    try:
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {
                'user_id': user_id,
                'message': message
            }
            response = requests.post(f"{BASE_URL}/chat", data=data, files=files)
            result = response.json()
            print(f"Image Chat input: {json.dumps(data, indent=2, ensure_ascii=False)}")
            print(f"Image path: {image_path}")
            print(f"Image Chat Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
            print()
    except FileNotFoundError:
        print(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        print("대신 텍스트만 전송합니다.")
        test_chat(user_id, message)
    except Exception as e:
        print(f"이미지 업로드 오류: {e}")
        test_chat(user_id, message)

def test_demo(scenario="morning"):
    """데모 시나리오 테스트"""
    data = {
        "scenario": scenario,
        "user_id": "demo_user"
    }
    response = requests.post(f"{BASE_URL}/demo", data=data)
    result = response.json()
    print(f"Demo Response: {json.dumps(result, indent=2, ensure_ascii=False)}")

if __name__ == "__main__":
    print("🧪 Agentic AI Diet Coach API 테스트 시작\n")
    
    # 1. 헬스체크
    print("1. Health Check:")
    test_health()
    print()
    
    # # 2. 채팅 테스트
    # print("2. Chat Test:")
    # test_chat()
    # print()
    
    # # 3. 데모 테스트
    # print("3. Demo Test:")
    # test_chat(message="어제 저녁에 치킨에 맥주를 먹었는데, 오늘 식단이나 운동은 어떻게 하는게 좋을지 추천해줘.")
    # print()

    # 4. 이미지 분석 테스트
    print("4. Image Analysis Test:")
    test_image_chat(message="어제 저녁에 먹은 사진이야. 두명이서 먹었어.", image_path="chiken_beer.png")

    # 5. 이미지 분석 테스트
    print("5. Image Analysis Test:")
    test_image_chat(message="오늘 점심에 먹은 사진이야. 두명이서 먹었어.", image_path="launch.jpg")
    
    print("✅ 테스트 완료")