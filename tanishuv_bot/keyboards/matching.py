# ==================== keyboards/matching.py ====================
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_matching_keyboard() -> InlineKeyboardMarkup:
    """Moslik topish tugmalari"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="⛔ O'tkazish", callback_data="swipe_pass"),
                InlineKeyboardButton(text="❤️ Yoqdi", callback_data="swipe_like")
            ],
            [InlineKeyboardButton(text="⏸ To'xtatish", callback_data="matching_stop")]
        ]
    )
    return keyboard


def get_match_success_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Match bo'lganda"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💬 Suhbatni boshlash", callback_data=f"open_chat_{user_id}")],
            [InlineKeyboardButton(text="🔍 Davom etish", callback_data="continue_matching")]
        ]
    )
    return keyboard


def get_no_profiles_keyboard() -> InlineKeyboardMarkup:
    """Profillar tugaganda"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ Premiumga o'tish", callback_data="show_premium")],
            [InlineKeyboardButton(text="🏠 Bosh sahifa", callback_data="main_menu")]
        ]
    )
    return keyboard

