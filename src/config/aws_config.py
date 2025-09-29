"""
AWS 서비스 설정 및 클라이언트 관리 모듈
각 AWS 서비스별 클라이언트를 중앙 집중식으로 관리
"""

import boto3
import os
from typing import Optional
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import logging

# 환경 변수 로드
load_dotenv()

logger = logging.getLogger(__name__)


class AWSConfig:
    """AWS 서비스 설정 및 클라이언트 관리 클래스"""
    
    def __init__(self):
        """AWS 클라이언트 초기화"""
        # AWS 자격 증명 설정
        self.region = os.getenv('AWS_REGION', 'us-east-1')
        self.access_key = os.getenv('AWS_ACCESS_KEY_ID')
        self.secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        self.session_token = os.getenv('AWS_SESSION_TOKEN')
        
        # 클라이언트 캐시
        self._s3_client = None
        self._dynamodb_client = None
        self._bedrock_client = None
        self._sns_client = None
        self._lambda_client = None
        
        self._validate_credentials()
    
    def _validate_credentials(self) -> None:
        """AWS 자격 증명 유효성 검사"""
        # 환경 변수나 AWS 프로필이 설정되어 있는지 확인
        if not self.access_key or not self.secret_key:
            # AWS CLI 프로필이나 IAM 역할을 사용할 수 있는지 확인
            try:
                # 기본 세션으로 자격 증명 테스트
                session = boto3.Session()
                credentials = session.get_credentials()
                if credentials is None:
                    logger.warning("AWS credentials not found. Using default configuration.")
                    # 개발 환경에서는 경고만 출력하고 계속 진행
                else:
                    logger.info("Using AWS credentials from default profile or IAM role")
            except Exception as e:
                logger.warning(f"AWS credentials validation failed: {e}. Continuing with default configuration.")
    
    def _create_client(self, service_name: str) -> boto3.client:
        """AWS 클라이언트 생성 헬퍼 메서드"""
        try:
            # 환경 변수나 AWS 프로필 사용
            return boto3.client(
                service_name,
                region_name=self.region
            )
        except ClientError as e:
            logger.error(f"Failed to create {service_name} client: {e}")
            raise
    
    @property
    def s3_client(self) -> boto3.client:
        """S3 클라이언트 반환 (싱글톤 패턴)"""
        if self._s3_client is None:
            self._s3_client = self._create_client('s3')
        return self._s3_client
    
    @property
    def dynamodb_client(self) -> boto3.client:
        """DynamoDB 클라이언트 반환 (싱글톤 패턴)"""
        if self._dynamodb_client is None:
            self._dynamodb_client = self._create_client('dynamodb')
        return self._dynamodb_client
    
    @property
    def bedrock_client(self) -> boto3.client:
        """Bedrock 클라이언트 반환 (싱글톤 패턴)"""
        if self._bedrock_client is None:
            self._bedrock_client = self._create_client('bedrock-runtime')
        return self._bedrock_client
    
    @property
    def sns_client(self) -> boto3.client:
        """SNS 클라이언트 반환 (싱글톤 패턴)"""
        if self._sns_client is None:
            self._sns_client = self._create_client('sns')
        return self._sns_client
    
    @property
    def lambda_client(self) -> boto3.client:
        """Lambda 클라이언트 반환 (싱글톤 패턴)"""
        if self._lambda_client is None:
            self._lambda_client = self._create_client('lambda')
        return self._lambda_client


class AWSResourceConfig:
    """AWS 리소스 설정 관리 클래스"""
    
    def __init__(self):
        """AWS 리소스 설정 초기화"""
        # S3 설정
        self.s3_image_bucket = os.getenv('S3_BUCKET_NAME', 'ai-diet-coach-images')
        self.s3_profile_bucket = os.getenv('S3_PROFILE_BUCKET', 'ai-diet-coach-profiles')
        
        # DynamoDB 테이블 설정
        self.diet_table = os.getenv('DYNAMODB_DIET_TABLE', 'diet_records')
        self.schedule_table = os.getenv('DYNAMODB_SCHEDULE_TABLE', 'schedule_records')
        self.user_table = os.getenv('DYNAMODB_USER_TABLE', 'user_profiles')
        
        # Bedrock 모델 설정 (us-east-1 리전용)
        self.bedrock_model_id = 'us.anthropic.claude-sonnet-4-20250514-v1:0'
        self.bedrock_image_model_id = 'us.anthropic.claude-sonnet-4-20250514-v1:0'
        
        # SNS 설정
        self.sns_topic_arn = os.getenv('SNS_TOPIC_ARN')


# 전역 인스턴스 (싱글톤)
aws_config = AWSConfig()
aws_resources = AWSResourceConfig()