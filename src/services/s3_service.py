"""
S3 서비스 모듈
이미지 업로드, 다운로드, 관리 기능
"""

import os
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError
from PIL import Image
import io

from ..config.aws_config import aws_config, aws_resources
from ..utils.logger import setup_logger
from ..utils.helpers import generate_unique_id, sanitize_filename

logger = setup_logger(__name__)


class S3Service:
    """S3 서비스 관리 클래스"""
    
    def __init__(self):
        """S3 서비스 초기화"""
        self.client = aws_config.s3_client
        self.image_bucket = aws_resources.s3_image_bucket
        self.profile_bucket = aws_resources.s3_profile_bucket
    
    async def upload_image(
        self,
        image_data: bytes,
        user_id: str,
        filename: str,
        meal_id: Optional[str] = None
    ) -> Optional[str]:
        """
        이미지 업로드
        
        Args:
            image_data: 이미지 바이트 데이터
            user_id: 사용자 ID
            filename: 원본 파일명
            meal_id: 식사 ID (선택사항)
        
        Returns:
            업로드된 이미지의 S3 URL
        """
        try:
            # 파일명 정리 및 고유 키 생성
            clean_filename = sanitize_filename(filename)
            file_extension = os.path.splitext(clean_filename)[1].lower()
            
            if meal_id:
                s3_key = f"meals/{user_id}/{meal_id}/{generate_unique_id()}{file_extension}"
            else:
                s3_key = f"images/{user_id}/{generate_unique_id()}{file_extension}"
            
            # 이미지 최적화
            optimized_image = await self._optimize_image(image_data)
            
            # S3 업로드
            self.client.put_object(
                Bucket=self.image_bucket,
                Key=s3_key,
                Body=optimized_image,
                ContentType=self._get_content_type(file_extension),
                Metadata={
                    'user_id': user_id,
                    'original_filename': clean_filename,
                    'meal_id': meal_id or ''
                }
            )
            
            # URL 생성
            s3_url = f"https://{self.image_bucket}.s3.{aws_config.region}.amazonaws.com/{s3_key}"
            
            logger.info(f"Image uploaded successfully: {s3_url}")
            return s3_url
            
        except ClientError as e:
            logger.error(f"Failed to upload image: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during image upload: {e}")
            return None
    
    async def download_image(self, s3_url: str) -> Optional[bytes]:
        """
        이미지 다운로드
        
        Args:
            s3_url: S3 이미지 URL
        
        Returns:
            이미지 바이트 데이터
        """
        try:
            # URL에서 키 추출
            s3_key = self._extract_key_from_url(s3_url)
            if not s3_key:
                logger.error(f"Invalid S3 URL: {s3_url}")
                return None
            
            # S3에서 객체 다운로드
            response = self.client.get_object(
                Bucket=self.image_bucket,
                Key=s3_key
            )
            
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"Failed to download image: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during image download: {e}")
            return None
    
    async def delete_image(self, s3_url: str) -> bool:
        """
        이미지 삭제
        
        Args:
            s3_url: 삭제할 이미지의 S3 URL
        
        Returns:
            삭제 성공 여부
        """
        try:
            s3_key = self._extract_key_from_url(s3_url)
            if not s3_key:
                logger.error(f"Invalid S3 URL: {s3_url}")
                return False
            
            self.client.delete_object(
                Bucket=self.image_bucket,
                Key=s3_key
            )
            
            logger.info(f"Image deleted successfully: {s3_url}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete image: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during image deletion: {e}")
            return False
    
    async def upload_user_profile(
        self,
        user_id: str,
        profile_data: Dict[str, Any]
    ) -> Optional[str]:
        """
        사용자 프로필 데이터 업로드
        
        Args:
            user_id: 사용자 ID
            profile_data: 프로필 데이터
        
        Returns:
            업로드된 프로필의 S3 URL
        """
        try:
            import json
            
            s3_key = f"profiles/{user_id}/profile.json"
            
            self.client.put_object(
                Bucket=self.profile_bucket,
                Key=s3_key,
                Body=json.dumps(profile_data, ensure_ascii=False, indent=2),
                ContentType='application/json',
                Metadata={'user_id': user_id}
            )
            
            s3_url = f"https://{self.profile_bucket}.s3.{aws_config.region}.amazonaws.com/{s3_key}"
            
            logger.info(f"Profile uploaded successfully: {s3_url}")
            return s3_url
            
        except Exception as e:
            logger.error(f"Failed to upload profile: {e}")
            return None
    
    async def _optimize_image(self, image_data: bytes) -> bytes:
        """
        이미지 최적화 (크기 조정 및 압축)
        
        Args:
            image_data: 원본 이미지 데이터
        
        Returns:
            최적화된 이미지 데이터
        """
        try:
            # PIL로 이미지 열기
            image = Image.open(io.BytesIO(image_data))
            
            # RGBA를 RGB로 변환 (JPEG 호환성)
            if image.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            
            # 크기 조정 (최대 1920x1080)
            max_size = (1920, 1080)
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # 최적화된 이미지를 바이트로 변환
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85, optimize=True)
            
            return output.getvalue()
            
        except Exception as e:
            logger.warning(f"Image optimization failed, using original: {e}")
            return image_data
    
    def _get_content_type(self, file_extension: str) -> str:
        """
        파일 확장자에 따른 Content-Type 반환
        
        Args:
            file_extension: 파일 확장자
        
        Returns:
            Content-Type
        """
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        
        return content_types.get(file_extension.lower(), 'application/octet-stream')
    
    def _extract_key_from_url(self, s3_url: str) -> Optional[str]:
        """
        S3 URL에서 키 추출
        
        Args:
            s3_url: S3 URL
        
        Returns:
            추출된 S3 키
        """
        try:
            # URL 파싱하여 키 추출
            if f"{self.image_bucket}.s3." in s3_url:
                return s3_url.split(f"{self.image_bucket}.s3.{aws_config.region}.amazonaws.com/")[1]
            elif f"{self.profile_bucket}.s3." in s3_url:
                return s3_url.split(f"{self.profile_bucket}.s3.{aws_config.region}.amazonaws.com/")[1]
            else:
                return None
        except IndexError:
            return None
    
    async def list_user_images(self, user_id: str) -> list[str]:
        """
        사용자의 모든 이미지 목록 조회
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            이미지 URL 목록
        """
        try:
            prefix = f"meals/{user_id}/"
            
            response = self.client.list_objects_v2(
                Bucket=self.image_bucket,
                Prefix=prefix
            )
            
            urls = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    url = f"https://{self.image_bucket}.s3.{aws_config.region}.amazonaws.com/{obj['Key']}"
                    urls.append(url)
            
            return urls
            
        except ClientError as e:
            logger.error(f"Failed to list user images: {e}")
            return []


# 전역 인스턴스
s3_service = S3Service()