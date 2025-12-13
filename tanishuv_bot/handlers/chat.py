from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database import db
from states import ChatStates
from texts.messages import *
from datetime import datetime

router = Router()


@router.message(F.text == "💬 Suhbatlar")
async def show_chats(message: Message):
    """Suhbatlar ro'yxati"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz. /start ni bosing")
        return
    
    # Matchlarni olish
    matches = await db.get_user_matches(user['id'])
    
    if not matches:
        await message.answer(NO_CHATS_MESSAGE)
        return
    
    text = "💬 SIZNING SUHBATLARINGIZ\n\n"
    current_year = datetime.now().year
    
    keyboard_buttons = []
    for match in matches:
        age = current_year - match['birth_year']
        text += f"• {match['full_name']}, {age} - {match['city']}\n"
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"💬 {match['full_name']}",
                callback_data=f"openchat_{match['match_id']}_{match['id']}"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("openchat_"))
async def open_chat_window(callback: CallbackQuery, state: FSMContext):
    """Suhbat oynasini ochish"""
    parts = callback.data.split("_")
    match_id = int(parts[1])
    partner_id = int(parts[2])
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    partner = await db.get_user_profile_data(partner_id)
    
    # Oxirgi xabarlarni olish
    messages = await db.get_chat_messages(match_id, limit=20)
    
    text = f"💬 {partner['full_name']} bilan suhbat\n"
    text += "─" * 30 + "\n\n"
    
    if messages:
        for msg in messages[-10:]:  # Oxirgi 10 ta
            sender = "Siz" if msg['sender_id'] == user['id'] else partner['full_name']
            text += f"{sender}: {msg['message_text']}\n\n"
    else:
        text += "Hali xabarlar yo'q. Birinchi bo'lib yozing!\n\n"
    
    text += "─" * 30 + "\n"
    text += "Xabar yozing yoki amal tanlang:"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👤 Profilni ko'rish", callback_data=f"viewprofile_{partner_id}")],
            [InlineKeyboardButton(text="🚫 Bloklash", callback_data=f"block_{partner_id}")],
            [InlineKeyboardButton(text="⚠️ Shikoyat", callback_data=f"report_{partner_id}")],
            [InlineKeyboardButton(text="◀️ Suhbatlarga qaytish", callback_data="back_to_chats")],
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    
    # State ga match_id va partner_id saqlash
    await state.update_data(match_id=match_id, partner_id=partner_id)
    await state.set_state(ChatStates.in_chat)


@router.message(ChatStates.in_chat)
async def send_chat_message(message: Message, state: FSMContext):
    """Suhbatda xabar yuborish"""
    data = await state.get_data()
    match_id = data.get('match_id')
    partner_id = data.get('partner_id')
    
    if not match_id or not partner_id:
        await message.answer("❌ Suhbat topilmadi. Qayta urinib ko'ring.")
        await state.clear()
        return
    
    user = await db.get_user_by_telegram_id(message.from_user.id)
    partner = await db.get_user_profile_data(partner_id)
    
    # Xabarni saqlash
    await db.send_message(
        match_id=match_id,
        sender_id=user['id'],
        receiver_id=partner_id,
        text=message.text
    )
    
    await message.answer("✅ Xabar yuborildi!")
    
    # Partnerga xabar yuborish
    try:
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text="💬 Javob berish",
                    callback_data=f"openchat_{match_id}_{user['id']}"
                )]
            ]
        )
        
        await message.bot.send_message(
            partner['telegram_id'],
            f"💌 {user['full_name']} dan yangi xabar:\n\n{message.text}",
            reply_markup=keyboard
        )
    except:
        pass  # Agar foydalanuvchi botni to'xtatgan bo'lsa


@router.callback_query(F.data.startswith("viewprofile_"))
async def view_partner_profile(callback: CallbackQuery):
    """Sherikni profilini ko'rish"""
    partner_id = int(callback.data.split("_")[1])
    
    profile = await db.get_user_profile_data(partner_id)
    
    current_year = datetime.now().year
    age = current_year - profile['birth_year']
    gender_emoji = "👨" if profile['gender'] == 'erkak' else "👩"
    bio = profile.get('bio') or "Bio yozilmagan"
    
    text = f"""
{gender_emoji} {profile['full_name']}, {age}
📍 {profile['city']}
🧭 {profile['mode'].capitalize()}

💬 Bio:
{bio}
"""
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data=f"openchat_0_{partner_id}")]
        ]
    )
    
    if profile.get('photo_file_id'):
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=profile['photo_file_id'],
            caption=text,
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("block_"))
async def block_user(callback: CallbackQuery, state: FSMContext):
    """Foydalanuvchini bloklash"""
    partner_id = int(callback.data.split("_")[1])
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ha, bloklash", callback_data=f"confirmblock_{partner_id}")],
            [InlineKeyboardButton(text="❌ Yo'q", callback_data="back_to_chats")],
        ]
    )
    
    await callback.message.edit_text(
        "🚫 Ushbu foydalanuvchini bloklashni xohlaysizmi?\n\nBlokdan keyin u sizga xabar yubora olmaydi.",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("confirmblock_"))
