# ==================== utils/filters.py ====================
from aiogram.filters import BaseFilter
from aiogram.types import Message
import config


class IsAdmin(BaseFilter):
    """Admin filtri"""
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in config.ADMIN_IDS


class IsPremium(BaseFilter):
    """Premium filtri"""
    async def __call__(self, message: Message) -> bool:
        from database import db
        user = await db.get_user_by_telegram_id(message.from_user.id)
        return user and user.get('is_premium', False)


class IsRegistered(BaseFilter):
    """Ro'yxatdan o'tgan filtri"""
    async def __call__(self, message: Message) -> bool:
        from database import db
        user = await db.get_user_by_telegram_id(message.from_user.id)
        return user is not None


class IsActive(BaseFilter):
    """Faol foydalanuvchi filtri"""
    async def __call__(self, message: Message) -> bool:
        from database import db
        user = await db.get_user_by_telegram_id(message.from_user.id)
        return user and user.get('status') == 'active'
