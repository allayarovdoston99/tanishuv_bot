# ==================== handlers/premium.py ====================
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta

from database import db
from texts.messages import *
import config

router = Router()


@router.message(F.text == "⭐ Premium")
async def show_premium(message: Message):
    """Premium ma'lumotlari"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz. /start ni bosing")
        return
    
    # Premium holati
    if user['is_premium']:
        until = user['premium_until'].strftime("%d.%m.%Y")
        status = f"✅ Faol ({until} gacha)"
    else:
        status = "❌ Faol emas"
    
    text = PREMIUM_INFO_MESSAGE.format(status=status)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Premium - 49,000 so'm", callback_data="buy_premium")],
            [InlineKeyboardButton(text="💎 VIP - 99,000 so'm", callback_data="buy_vip")],
        ]
    )
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("buy_"))
async def buy_premium_package(callback: CallbackQuery):
    """Premium sotib olish"""
    package = callback.data.split("_")[1]  # premium yoki vip
    
    amount = config.PREMIUM_PRICES.get(f"{package}_month", 0)
    
    # Bu yerda to'lov tizimini integratsiya qilish kerak
    # Hozircha oddiy tasdiqlash
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="💳 To'lash", callback_data=f"payment_{package}_{amount}")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_premium")],
        ]
    )
    
    await callback.message.edit_text(
        f"""
💎 {package.upper()} paket

Narx: {amount:,} so'm
Muddat: 30 kun

To'lov uchun tugmani bosing:
""",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("payment_"))
async def process_payment(callback: CallbackQuery):
    """To'lovni qayta ishlash (demo)"""
    parts = callback.data.split("_")
    package = parts[1]
    amount = int(parts[2])
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    # Premium aktivatsiya (demo)
    until = datetime.now() + timedelta(days=30)
    
    await db.update_user(
        user['id'],
        is_premium=True,
        premium_until=until
    )
    
    # Transaction saqlash
    # await db.create_premium_transaction(...)
    
    await callback.message.edit_text(
        PREMIUM_ACTIVATED_MESSAGE.format(until=until.strftime("%d.%m.%Y"))
    )


@router.callback_query(F.data == "back_to_premium")
async def back_to_premium(callback: CallbackQuery):
    """Premium sahifasiga qaytish"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("❌ Xatolik", show_alert=True)
        return
    
    # Premium holati
    if user['is_premium']:
        until = user['premium_until'].strftime("%d.%m.%Y")
        status = f"✅ Faol ({until} gacha)"
    else:
        status = "❌ Faol emas"
    
    text = PREMIUM_INFO_MESSAGE.format(status=status)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Premium - 49,000 so'm", callback_data="buy_premium")],
            [InlineKeyboardButton(text="💎 VIP - 99,000 so'm", callback_data="buy_vip")],
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)