async def confirm_block(callback: CallbackQuery):
    """Bloklashni tasdiqlash"""
    partner_id = int(callback.data.split("_")[1])
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    await db.block_user(user['id'], partner_id)
    
    await callback.message.edit_text("✅ Foydalanuvchi bloklandi")
    await callback.message.answer("💬 Suhbatlar ro'yxatiga qaytish uchun '💬 Suhbatlar' tugmasini bosing")


@router.callback_query(F.data.startswith("report_"))
async def report_user_start(callback: CallbackQuery, state: FSMContext):
    """Shikoyat qilishni boshlash"""
    partner_id = int(callback.data.split("_")[1])
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚫 Spam", callback_data=f"reportreason_{partner_id}_spam")],
            [InlineKeyboardButton(text="😡 Haqorat", callback_data=f"reportreason_{partner_id}_haqorat")],
            [InlineKeyboardButton(text="🔞 Nopasand kontent", callback_data=f"reportreason_{partner_id}_kontent")],
            [InlineKeyboardButton(text="💰 Pul so'rash", callback_data=f"reportreason_{partner_id}_pul")],
            [InlineKeyboardButton(text="🎭 Fake profil", callback_data=f"reportreason_{partner_id}_fake")],
            [InlineKeyboardButton(text="◀️ Bekor qilish", callback_data="back_to_chats")],
        ]
    )
    
    await callback.message.edit_text(
        "⚠️ Shikoyat sababi:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("reportreason_"))
async def report_user_reason(callback: CallbackQuery, state: FSMContext):
    """Shikoyat sababini saqlash"""
    parts = callback.data.split("_")
    partner_id = int(parts[1])
    reason = parts[2]
    
    await state.update_data(report_partner_id=partner_id, report_reason=reason)
    await state.set_state(ChatStates.report_details)
    
    await callback.message.edit_text(
        "📝 Qo'shimcha tafsilot yozing (ixtiyoriy):\n\nYoki /skip buyrug'ini yuboring"
    )


@router.message(ChatStates.report_details)
async def report_user_details(message: Message, state: FSMContext):
    """Shikoyat tafsilotlari"""
    data = await state.get_data()
    partner_id = data.get('report_partner_id')
    reason = data.get('report_reason')
    
    details = None if message.text == "/skip" else message.text
    
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    await db.create_report(
        reporter_id=user['id'],
        reported_id=partner_id,
        reason=reason,
        details=details
    )
    
    await state.clear()
    await message.answer(REPORT_SENT_MESSAGE)


@router.callback_query(F.data == "back_to_chats")
async def back_to_chats(callback: CallbackQuery, state: FSMContext):
    """Suhbatlarga qaytish"""
    await state.clear()
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        return
    
    # Matchlarni olish
    matches = await db.get_user_matches(user['id'])
    
    if not matches:
        await callback.message.edit_text(NO_CHATS_MESSAGE)
        return
    
    text = "💬 SIZNING SUHBATLARINGIZ\n\n"
    current_year = datetime.now().year
    
    keyboard_buttons = []
    for match in matches:
        age = current_year - match['birth_year']
        text += f"• {match['full_name']}, {age} - {match['city']}\n"
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"💬 {match['full_name']}",
                callback_data=f"openchat_{match['match_id']}_{match['id']}"
            )
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard)


# ========== BLOKDAN CHIQARISH ==========

@router.callback_query(F.data.startswith("unblock_"))
async def unblock_user(callback: CallbackQuery):
    """Foydalanuvchini blokdan chiqarish"""
    partner_id = int(callback.data.split("_")[1])
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    # Blokdan chiqarish
    await db.unblock_user(user['id'], partner_id)
    
    await callback.message.edit_text("✅ Foydalanuvchi blokdan chiqarildi")
    await callback.answer("Blokdan chiqarildi!")