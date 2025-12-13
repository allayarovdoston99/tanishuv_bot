from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import logging

import config
from database import db
from states import ChatStates

router = Router()
logger = logging.getLogger(__name__)


# ============ VOICE XABAR YUBORISH ============

@router.message(ChatStates.in_chat, F.voice)
async def handle_voice_in_chat(message: Message, state: FSMContext):
    """Suhbatda ovozli xabar yuborish"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting: /start")
        return
    
    # Current chat ma'lumotlarini olish
    data = await state.get_data()
    match_id = data.get('current_match_id')
    partner_id = data.get('partner_id')
    
    if not match_id or not partner_id:
        await message.answer("❌ Suhbat topilmadi")
        return
    
    # Partner ma'lumotlarini olish
    partner = await db.get_user_by_id(partner_id)
    
    if not partner:
        await message.answer("❌ Foydalanuvchi topilmadi")
        return
    
    # Bloklangan tekshirish
    if await db.is_blocked(user['id'], partner_id):
        await message.answer("❌ Bu foydalanuvchi bilan aloqa o'rnatib bo'lmaydi")
        return
    
    # Premium tekshirish (Voice faqat premium'da)
    if not user['is_premium'] and not config.FEATURES.get('voice_messages_enabled', True):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💎 Premium Olish", callback_data="buy_premium")]
        ])
        await message.answer(
            "🎤 <b>Ovozli xabar - Premium funksiya</b>\n\n"
            "Ovozli xabar yuborish uchun Premium obuna kerak!",
            reply_markup=keyboard
        )
        return
    
    # Xabarni saqlash
    try:
        msg_id = await db.send_message(
            match_id=match_id,
            sender_id=user['id'],
            receiver_id=partner_id,
            message_type='voice',
            file_id=message.voice.file_id
        )
        
        # Partner'ga yuborish
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 Javob berish", callback_data=f"open_chat_{user['id']}")]
            ])
            
            await message.bot.send_voice(
                chat_id=partner['telegram_id'],
                voice=message.voice.file_id,
                caption=f"🎤 {user['full_name']} sizga ovozli xabar yubordi",
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Partner'ga voice yuborishda xato: {e}")
        
        # Tasdiqlash
        await message.answer("✅ Ovozli xabar yuborildi")
        
        logger.info(f"Voice xabar: {user['id']} -> {partner_id}")
        
    except Exception as e:
        logger.error(f"Voice xabar yuborishda xato: {e}")
        await message.answer("❌ Xatolik yuz berdi")


# ============ VOICE XABAR QABUL QILISH ============

@router.message(F.voice)
async def handle_voice_outside_chat(message: Message):
    """Suhbatdan tashqari voice xabar"""
    await message.answer(
        "🎤 <b>Ovozli xabar</b>\n\n"
        "Ovozli xabar yuborish uchun avval biror kishi bilan match bo'ling!\n\n"
        "👉 /matching - Moslik topish"
    )


# ============ VOICE SOZLAMALARI ============

async def check_voice_permission(user_id: int) -> tuple[bool, str]:
    """
    Voice xabar yuborish ruxsatini tekshirish
    Returns: (ruxsat bor/yo'q, xabar)
    """
    user = await db.get_user_by_id(user_id)
    
    if not user:
        return False, "Foydalanuvchi topilmadi"
    
    # Feature flag tekshirish
    if not config.FEATURES.get('voice_messages_enabled', True):
        return False, "Ovozli xabarlar vaqtincha o'chirilgan"
    
    # Premium tekshirish (agar kerak bo'lsa)
    # if not user['is_premium']:
    #     return False, "Ovozli xabar - Premium funksiya"
    
    # Banned tekshirish
    if user['status'] == 'banned':
        return False, "Sizning hisobingiz bloklangan"
    
    return True, "OK"


# ============ VOICE XABAR STATISTIKASI ============

async def get_voice_stats(user_id: int) -> dict:
    """Voice xabar statistikasi"""
    async with db.pool.acquire() as conn:
        # Yuborilgan voice xabarlar
        sent_count = await conn.fetchval("""
            SELECT COUNT(*) FROM messages
            WHERE sender_id = $1 AND message_type = 'voice'
        """, user_id)
        
        # Qabul qilingan voice xabarlar
        received_count = await conn.fetchval("""
            SELECT COUNT(*) FROM messages
            WHERE receiver_id = $1 AND message_type = 'voice'
        """, user_id)
        
        return {
            'sent': sent_count or 0,
            'received': received_count or 0,
            'total': (sent_count or 0) + (received_count or 0)
        }


# ============ CALLBACK HANDLERLAR ============

@router.callback_query(F.data == "voice_info")
async def voice_info(callback: CallbackQuery):
    """Voice xabar haqida ma'lumot"""
    text = (
        "🎤 <b>Ovozli Xabarlar</b>\n\n"
        "Ovozli xabar yuborish imkoniyati match bo'lgan odamlar bilan.\n\n"
        "<b>Qanday ishlaydi?</b>\n"
        "1️⃣ Biror kishi bilan match bo'ling\n"
        "2️⃣ Suhbatni oching\n"
        "3️⃣ Mikrofon tugmasini bosib ovoz yozib yuboring\n\n"
        "<b>Afzalliklari:</b>\n"
        "✅ Tezroq muloqot\n"
        "✅ Ovozingizni eshitadi\n"
        "✅ Yozishdan oson\n\n"
    )
    
    if config.FEATURES.get('voice_messages_enabled'):
        text += "✅ <b>Funksiya faol</b>"
    else:
        text += "⏸ <b>Vaqtincha o'chirilgan</b>"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="help_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "voice_settings")
async def voice_settings(callback: CallbackQuery):
    """Voice sozlamalari"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    # Foydalanuvchi statistikasi
    stats = await get_voice_stats(user['id'])
    
    text = (
        f"🎤 <b>Ovozli Xabar Sozlamalari</b>\n\n"
        f"📊 <b>Statistika:</b>\n"
        f"• Yuborilgan: {stats['sent']} ta\n"
        f"• Qabul qilingan: {stats['received']} ta\n"
        f"• Jami: {stats['total']} ta\n\n"
        f"🎯 <b>Holat:</b> {'Faol ✅' if config.FEATURES.get('voice_messages_enabled') else 'O\'chirilgan ❌'}\n"
    )
    
    if not user['is_premium']:
        text += "\n💎 Premium obuna bilan cheklovsiz ovozli xabarlar!"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Batafsil statistika", callback_data="voice_stats_detail")],
        [InlineKeyboardButton(text="💎 Premium", callback_data="buy_premium")] if not user['is_premium'] else [],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="settings_main")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "voice_stats_detail")
async def voice_stats_detail(callback: CallbackQuery):
    """Batafsil voice statistika"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    async with db.pool.acquire() as conn:
        # Oxirgi 7 kun statistikasi
        recent_stats = await conn.fetch("""
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as count
            FROM messages
            WHERE (sender_id = $1 OR receiver_id = $1)
            AND message_type = 'voice'
            AND created_at > CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, user['id'])
        
        # Eng ko'p voice xabar yuborilgan shaxs
        top_partner = await conn.fetchrow("""
            SELECT 
                u.full_name,
                COUNT(*) as count
            FROM messages m
            JOIN users u ON (
                CASE 
                    WHEN m.sender_id = $1 THEN u.id = m.receiver_id
                    ELSE u.id = m.sender_id
                END
            )
            WHERE (m.sender_id = $1 OR m.receiver_id = $1)
            AND m.message_type = 'voice'
            GROUP BY u.id, u.full_name
            ORDER BY count DESC
            LIMIT 1
        """, user['id'])
    
    text = "📊 <b>Batafsil Voice Statistika</b>\n\n"
    
    if recent_stats:
        text += "<b>Oxirgi 7 kun:</b>\n"
        for stat in recent_stats:
            text += f"• {stat['date'].strftime('%d.%m')}: {stat['count']} ta\n"
    else:
        text += "📊 Oxirgi 7 kunda voice xabar yo'q\n"
    
    if top_partner:
        text += f"\n👤 <b>Eng ko'p:</b> {top_partner['full_name']} ({top_partner['count']} ta)"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="voice_settings")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()