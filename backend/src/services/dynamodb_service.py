"""
DynamoDB 서비스 모듈
사용자 데이터, 식사 기록, 스케줄 관리
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from botocore.exceptions import ClientError

from ..config.aws_config import aws_config, aws_resources
from ..models.data_models import UserProfile, MealRecord, ScheduleEvent, CoachingMessage
from ..utils.logger import setup_logger
from ..utils.helpers import format_datetime

logger = setup_logger(__name__)


class DynamoDBService:
    """DynamoDB 서비스 관리 클래스"""
    
    def __init__(self):
        """DynamoDB 서비스 초기화"""
        self.client = aws_config.dynamodb_client
        self.diet_table = aws_resources.diet_table
        self.schedule_table = aws_resources.schedule_table
        self.user_table = aws_resources.user_table
    
    # 사용자 프로필 관리
    async def save_user_profile(self, user_profile: UserProfile) -> bool:
        """
        사용자 프로필 저장
        
        Args:
            user_profile: 사용자 프로필 객체
        
        Returns:
            저장 성공 여부
        """
        try:
            item = {
                'user_id': {'S': user_profile.user_id},
                'name': {'S': user_profile.name},
                'age': {'N': str(user_profile.age)},
                'gender': {'S': user_profile.gender},
                'height': {'N': str(user_profile.height)},
                'weight': {'N': str(user_profile.weight)},
                'health_goal': {'S': user_profile.health_goal.value},
                'preferred_exercises': {'SS': [ex.value for ex in user_profile.preferred_exercises]} if user_profile.preferred_exercises else {'SS': ['none']},
                'disliked_exercises': {'SS': [ex.value for ex in user_profile.disliked_exercises]} if user_profile.disliked_exercises else {'SS': ['none']},
                'activity_level': {'S': user_profile.activity_level},
                'dietary_restrictions': {'SS': user_profile.dietary_restrictions} if user_profile.dietary_restrictions else {'SS': ['none']},
                'target_calories': {'N': str(user_profile.target_calories)} if user_profile.target_calories else {'NULL': True},
                'created_at': {'S': format_datetime(user_profile.created_at)},
                'updated_at': {'S': format_datetime(user_profile.updated_at)}
            }
            
            self.client.put_item(
                TableName=self.user_table,
                Item=item
            )
            
            logger.info(f"User profile saved: {user_profile.user_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to save user profile: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving user profile: {e}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """
        사용자 프로필 조회
        
        Args:
            user_id: 사용자 ID
        
        Returns:
            사용자 프로필 객체 또는 None
        """
        try:
            # 빈 문자열 검사
            if not user_id or user_id.strip() == "":
                logger.error(f"Invalid user_id: empty string")
                return None
                
            response = self.client.get_item(
                TableName=self.user_table,
                Key={'user_id': {'S': user_id.strip()}}
            )
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            
            # DynamoDB 아이템을 UserProfile 객체로 변환
            user_profile = self._dynamodb_item_to_user_profile(item)
            
            logger.info(f"User profile retrieved: {user_id}")
            return user_profile
            
        except ClientError as e:
            logger.error(f"Failed to get user profile: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user profile: {e}")
            return None
    
    # 식사 기록 관리
    async def save_meal_record(self, meal_record: MealRecord) -> bool:
        """
        식사 기록 저장
        
        Args:
            meal_record: 식사 기록 객체
        
        Returns:
            저장 성공 여부
        """
        try:
            item = {
                'user_id': {'S': meal_record.user_id},
                'meal_id': {'S': meal_record.meal_id},
                'timestamp': {'S': format_datetime(meal_record.timestamp)},
                'meal_type': {'S': meal_record.meal_type},
                'image_url': {'S': meal_record.image_url} if meal_record.image_url else {'NULL': True},
                'foods': {'S': json.dumps([food.dict() for food in meal_record.foods], ensure_ascii=False)},
                'total_nutrition': {'S': json.dumps(meal_record.total_nutrition.dict(), ensure_ascii=False)},
                'people_count': {'N': str(meal_record.people_count)},
                'notes': {'S': meal_record.notes} if meal_record.notes else {'NULL': True}
            }
            
            self.client.put_item(
                TableName=self.diet_table,
                Item=item
            )
            
            logger.info(f"Meal record saved: {meal_record.meal_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to save meal record: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving meal record: {e}")
            return False
    
    async def get_user_meals(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[MealRecord]:
        """
        사용자 식사 기록 조회
        
        Args:
            user_id: 사용자 ID
            start_date: 시작 날짜
            end_date: 종료 날짜
            limit: 최대 조회 개수
        
        Returns:
            식사 기록 리스트
        """
        try:
            # 쿼리 조건 구성
            key_condition = 'user_id = :user_id'
            expression_values = {':user_id': {'S': user_id}}
            
            if start_date and end_date:
                key_condition += ' AND #ts BETWEEN :start_date AND :end_date'
                expression_values.update({
                    ':start_date': {'S': format_datetime(start_date)},
                    ':end_date': {'S': format_datetime(end_date)}
                })
            
            if start_date and end_date:
                response = self.client.scan(
                    TableName=self.diet_table,
                    FilterExpression='user_id = :user_id AND #ts BETWEEN :start_date AND :end_date',
                    ExpressionAttributeValues={
                        ':user_id': {'S': user_id},
                        ':start_date': {'S': format_datetime(start_date)},
                        ':end_date': {'S': format_datetime(end_date)}
                    },
                    ExpressionAttributeNames={'#ts': 'timestamp'},
                    Limit=limit
                )
            else:
                response = self.client.scan(
                    TableName=self.diet_table,
                    FilterExpression='user_id = :user_id',
                    ExpressionAttributeValues={':user_id': {'S': user_id}},
                    Limit=limit
                )
            
            meals = []
            for item in response.get('Items', []):
                meal = self._dynamodb_item_to_meal_record(item)
                if meal:
                    meals.append(meal)
            
            logger.info(f"Retrieved {len(meals)} meals for user: {user_id}")
            return meals
            
        except ClientError as e:
            logger.error(f"Failed to get user meals: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting user meals: {e}")
            return []
    
    async def get_daily_nutrition_summary(
        self,
        user_id: str,
        date: datetime
    ) -> Dict[str, Any]:
        """
        일일 영양소 섭취 요약
        
        Args:
            user_id: 사용자 ID
            date: 조회할 날짜
        
        Returns:
            영양소 요약 정보
        """
        try:
            # 해당 날짜의 식사 기록 조회
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1) - timedelta(microseconds=1)
            
            meals = await self.get_user_meals(user_id, start_date, end_date)
            
            # 영양소 합계 계산
            total_calories = sum(meal.total_nutrition.calories for meal in meals)
            total_carbs = sum(meal.total_nutrition.carbohydrates for meal in meals)
            total_protein = sum(meal.total_nutrition.protein for meal in meals)
            total_fat = sum(meal.total_nutrition.fat for meal in meals)
            
            summary = {
                'date': format_datetime(date, '%Y-%m-%d'),
                'meal_count': len(meals),
                'total_nutrition': {
                    'calories': total_calories,
                    'carbohydrates': total_carbs,
                    'protein': total_protein,
                    'fat': total_fat
                },
                'meals_by_type': {}
            }
            
            # 식사 종류별 분류
            for meal in meals:
                meal_type = meal.meal_type
                if meal_type not in summary['meals_by_type']:
                    summary['meals_by_type'][meal_type] = []
                summary['meals_by_type'][meal_type].append({
                    'meal_id': meal.meal_id,
                    'timestamp': format_datetime(meal.timestamp),
                    'calories': meal.total_nutrition.calories
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get daily nutrition summary: {e}")
            return {}
    
    # 스케줄 관리
    async def save_schedule_event(self, event: ScheduleEvent) -> bool:
        """
        스케줄 이벤트 저장
        
        Args:
            event: 스케줄 이벤트 객체
        
        Returns:
            저장 성공 여부
        """
        try:
            item = {
                'event_id': {'S': event.event_id},
                'user_id': {'S': event.user_id},
                'title': {'S': event.title},
                'event_type': {'S': event.event_type},
                'start_time': {'S': format_datetime(event.start_time)},
                'end_time': {'S': format_datetime(event.end_time)} if event.end_time else {'NULL': True},
                'location': {'S': event.location} if event.location else {'NULL': True},
                'participants': {'N': str(event.participants)} if event.participants else {'NULL': True},
                'notes': {'S': event.notes} if event.notes else {'NULL': True},
                'is_processed': {'BOOL': event.is_processed}
            }
            
            self.client.put_item(
                TableName=self.schedule_table,
                Item=item
            )
            
            logger.info(f"Schedule event saved: {event.event_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to save schedule event: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error saving schedule event: {e}")
            return False
    
    async def get_upcoming_events(
        self,
        user_id: str,
        days_ahead: int = 7
    ) -> List[ScheduleEvent]:
        """
        예정된 이벤트 조회
        
        Args:
            user_id: 사용자 ID
            days_ahead: 조회할 일수
        
        Returns:
            예정된 이벤트 리스트
        """
        try:
            end_date = datetime.now() + timedelta(days=days_ahead)
            
            response = self.client.query(
                TableName=self.schedule_table,
                IndexName='user_id-start_time-index',  # GSI 필요
                KeyConditionExpression='user_id = :user_id AND start_time BETWEEN :now AND :end_date',
                ExpressionAttributeValues={
                    ':user_id': {'S': user_id},
                    ':now': {'S': format_datetime(datetime.now())},
                    ':end_date': {'S': format_datetime(end_date)}
                }
            )
            
            events = []
            for item in response.get('Items', []):
                event = self._dynamodb_item_to_schedule_event(item)
                if event:
                    events.append(event)
            
            logger.info(f"Retrieved {len(events)} upcoming events for user: {user_id}")
            return events
            
        except ClientError as e:
            logger.error(f"Failed to get upcoming events: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting upcoming events: {e}")
            return []
    
    # 헬퍼 메서드들
    def _dynamodb_item_to_user_profile(self, item: Dict[str, Any]) -> UserProfile:
        """DynamoDB 아이템을 UserProfile 객체로 변환"""
        from ..models.data_models import HealthGoal, ExerciseType
        
        return UserProfile(
            user_id=item['user_id']['S'],
            name=item['name']['S'],
            age=int(item['age']['N']),
            gender=item['gender']['S'],
            height=float(item['height']['N']),
            weight=float(item['weight']['N']),
            health_goal=HealthGoal(item['health_goal']['S']),
            preferred_exercises=[ExerciseType(ex) for ex in item['preferred_exercises']['SS'] if ex != 'none'],
            disliked_exercises=[ExerciseType(ex) for ex in item['disliked_exercises']['SS'] if ex != 'none'] if 'disliked_exercises' in item else [],
            activity_level=item['activity_level']['S'],
            dietary_restrictions=[dr for dr in item['dietary_restrictions']['SS'] if dr != 'none'] if 'dietary_restrictions' in item else [],
            target_calories=float(item['target_calories']['N']) if 'target_calories' in item and 'N' in item['target_calories'] else None,
            created_at=datetime.fromisoformat(item['created_at']['S']),
            updated_at=datetime.fromisoformat(item['updated_at']['S'])
        )
    
    def _dynamodb_item_to_meal_record(self, item: Dict[str, Any]) -> Optional[MealRecord]:
        """DynamoDB 아이템을 MealRecord 객체로 변환"""
        try:
            from ..models.data_models import FoodItem, NutritionInfo
            
            foods_data = json.loads(item['foods']['S'])
            foods = [FoodItem(**food_data) for food_data in foods_data]
            
            nutrition_data = json.loads(item['total_nutrition']['S'])
            total_nutrition = NutritionInfo(**nutrition_data)
            
            return MealRecord(
                user_id=item['user_id']['S'],
                meal_id=item['meal_id']['S'],
                timestamp=datetime.fromisoformat(item['timestamp']['S']),
                meal_type=item['meal_type']['S'],
                image_url=item['image_url']['S'] if 'image_url' in item and 'S' in item['image_url'] else None,
                foods=foods,
                total_nutrition=total_nutrition,
                people_count=int(item['people_count']['N']),
                notes=item['notes']['S'] if 'notes' in item and 'S' in item['notes'] else None
            )
            
        except Exception as e:
            logger.error(f"Failed to convert DynamoDB item to MealRecord: {e}")
            return None
    
    def _dynamodb_item_to_schedule_event(self, item: Dict[str, Any]) -> Optional[ScheduleEvent]:
        """DynamoDB 아이템을 ScheduleEvent 객체로 변환"""
        try:
            return ScheduleEvent(
                event_id=item['event_id']['S'],
                user_id=item['user_id']['S'],
                title=item['title']['S'],
                event_type=item['event_type']['S'],
                start_time=datetime.fromisoformat(item['start_time']['S']),
                end_time=datetime.fromisoformat(item['end_time']['S']) if 'end_time' in item and 'S' in item['end_time'] else None,
                location=item['location']['S'] if 'location' in item and 'S' in item['location'] else None,
                participants=int(item['participants']['N']) if 'participants' in item and 'N' in item['participants'] else None,
                notes=item['notes']['S'] if 'notes' in item and 'S' in item['notes'] else None,
                is_processed=item['is_processed']['BOOL']
            )
            
        except Exception as e:
            logger.error(f"Failed to convert DynamoDB item to ScheduleEvent: {e}")
            return None


# 전역 인스턴스
dynamodb_service = DynamoDBService()