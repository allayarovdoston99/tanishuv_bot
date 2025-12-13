# ==================== utils/helpers.py ====================
from datetime import datetime
from typing import Optional


def calculate_age(birth_year: int) -> int:
    """Yoshni hisoblash"""
    current_year = datetime.now().year
    return current_year - birth_year


def format_datetime(dt: Optional[datetime]) -> str:
    """Sana va vaqtni formatlash"""
    if not dt:
        return "Noma'lum"
    
    return dt.strftime("%d.%m.%Y %H:%M")


def format_date(dt: Optional[datetime]) -> str:
    """Sanani formatlash"""
    if not dt:
        return "Noma'lum"
    
    return dt.strftime("%d.%m.%Y")


def truncate_text(text: str, max_length: int = 100) -> str:
    """Matnni qisqartirish"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."


def format_number(number: int) -> str:
    """Raqamni formatlash (1000 -> 1,000)"""
    return f"{number:,}"


def get_gender_emoji(gender: str) -> str:
    """Jins emoji"""
    return "👨" if gender == "erkak" else "👩"


def get_mode_emoji(mode: str) -> str:
    """Rejim emoji"""
    emojis = {
        'nikoh': '🕌',
        'dost': '👥',
        'talaba': '🎓'
    }
    return emojis.get(mode, '❓')


def is_premium_active(user: dict) -> bool:
    """Premium faolligini tekshirish"""
    if not user.get('is_premium'):
        return False
    
    premium_until = user.get('premium_until')
    if not premium_until:
        return False
    
    return datetime.now() < premium_until


def format_distance(distance_km: Optional[int]) -> str:
    """Masofani formatlash"""
    if distance_km is None:
        return "Cheklanmagan"
    
    return f"{distance_km} km"


def mask_username(username: Optional[str]) -> str:
    """Username ni maskalash (xavfsizlik uchun)"""
    if not username:
        return "username_yoq"
    
    if len(username) <= 3:
        return username
    
    return username[:3] + "*" * (len(username) - 3)
