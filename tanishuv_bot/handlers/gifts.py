from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import logging

import config
from database import db
from states import GiftStates

router = Router()
logger = logging.getLogger(__name__)

# Gift emoji mapping
GIFT_EMOJIS = {
    "rose": "🌹",
    "heart": "❤️",
    "cake": "🎂",
    "diamond": "💎",
    "crown": "👑"
}


# ============ GIFT YUBORISH ============

@router.callback_query(F.data.startswith("send_gift_"))
async def send_gift_start(callback: CallbackQuery, state: FSMContext):
    """Gift yuborish jarayonini boshlash"""
    user_id = int(callback.data.split("_")[2])
    
    sender = await db.get_user_by_telegram_id(callback.from_user.id)
    receiver = await db.get_user_by_id(user_id)
    
    if not receiver:
        await callback.answer("❌ Foydalanuvchi topilmadi", show_alert=True)
        return
    
    # Bloklangan tekshirish
    if await db.is_blocked(sender['id'], user_id):
        await callback.answer("❌ Bu foydalanuvchi bilan aloqa o'rnatib bo'lmaydi", show_alert=True)
        return
    
    await state.update_data(receiver_id=user_id, receiver_name=receiver['full_name'])
    await state.set_state(GiftStates.choose_gift)
    
    # Gift'larni ko'rsatish
    keyboard_buttons = []
    
    for gift_key, price in config.GIFT_PRICES.items():
        emoji = GIFT_EMOJIS.get(gift_key, "🎁")
        gift_name = gift_key.capitalize()
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{emoji} {gift_name} - {price:,} so'm",
                callback_data=f"gift_select_{gift_key}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="gift_cancel")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    text = (
        f"🎁 <b>Sovg'a yuborish</b>\n\n"
        f"👤 {receiver['full_name']} uchun sovg'a tanlang:\n\n"
        f"💡 Sovg'a yuborish orqali diqqatingizni ko'rsatasiz!"
    )
    
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("gift_select_"))
async def gift_select(callback: CallbackQuery, state: FSMContext):
    """Gift tanlash"""
    gift_type = callback.data.split("_")[2]
    
    if gift_type not in config.GIFT_PRICES:
        await callback.answer("❌ Noto'g'ri sovg'a", show_alert=True)
        return
    
    price = config.GIFT_PRICES[gift_type]
    emoji = GIFT_EMOJIS.get(gift_type, "🎁")
    
    await state.update_data(gift_type=gift_type, gift_price=price)
    await state.set_state(GiftStates.add_message)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Xabarsiz yuborish", callback_data="gift_no_message")],
        [InlineKeyboardButton(text="❌ Bekor qilish", callback_data="gift_cancel")]
    ])
    
    await callback.message.edit_text(
        f"{emoji} <b>Sovg'a tanlandi!</b>\n\n"
        f"💰 Narx: {price:,} so'm\n\n"
        f"✍️ Sovg'a bilan birga xabar yuboring yoki 'Xabarsiz yuborish' tugmasini bosing:",
        reply_markup=keyboard
    )
    await callback.answer()


@router.message(GiftStates.add_message, F.text)
async def gift_message_received(message: Message, state: FSMContext):
    """Gift uchun xabar qabul qilish"""
    data = await state.get_data()
    gift_type = data['gift_type']
    gift_price = data['gift_price']
    gift_message = message.text
    
    await confirm_gift_send(message, state, gift_type, gift_price, gift_message)


@router.callback_query(F.data == "gift_no_message")
async def gift_no_message(callback: CallbackQuery, state: FSMContext):
    """Xabarsiz gift yuborish"""
    data = await state.get_data()
    gift_type = data['gift_type']
    gift_price = data['gift_price']
    
    await confirm_gift_send(callback.message, state, gift_type, gift_price, None)
    await callback.answer()


