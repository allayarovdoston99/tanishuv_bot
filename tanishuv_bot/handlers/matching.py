from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from database import db
from keyboards.matching import *
from texts.messages import *
import config

router = Router()


@router.message(F.text == "🔍 Moslik topish")
async def start_matching(message: Message, state: FSMContext):
    """Moslik topishni boshlash"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz. /start ni bosing")
        return
    
    if user['status'] != 'active':
        await message.answer("❌ Sizning hisobingiz faol emas")
        return
    
    # Kunlik limit tekshirish
    swipes_today = await db.count_today_swipes(user['id'])
    max_swipes = config.MAX_DAILY_SWIPES_PREMIUM if user['is_premium'] else config.MAX_DAILY_SWIPES_FREE
    
    if swipes_today >= max_swipes and not user['is_premium']:
        await message.answer(
            DAILY_LIMIT_REACHED_MESSAGE.format(limit=max_swipes),
            reply_markup=get_no_profiles_keyboard()
        )
        return
    
    # Keyingi profilni ko'rsatish
    await show_next_profile(message, user['id'])


async def show_next_profile(message: Message, user_id: int):
    """Keyingi profilni ko'rsatish"""
    # Mos profillarni topish
    matches = await db.get_potential_matches(user_id, limit=1)
    
    if not matches:
        await message.answer(
            NO_PROFILES_MESSAGE,
            reply_markup=get_no_profiles_keyboard()
        )
        return
    
    profile = matches[0]
    
    # Profil ma'lumotlarini tayyorlash
    age = datetime.now().year - profile['birth_year']
    gender_emoji = "👨" if profile['gender'] == 'erkak' else "👩"
    
    # Bio
    bio = profile.get('bio') or "Bio yozilmagan"
    
    text = f"""
{gender_emoji} {profile['full_name']}, {age}
📍 {profile['city']}
🧭 {profile['mode'].capitalize()}

💬 {bio}

🔢 Qolgan swipe: {config.MAX_DAILY_SWIPES_FREE - await db.count_today_swipes(user_id)}
"""
    
    # Profilni yuborish
    if profile.get('photo_file_id'):
        await message.answer_photo(
            photo=profile['photo_file_id'],
            caption=text,
            reply_markup=get_matching_keyboard()
        )
    else:
        await message.answer(
            text,
            reply_markup=get_matching_keyboard()
        )
    
    # Profile view count oshirish
    await db.update_user(profile['id'], profile_views=profile['profile_views'] + 1)


@router.callback_query(F.data == "swipe_like")
async def swipe_like(callback: CallbackQuery):
    """Like bosish"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    # Profil ID ni message caption dan olish
    # Bu yerda oddiyroq yo'l - state ishlatish kerak edi, lekin:
    # Hozircha faqat bitta profil ko'rsatiladi, shuning uchun
    # oxirgi ko'rsatilgan profilni topish kerak
    
    matches = await db.get_potential_matches(user['id'], limit=1)
    if not matches:
        await callback.answer("❌ Profil topilmadi")
        return
    
    liked_profile = matches[0]
    
    # Like qo'shish
    is_match = await db.add_like(user['id'], liked_profile['id'])
    
    if is_match:
        # Match bo'ldi!
        await callback.message.delete()
        await callback.message.answer(
            MATCH_SUCCESS_MESSAGE.format(name=liked_profile['full_name']),
            reply_markup=get_match_success_keyboard(liked_profile['id'])
        )
        
        # Ikkinchi foydalanuvchiga ham xabar
        try:
            await callback.bot.send_message(
                liked_profile['telegram_id'],
                MATCH_SUCCESS_MESSAGE.format(name=user['full_name']),
                reply_markup=get_match_success_keyboard(user['id'])
            )
        except:
            pass  # Agar foydalanuvchi botni to'xtatgan bo'lsa
    else:
        # Match bo'lmadi, keyingi profilni ko'rsatish
        await callback.message.delete()
        await show_next_profile(callback.message, user['id'])


@router.callback_query(F.data == "swipe_pass")
async def swipe_pass(callback: CallbackQuery):
    """O'tkazish"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    await callback.message.delete()
    await show_next_profile(callback.message, user['id'])


@router.callback_query(F.data == "matching_stop")
async def matching_stop(callback: CallbackQuery):
    """Moslik topishni to'xtatish"""
    await callback.message.delete()
    await callback.message.answer(
        "⏸ Moslik topish to'xtatildi.\n\nKeyin davom etish uchun '🔍 Moslik topish' tugmasini bosing."
    )


@router.callback_query(F.data == "continue_matching")
async def continue_matching(callback: CallbackQuery):
    """Moslik topishni davom ettirish"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    await callback.message.delete()
    await show_next_profile(callback.message, user['id'])


@router.callback_query(F.data.startswith("open_chat_"))
async def open_chat(callback: CallbackQuery):
    """Suhbatni ochish"""
    partner_id = int(callback.data.split("_")[2])
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    # Match ID topish
    match_id = await db.get_match_id_between_users(user['id'], partner_id)
    
    if not match_id:
        await callback.answer("❌ Match topilmadi")
        return
    
    partner = await db.get_user_profile_data(partner_id)
    
    await callback.message.delete()
    await callback.message.answer(
        f"💬 {partner['full_name']} bilan suhbat\n\nXabar yozing:",
    )