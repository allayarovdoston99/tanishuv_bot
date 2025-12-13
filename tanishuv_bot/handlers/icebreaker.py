from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import random
import logging

import config
from database import db
from states import IcebreakerStates

router = Router()
logger = logging.getLogger(__name__)


# ============ ICEBREAKER O'YIN BOSHLASH ============

@router.callback_query(F.data.startswith("icebreaker_start_"))
async def icebreaker_start(callback: CallbackQuery, state: FSMContext):
    """Icebreaker o'yinini boshlash"""
    partner_id = int(callback.data.split("_")[2])
    
    sender = await db.get_user_by_telegram_id(callback.from_user.id)
    partner = await db.get_user_by_id(partner_id)
    
    if not partner:
        await callback.answer("❌ Foydalanuvchi topilmadi", show_alert=True)
        return
    
    # Match ID topish
    match_id = await db.get_match_id_between_users(sender['id'], partner_id)
    
    if not match_id:
        await callback.answer("❌ Avval match bo'ling!", show_alert=True)
        return
    
    # Random savol tanlash
    question = random.choice(config.ICEBREAKER_QUESTIONS)
    
    await state.update_data(
        partner_id=partner_id,
        partner_name=partner['full_name'],
        match_id=match_id,
        current_question=question
    )
    await state.set_state(IcebreakerStates.playing_game)
    
    text = (
        f"🎮 <b>Icebreaker O'yin</b>\n\n"
        f"👤 {partner['full_name']} bilan tanishish uchun savol:\n\n"
        f"❓ <i>{question}</i>\n\n"
        f"✍️ Javobingizni yozing:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Boshqa savol", callback_data="icebreaker_new_question")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="icebreaker_cancel")]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "icebreaker_new_question")
async def icebreaker_new_question(callback: CallbackQuery, state: FSMContext):
    """Yangi savol olish"""
    data = await state.get_data()
    current_question = data.get('current_question')
    
    # Avvalgi savoldan boshqa savol tanlash
    questions = [q for q in config.ICEBREAKER_QUESTIONS if q != current_question]
    new_question = random.choice(questions)
    
    await state.update_data(current_question=new_question)
    
    text = (
        f"🎮 <b>Yangi savol:</b>\n\n"
        f"❓ <i>{new_question}</i>\n\n"
        f"✍️ Javobingizni yozing:"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Boshqa savol", callback_data="icebreaker_new_question")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="icebreaker_cancel")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.message(IcebreakerStates.playing_game, F.text)
async def icebreaker_answer(message: Message, state: FSMContext):
    """Icebreaker javob"""
    data = await state.get_data()
    partner_id = data['partner_id']
    partner_name = data['partner_name']
    match_id = data['match_id']
    question = data['current_question']
    answer = message.text
    
    sender = await db.get_user_by_telegram_id(message.from_user.id)
    partner = await db.get_user_by_id(partner_id)
    
    # Javobni saqlash
    try:
        # Xabar yuborish
        await db.send_message(
            match_id=match_id,
            sender_id=sender['id'],
            receiver_id=partner_id,
            message_text=f"🎮 Icebreaker\n\n❓ {question}\n\n💬 {answer}"
        )
        
        # Partner'ga yuborish
        try:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💬 Javob berish", callback_data=f"open_chat_{sender['id']}")],
                [InlineKeyboardButton(text="🎮 O'ynash", callback_data=f"icebreaker_start_{sender['id']}")]
            ])
            
            await message.bot.send_message(
                chat_id=partner['telegram_id'],
                text=(
                    f"🎮 <b>{sender['full_name']} Icebreaker o'yinini boshladi!</b>\n\n"
                    f"❓ <i>{question}</i>\n\n"
                    f"💬 {answer}"
                ),
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Partner'ga xabar yuborishda xato: {e}")
        
        await state.clear()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Suhbatni ochish", callback_data=f"open_chat_{partner_id}")],
            [InlineKeyboardButton(text="🎮 Yana o'ynash", callback_data=f"icebreaker_start_{partner_id}")]
        ])
        
        await message.answer(
            f"✅ <b>Javobingiz yuborildi!</b>\n\n"
            f"👤 {partner_name} javob kutmoqda...",
            reply_markup=keyboard
        )
        
        logger.info(f"Icebreaker: {sender['id']} -> {partner_id}")
        
    except Exception as e:
        logger.error(f"Icebreaker xato: {e}")
        await message.answer("❌ Xatolik yuz berdi")
        await state.clear()


@router.callback_query(F.data == "icebreaker_cancel")
async def icebreaker_cancel(callback: CallbackQuery, state: FSMContext):
    """O'yinni bekor qilish"""
    await state.clear()
    await callback.message.edit_text("❌ O'yin bekor qilindi")
    await callback.answer()


