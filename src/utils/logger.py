"""
로깅 설정 유틸리티
중앙 집중식 로깅 관리
"""

import logging
import os
from datetime import datetime
from typing import Optional


class CustomFormatter(logging.Formatter):
    """커스텀 로그 포매터"""
    
    def format(self, record):
        """로그 레코드 포맷팅"""
        # 타임스탬프 추가
        record.timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 모듈명 단축
        if hasattr(record, 'name'):
            record.short_name = record.name.split('.')[-1]
        
        return super().format(record)


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    로거 설정 함수
    
    Args:
        name: 로거 이름
        level: 로그 레벨
        log_file: 로그 파일 경로 (선택사항)
    
    Returns:
        설정된 로거 인스턴스
    """
    logger = logging.getLogger(name)
    
    # 이미 핸들러가 있으면 중복 방지
    if logger.handlers:
        return logger
    
    # 로그 레벨 설정
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 포매터 설정
    formatter = CustomFormatter(
        fmt='%(timestamp)s - %(short_name)s - %(levelname)s - %(message)s'
    )
    
    # 콘솔 핸들러
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 파일 핸들러 (선택사항)
    if log_file:
        # 로그 디렉토리 생성
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


# 기본 로거 인스턴스
main_logger = setup_logger(
    name="ai_diet_coach",
    level=os.getenv("LOG_LEVEL", "INFO"),
    log_file="logs/app.log"
)