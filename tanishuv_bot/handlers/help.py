# ==================== handlers/help.py ====================
from aiogram.types import CallbackQuery
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from texts.messages import *

router = Router()


@router.message(F.text == "ℹ️ Ma'lumot")
async def show_help(message: Message):
    """Yordam va ma'lumot"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Qoidalar", callback_data="help_rules")],
            [InlineKeyboardButton(text="❓ Savollar", callback_data="help_faq")],
            [InlineKeyboardButton(text="📞 Aloqa", url="https://t.me/admin_username")],
        ]
    )
    
    await message.answer(HELP_MESSAGE, reply_markup=keyboard)


@router.callback_query(F.data == "help_rules")
async def show_rules(callback: CallbackQuery):
    """Qoidalarni ko'rsatish"""
    await callback.answer()
    await callback.message.answer(CONFIRM_RULES_MESSAGE)


@router.callback_query(F.data == "help_faq")
async def show_faq(callback: CallbackQuery):
    """FAQ ko'rsatish"""
    await callback.answer()
    await callback.message.answer(HELP_MESSAGE)