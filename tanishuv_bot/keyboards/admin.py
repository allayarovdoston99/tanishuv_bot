# ==================== keyboards/admin.py ====================
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin panel"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
            [InlineKeyboardButton(text="👥 Foydalanuvchilar", callback_data="admin_users")],
            [InlineKeyboardButton(text="⚠️ Shikoyatlar", callback_data="admin_reports")],
            [InlineKeyboardButton(text="📢 Umumiy xabar", callback_data="admin_broadcast")],
        ]
    )
    return keyboard


def get_report_actions_keyboard(report_id: int, user_id: int) -> InlineKeyboardMarkup:
    """Shikoyat uchun amallar"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Ban (7 kun)", callback_data=f"ban_{user_id}_7")],
            [InlineKeyboardButton(text="🚫 Ban (doimiy)", callback_data=f"ban_{user_id}_permanent")],
            [InlineKeyboardButton(text="⚠️ Ogohlantirish", callback_data=f"warn_{user_id}")],
            [InlineKeyboardButton(text="❌ Rad etish", callback_data=f"dismiss_report_{report_id}")],
        ]
    )
    return keyboard