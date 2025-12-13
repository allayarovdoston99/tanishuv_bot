# ==================== utils/validators.py ====================
import re
from typing import Tuple


def validate_name(name: str) -> Tuple[bool, str]:
    """Ismni tekshirish"""
    if len(name) < 3:
        return False, "Ism juda qisqa (kamida 3 ta belgi)"
    
    if len(name) > 100:
        return False, "Ism juda uzun (maksimum 100 ta belgi)"
    
    # Faqat harflar va bo'sh joylar
    if not re.match(r"^[a-zA-Zа-яА-ЯёЁўҲғҚқҒ\s'-]+$", name):
        return False, "Ismda faqat harflar bo'lishi kerak"
    
    return True, ""


def validate_birth_year(year: int) -> Tuple[bool, str]:
    """Tug'ilgan yilni tekshirish"""
    current_year = 2024
    age = current_year - year
    
    if age < 18:
        return False, "Yoshingiz 18 dan kichik"
    
    if year < 1920 or year > 2006:
        return False, "Noto'g'ri yil kiritildi"
    
    return True, ""


def validate_bio(bio: str) -> Tuple[bool, str]:
    """Bio tekshirish"""
    if len(bio) > 200:
        return False, "Bio 200 belgidan oshmasligi kerak"
    
    # Taqiqlangan so'zlar
    forbidden_words = ['spam', 'reklama', 'pul', 'dollar']
    bio_lower = bio.lower()
    
    for word in forbidden_words:
        if word in bio_lower:
            return False, f"Bio da '{word}' so'zi taqiqlangan"
    
    return True, ""


def validate_phone(phone: str) -> Tuple[bool, str]:
    """Telefon raqamni tekshirish"""
    # O'zbekiston telefon raqami formati: +998XXXXXXXXX
    pattern = r'^\+998\d{9}$'
    
    if not re.match(pattern, phone):
        return False, "Noto'g'ri telefon raqam formati. Misol: +998901234567"
    
    return True, ""


def validate_age_range(age_min: int, age_max: int) -> Tuple[bool, str]:
    """Yosh oralig'ini tekshirish"""
    if age_min < 18:
        return False, "Minimal yosh 18 dan kichik bo'lmasligi kerak"
    
    if age_max > 100:
        return False, "Maksimal yosh 100 dan oshmasligi kerak"
    
    if age_min > age_max:
        return False, "Minimal yosh maksimal yoshdan katta bo'lmasligi kerak"
    
    return True, ""