# ============ ICEBREAKER MENU ============

@router.callback_query(F.data == "icebreaker_menu")
async def icebreaker_menu(callback: CallbackQuery):
    """Icebreaker menyu"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    # Statistika
    async with db.pool.acquire() as conn:
        games_played = await conn.fetchval("""
            SELECT COUNT(*) FROM messages
            WHERE (sender_id = $1 OR receiver_id = $1)
            AND message_text LIKE '🎮 Icebreaker%'
        """, user['id']) or 0
    
    text = (
        f"🎮 <b>Icebreaker O'yinlari</b>\n\n"
        f"Tanishuv uchun qiziqarli savollar!\n\n"
        f"📊 Sizning o'yinlaringiz: {games_played} ta\n\n"
        f"<b>Qanday ishlaydi?</b>\n"
        f"1️⃣ Match bo'lgan odamni tanlang\n"
        f"2️⃣ 'Icebreaker o'ynash' tugmasini bosing\n"
        f"3️⃣ Random savol beriladi\n"
        f"4️⃣ Javob yozing va yuboring\n"
        f"5️⃣ Ular ham javob berishadi!\n\n"
        f"💡 Bu suhbatni boshlashning eng oson yo'li!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Barcha savollar", callback_data="icebreaker_all_questions")],
        [InlineKeyboardButton(text="🎲 Random savol", callback_data="icebreaker_random_question")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="help_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "icebreaker_all_questions")
async def icebreaker_all_questions(callback: CallbackQuery):
    """Barcha savollar"""
    text = "📋 <b>Icebreaker Savollari</b>\n\n"
    
    for i, question in enumerate(config.ICEBREAKER_QUESTIONS, 1):
        text += f"{i}. {question}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="icebreaker_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "icebreaker_random_question")
async def icebreaker_random_question(callback: CallbackQuery):
    """Random savol"""
    question = random.choice(config.ICEBREAKER_QUESTIONS)
    
    text = (
        f"🎲 <b>Random savol:</b>\n\n"
        f"❓ <i>{question}</i>\n\n"
        f"Bu savolni do'stingizga bering va javobini oling!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Boshqa savol", callback_data="icebreaker_random_question")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="icebreaker_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ============ STATISTIKA ============

@router.callback_query(F.data == "icebreaker_stats")
async def icebreaker_stats(callback: CallbackQuery):
    """Icebreaker statistika"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    async with db.pool.acquire() as conn:
        # Yuborilgan
        sent_count = await conn.fetchval("""
            SELECT COUNT(*) FROM messages
            WHERE sender_id = $1 AND message_text LIKE '🎮 Icebreaker%'
        """, user['id']) or 0
        
        # Qabul qilingan
        received_count = await conn.fetchval("""
            SELECT COUNT(*) FROM messages
            WHERE receiver_id = $1 AND message_text LIKE '🎮 Icebreaker%'
        """, user['id']) or 0
        
        # Eng faol sherik
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
            AND m.message_text LIKE '🎮 Icebreaker%'
            GROUP BY u.id, u.full_name
            ORDER BY count DESC
            LIMIT 1
        """, user['id'])
    
    text = (
        f"📊 <b>Icebreaker Statistika</b>\n\n"
        f"📤 Yuborilgan: {sent_count} ta\n"
        f"📥 Qabul qilingan: {received_count} ta\n"
        f"🎮 Jami o'yinlar: {sent_count + received_count} ta\n"
    )
    
    if top_partner:
        text += f"\n👤 Eng faol sherik: {top_partner['full_name']} ({top_partner['count']} ta o'yin)"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="icebreaker_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ============ ICEBREAKER TUGMASI PROFILGA QO'SHISH ============

def get_icebreaker_button(user_id: int) -> InlineKeyboardButton:
    """Profile uchun icebreaker tugmasi"""
    return InlineKeyboardButton(
        text="🎮 Icebreaker o'ynash",
        callback_data=f"icebreaker_start_{user_id}"
    )


# ============ ICEBREAKER TAKLIF ============

@router.callback_query(F.data == "icebreaker_suggest")
async def icebreaker_suggest(callback: CallbackQuery):
    """Icebreaker taklifi"""
    text = (
        "💡 <b>Suhbatni boshlash qiyin?</b>\n\n"
        "🎮 Icebreaker o'yini yordam beradi!\n\n"
        "Bu qiziqarli savollarga javob berib, "
        "bir-biringizni yaxshiroq tanishingiz uchun yaratilgan.\n\n"
        "Boshlaymizmi?"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎮 Ha, boshlaymiz!", callback_data="icebreaker_menu")],
        [InlineKeyboardButton(text="❌ Yo'q, rahmat", callback_data="close_message")]
    ])
    
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()