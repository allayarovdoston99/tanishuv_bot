"""
Database modellari va typing lar

Bu fayl hozircha kerak emas (asyncpg to'g'ridan-to'g'ri SQL ishlatadi),
lekin kelajakda SQLAlchemy yoki boshqa ORM ga o'tish uchun tayyor.
"""

from typing import TypedDict, Optional, List
from datetime import datetime
from enum import Enum


# ==================== ENUMS ====================

class UserStatus(str, Enum):
    """Foydalanuvchi holati"""
    ACTIVE = "active"
    PAUSE = "pause"
    BANNED = "banned"


class UserMode(str, Enum):
    """Foydalanuvchi rejimi"""
    NIKOH = "nikoh"
    DOST = "dost"
    TALABA = "talaba"


class Gender(str, Enum):
    """Jins"""
    ERKAK = "erkak"
    AYOL = "ayol"


class LookingForGender(str, Enum):
    """Qidiruv jinsi"""
    ERKAK = "erkak"
    AYOL = "ayol"
    FARQI_YOQ = "farqi_yoq"


class ReportStatus(str, Enum):
    """Shikoyat holati"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    DISMISSED = "dismissed"


class TransactionStatus(str, Enum):
    """To'lov holati"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


# ==================== TYPE DICTS ====================

class UserDict(TypedDict):
    """User modeli"""
    id: int
    telegram_id: int
    username: Optional[str]
    full_name: str
    birth_year: int
    gender: str
    city: str
    bio: Optional[str]
    photo_file_id: Optional[str]
    photo_verified: bool
    mode: str
    status: str
    is_premium: bool
    premium_until: Optional[datetime]
    profile_views: int
    created_at: datetime
    last_active: datetime


class NikohProfileDict(TypedDict):
    """Nikoh profili"""
    user_id: int
    religion: Optional[str]
    occupation: Optional[str]
    education: Optional[str]
    marital_status: Optional[str]
    children: Optional[str]
    created_at: datetime


class DostProfileDict(TypedDict):
    """Do'st profili"""
    user_id: int
    interests: List[str]
    languages: List[str]
    created_at: datetime


class TalabaProfileDict(TypedDict):
    """Talaba profili"""
    user_id: int
    university: Optional[str]
    faculty: Optional[str]
    course: Optional[int]
    academic_interests: List[str]
    created_at: datetime


class SearchPreferencesDict(TypedDict):
    """Qidiruv parametrlari"""
    user_id: int
    looking_for_gender: str
    age_min: int
    age_max: int
    distance_km: Optional[int]
    created_at: datetime
    updated_at: datetime


class LikeDict(TypedDict):
    """Like"""
    id: int
    liker_id: int
    liked_id: int
    created_at: datetime


class MatchDict(TypedDict):
    """Match"""
    id: int
    user1_id: int
    user2_id: int
    created_at: datetime


class MessageDict(TypedDict):
    """Xabar"""
    id: int
    match_id: int
    sender_id: int
    receiver_id: int
    message_text: str
    created_at: datetime
    read_at: Optional[datetime]


class BlockDict(TypedDict):
    """Blok"""
    id: int
    blocker_id: int
    blocked_id: int
    created_at: datetime


class ReportDict(TypedDict):
    """Shikoyat"""
    id: int
    reporter_id: int
    reported_id: int
    reason: str
    details: Optional[str]
    status: str
    reviewed_by: Optional[int]
    created_at: datetime


class PremiumTransactionDict(TypedDict):
    """Premium to'lov"""
    id: int
    user_id: int
    package: str
    amount: int
    payment_provider: str
    payment_id: Optional[str]
    status: str
    created_at: datetime


class AdminActionDict(TypedDict):
    """Admin harakati"""
    id: int
    admin_id: int
    action: str
    target_user_id: Optional[int]
    details: Optional[str]
    created_at: datetime


# ==================== HELPER FUNCTIONS ====================

def user_to_dict(user_row) -> UserDict:
    """asyncpg Row ni UserDict ga aylantirish"""
    return dict(user_row) if user_row else None


def profile_to_dict(profile_row, profile_type: str) -> dict:
    """Profile ni dict ga aylantirish"""
    if not profile_row:
        return {}
    
    data = dict(profile_row)
    
    # List fieldlarni parse qilish (agar kerak bo'lsa)
    if profile_type == 'dost':
        # asyncpg avtomatik list qaytaradi
        pass
    elif profile_type == 'talaba':
        # academic_interests list bo'lishi kerak
        pass
    
    return data


# ==================== VALIDATION SCHEMAS ====================

class CreateUserSchema:
    """Yangi user yaratish uchun schema"""
    def __init__(
        self,
        telegram_id: int,
        username: Optional[str],
        full_name: str,
        birth_year: int,
        gender: str,
        city: str,
        mode: str
    ):
        self.telegram_id = telegram_id
        self.username = username
        self.full_name = full_name
        self.birth_year = birth_year
        self.gender = gender
        self.city = city
        self.mode = mode
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validatsiya"""
        if self.birth_year > 2006:
            return False, "Yoshingiz 18 dan kichik"
        
        if self.gender not in ['erkak', 'ayol']:
            return False, "Noto'g'ri jins"
        
        if self.mode not in ['nikoh', 'dost', 'talaba']:
            return False, "Noto'g'ri rejim"
        
        return True, None


class UpdateUserSchema:
    """User yangilash uchun schema"""
    def __init__(self, **kwargs):
        self.data = kwargs
    
    def get_valid_fields(self) -> dict:
        """Faqat ruxsat etilgan fieldlarni qaytarish"""
        allowed_fields = [
            'full_name', 'bio', 'photo_file_id', 'city',
            'status', 'is_premium', 'premium_until', 'profile_views'
        ]
        
        return {k: v for k, v in self.data.items() if k in allowed_fields}


# ==================== CONSTANTS ====================

class UserConstants:
    """User konstantalari"""
    MIN_NAME_LENGTH = 3
    MAX_NAME_LENGTH = 100
    MAX_BIO_LENGTH = 200
    MIN_AGE = 18
    MAX_AGE = 100
    
    # Kunlik limitlar
    FREE_DAILY_SWIPES = 10
    PREMIUM_DAILY_SWIPES = 50
    FREE_DAILY_MESSAGES = 50


class PremiumPackages:
    """Premium paketlar"""
    PREMIUM_MONTH = {
        'name': 'Premium',
        'price': 49000,
        'duration_days': 30,
        'features': [
            'Cheksiz swipe',
            'Kim yoqtirdi ko\'rish',
            'Super like',
            'Keng filtrlar'
        ]
    }
    
    VIP_MONTH = {
        'name': 'VIP',
        'price': 99000,
        'duration_days': 30,
        'features': [
            'Premium barcha imkoniyatlar',
            'Profilni ko\'tarish (boost)',
            'Maxfiy rejim',
            'Prioritet ko\'rsatish'
        ]
    }


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Bu faqat test uchun
    print("Models module loaded successfully")
    
    # Schema test
    schema = CreateUserSchema(
        telegram_id=123456789,
        username="test_user",
        full_name="Test User",
        birth_year=1995,
        gender="erkak",
        city="Toshkent",
        mode="nikoh"
    )
    
    is_valid, error = schema.validate()
    print(f"Valid: {is_valid}, Error: {error}")