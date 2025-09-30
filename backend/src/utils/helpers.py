"""
공통 유틸리티 함수들
재사용 가능한 헬퍼 함수 모음
"""

import uuid
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import json
import re


def generate_unique_id(prefix: str = "") -> str:
    """
    고유 ID 생성
    
    Args:
        prefix: ID 접두사
    
    Returns:
        생성된 고유 ID
    """
    unique_id = str(uuid.uuid4())
    return f"{prefix}_{unique_id}" if prefix else unique_id


def generate_hash(data: str) -> str:
    """
    데이터 해시 생성
    
    Args:
        data: 해시할 데이터
    
    Returns:
        SHA256 해시값
    """
    return hashlib.sha256(data.encode()).hexdigest()


def encode_base64(data: bytes) -> str:
    """
    Base64 인코딩
    
    Args:
        data: 인코딩할 바이트 데이터
    
    Returns:
        Base64 인코딩된 문자열
    """
    return base64.b64encode(data).decode('utf-8')


def decode_base64(encoded_data: str) -> bytes:
    """
    Base64 디코딩
    
    Args:
        encoded_data: Base64 인코딩된 문자열
    
    Returns:
        디코딩된 바이트 데이터
    """
    return base64.b64decode(encoded_data)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    날짜시간 포맷팅
    
    Args:
        dt: 날짜시간 객체
        format_str: 포맷 문자열
    
    Returns:
        포맷된 날짜시간 문자열
    """
    return dt.strftime(format_str)


def parse_datetime(date_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """
    문자열을 날짜시간으로 파싱
    
    Args:
        date_str: 날짜시간 문자열
        format_str: 포맷 문자열
    
    Returns:
        파싱된 날짜시간 객체
    """
    return datetime.strptime(date_str, format_str)


def calculate_age(birth_date: datetime) -> int:
    """
    나이 계산
    
    Args:
        birth_date: 생년월일
    
    Returns:
        계산된 나이
    """
    today = datetime.now()
    age = today.year - birth_date.year
    
    # 생일이 지나지 않았으면 1살 빼기
    if today.month < birth_date.month or \
       (today.month == birth_date.month and today.day < birth_date.day):
        age -= 1
    
    return age


def calculate_bmi(weight: float, height: float) -> float:
    """
    BMI 계산
    
    Args:
        weight: 체중 (kg)
        height: 신장 (cm)
    
    Returns:
        BMI 값
    """
    height_m = height / 100  # cm를 m로 변환
    return round(weight / (height_m ** 2), 2)


def get_bmi_category(bmi: float) -> str:
    """
    BMI 카테고리 분류
    
    Args:
        bmi: BMI 값
    
    Returns:
        BMI 카테고리
    """
    if bmi < 18.5:
        return "저체중"
    elif bmi < 25:
        return "정상"
    elif bmi < 30:
        return "과체중"
    else:
        return "비만"


def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    """
    기초대사율(BMR) 계산 (Harris-Benedict 공식)
    
    Args:
        weight: 체중 (kg)
        height: 신장 (cm)
        age: 나이
        gender: 성별 (male/female)
    
    Returns:
        기초대사율 (kcal/day)
    """
    if gender.lower() == 'male':
        bmr = 88.362 + (13.397 * weight) + (4.799 * height) - (5.677 * age)
    else:
        bmr = 447.593 + (9.247 * weight) + (3.098 * height) - (4.330 * age)
    
    return round(bmr, 2)


def calculate_tdee(bmr: float, activity_level: str) -> float:
    """
    총 일일 에너지 소비량(TDEE) 계산
    
    Args:
        bmr: 기초대사율
        activity_level: 활동량 (low/moderate/high)
    
    Returns:
        TDEE (kcal/day)
    """
    activity_multipliers = {
        'low': 1.2,      # 거의 운동하지 않음
        'moderate': 1.55, # 보통 활동량
        'high': 1.9      # 높은 활동량
    }
    
    multiplier = activity_multipliers.get(activity_level.lower(), 1.55)
    return round(bmr * multiplier, 2)


def validate_email(email: str) -> bool:
    """
    이메일 유효성 검사
    
    Args:
        email: 검사할 이메일 주소
    
    Returns:
        유효성 여부
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def sanitize_filename(filename: str) -> str:
    """
    파일명 정리 (특수문자 제거)
    
    Args:
        filename: 원본 파일명
    
    Returns:
        정리된 파일명
    """
    # 특수문자를 언더스코어로 대체
    sanitized = re.sub(r'[^\w\-_\.]', '_', filename)
    # 연속된 언더스코어 제거
    sanitized = re.sub(r'_+', '_', sanitized)
    return sanitized


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    리스트를 청크로 분할
    
    Args:
        lst: 분할할 리스트
        chunk_size: 청크 크기
    
    Returns:
        분할된 청크 리스트
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    안전한 JSON 파싱
    
    Args:
        json_str: JSON 문자열
        default: 파싱 실패 시 기본값
    
    Returns:
        파싱된 객체 또는 기본값
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def format_file_size(size_bytes: int) -> str:
    """
    파일 크기 포맷팅
    
    Args:
        size_bytes: 바이트 단위 크기
    
    Returns:
        포맷된 크기 문자열
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def get_week_dates(date: datetime) -> tuple[datetime, datetime]:
    """
    주의 시작일과 종료일 계산
    
    Args:
        date: 기준 날짜
    
    Returns:
        (주 시작일, 주 종료일) 튜플
    """
    # 월요일을 주의 시작으로 설정
    days_since_monday = date.weekday()
    week_start = date - timedelta(days=days_since_monday)
    week_end = week_start + timedelta(days=6)
    
    return week_start, week_end