async def confirm_gift_send(message: Message, state: FSMContext, gift_type: str, 
                            gift_price: int, gift_message: str = None):
    """Gift yuborishni tasdiqlash"""
    data = await state.get_data()
    receiver_id = data['receiver_id']
    receiver_name = data['receiver_name']
    emoji = GIFT_EMOJIS.get(gift_type, "🎁")
    
    await state.update_data(gift_message=gift_message)
    await state.set_state(GiftStates.confirm_gift)
    
    text = (
        f"🎁 <b>Tasdiqlash</b>\n\n"
        f"👤 Qabul qiluvchi: {receiver_name}\n"
        f"{emoji} Sovg'a: {gift_type.capitalize()}\n"
        f"💰 Narx: {gift_price:,} so'm\n"
    )
    
    if gift_message:
        text += f"\n✉️ Xabar: {gift_message}\n"
    
    text += "\n❓ Yuborishni tasdiqlaysizmi?"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="gift_confirm_yes"),
            InlineKeyboardButton(text="❌ Yo'q", callback_data="gift_cancel")
        ]
    ])
    
    await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "gift_confirm_yes")
async def gift_confirm_yes(callback: CallbackQuery, state: FSMContext):
    """Gift yuborishni tasdiqlash"""
    data = await state.get_data()
    receiver_id = data['receiver_id']
    receiver_name = data['receiver_name']
    gift_type = data['gift_type']
    gift_price = data['gift_price']
    gift_message = data.get('gift_message')
    
    sender = await db.get_user_by_telegram_id(callback.from_user.id)
    receiver = await db.get_user_by_id(receiver_id)
    
    try:
        # Gift'ni database'ga saqlash
        gift_id = await db.send_gift(
            sender_id=sender['id'],
            receiver_id=receiver_id,
            gift_type=gift_type,
            amount=gift_price,
            message=gift_message
        )
        
        # Match ID topish
        match_id = await db.get_match_id_between_users(sender['id'], receiver_id)
        
        if match_id:
            # Suhbatga xabar qo'shish
            await db.send_message(
                match_id=match_id,
                sender_id=sender['id'],
                receiver_id=receiver_id,
                message_type='gift',
                gift_type=gift_type
            )
        
        emoji = GIFT_EMOJIS.get(gift_type, "🎁")
        
        # Qabul qiluvchiga xabar yuborish
        try:
            gift_text = (
                f"🎁 <b>Sovg'a oldiniz!</b>\n\n"
                f"👤 {sender['full_name']} sizga {emoji} {gift_type.capitalize()} yubordi!\n"
            )
            
            if gift_message:
                gift_text += f"\n✉️ Xabar: {gift_message}\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(
                    text="💬 Javob berish", 
                    callback_data=f"open_chat_{sender['id']}"
                )],
                [InlineKeyboardButton(
                    text="🎁 Sovg'a yuborish",
                    callback_data=f"send_gift_{sender['id']}"
                )]
            ])
            
            await callback.bot.send_message(
                chat_id=receiver['telegram_id'],
                text=gift_text,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Qabul qiluvchiga xabar yuborishda xato: {e}")
        
        await state.clear()
        
        await callback.message.edit_text(
            f"✅ <b>Sovg'a yuborildi!</b>\n\n"
            f"{emoji} {receiver_name} sizning sovg'angizni oldi.\n"
            f"💰 -{gift_price:,} so'm"
        )
        
        logger.info(f"Gift yuborildi: {sender['id']} -> {receiver_id}, type={gift_type}")
        
    except Exception as e:
        logger.error(f"Gift yuborishda xato: {e}")
        await callback.answer("❌ Xatolik yuz berdi", show_alert=True)
        await state.clear()


@router.callback_query(F.data == "gift_cancel")
async def gift_cancel(callback: CallbackQuery, state: FSMContext):
    """Gift yuborishni bekor qilish"""
    await state.clear()
    await callback.message.edit_text("❌ Bekor qilindi")
    await callback.answer()


# ============ QABUL QILINGAN SOVG'ALAR ============

@router.callback_query(F.data == "my_gifts")
async def my_gifts(callback: CallbackQuery):
    """Qabul qilingan sovg'alar"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    gifts = await db.get_received_gifts(user['id'])
    
    if not gifts:
        await callback.answer("😔 Sizga hali sovg'a yuborilmagan", show_alert=True)
        return
    
    text = "🎁 <b>Qabul qilingan sovg'alar</b>\n\n"
    
    for i, gift in enumerate(gifts[:10], 1):
        emoji = GIFT_EMOJIS.get(gift['gift_type'], "🎁")
        text += f"{i}. {emoji} {gift['gift_type'].capitalize()}\n"
        text += f"   👤 {gift['sender_name']}\n"
        text += f"   📅 {gift['created_at'].strftime('%d.%m.%Y %H:%M')}\n"
        
        if gift.get('message'):
            text += f"   ✉️ {gift['message']}\n"
        
        text += "\n"
    
    if len(gifts) > 10:
        text += f"\n... va yana {len(gifts) - 10} ta sovg'a"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="profile_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ============ GIFT STATISTIKASI ============

@router.callback_query(F.data == "gift_stats")
async def gift_stats(callback: CallbackQuery):
    """Gift statistikasi"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    async with db.pool.acquire() as conn:
        # Yuborilgan sovg'alar
        sent_stats = await conn.fetch("""
            SELECT gift_type, COUNT(*) as count, SUM(amount) as total
            FROM sent_gifts
            WHERE sender_id = $1
            GROUP BY gift_type
            ORDER BY count DESC
        """, user['id'])
        
        # Qabul qilingan sovg'alar
        received_stats = await conn.fetch("""
            SELECT gift_type, COUNT(*) as count
            FROM sent_gifts
            WHERE receiver_id = $1
            GROUP BY gift_type
            ORDER BY count DESC
        """, user['id'])
        
        # Jami
        total_sent = await conn.fetchval("""
            SELECT COALESCE(SUM(amount), 0)
            FROM sent_gifts
            WHERE sender_id = $1
        """, user['id']) or 0
        
        total_received = await conn.fetchval("""
            SELECT COUNT(*)
            FROM sent_gifts
            WHERE receiver_id = $1
        """, user['id']) or 0
    
    text = "📊 <b>Sovg'a Statistikasi</b>\n\n"
    
    if sent_stats:
        text += "<b>📤 Yuborilgan:</b>\n"
        for stat in sent_stats:
            emoji = GIFT_EMOJIS.get(stat['gift_type'], "🎁")
            text += f"{emoji} {stat['gift_type'].capitalize()}: {stat['count']} ta\n"
        text += f"\n💰 Jami: {total_sent:,} so'm\n"
    else:
        text += "📤 Yuborilgan sovg'alar yo'q\n"
    
    text += "\n"
    
    if received_stats:
        text += "<b>📥 Qabul qilingan:</b>\n"
        for stat in received_stats:
            emoji = GIFT_EMOJIS.get(stat['gift_type'], "🎁")
            text += f"{emoji} {stat['gift_type'].capitalize()}: {stat['count']} ta\n"
        text += f"\n🎁 Jami: {total_received} ta\n"
    else:
        text += "📥 Qabul qilingan sovg'alar yo'q\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Sovg'a yuborish", callback_data="gift_send_menu")],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="profile_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


# ============ GIFT HAQIDA MA'LUMOT ============

@router.callback_query(F.data == "gift_info")
async def gift_info(callback: CallbackQuery):
    """Gift haqida ma'lumot"""
    text = (
        "🎁 <b>Virtual Sovg'alar</b>\n\n"
        "Yoqqan odamingizga sovg'a yuboring va o'zingizga e'tiborni tortib oling!\n\n"
        "<b>Mavjud sovg'alar:</b>\n\n"
    )
    
    for gift_key, price in config.GIFT_PRICES.items():
        emoji = GIFT_EMOJIS.get(gift_key, "🎁")
        text += f"{emoji} <b>{gift_key.capitalize()}</b> - {price:,} so'm\n"
    
    text += (
        "\n<b>Qanday ishlaydi?</b>\n"
        "1️⃣ Profilga kiring\n"
        "2️⃣ 'Sovg'a yuborish' tugmasini bosing\n"
        "3️⃣ Sovg'a tanlang\n"
        "4️⃣ Xabar yozing (ixtiyoriy)\n"
        "5️⃣ Yuboring!\n\n"
        "💡 Sovg'a yuborish orqali diqqatingizni ko'rsatasiz va "
        "match bo'lish imkoniyatingiz oshadi!"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="help_menu")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()