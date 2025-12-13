from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from datetime import datetime

from database import db
from states import ProfileStates
from texts.messages import *
import config

router = Router()


@router.message(F.text == "👤 Profilim")
async def show_profile(message: Message):
    """Profilni ko'rsatish"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz. /start ni bosing")
        return
    
    profile_data = await db.get_user_profile_data(user['id'])
    
    # Yosh hisoblash
    current_year = datetime.now().year
    age = current_year - profile_data['birth_year']
    
    # Rasm holati
    photo_status = "✅ Yuklangan" if profile_data['photo_file_id'] else "❌ Yuklanmagan"
    
    # Bio
    bio = profile_data.get('bio') or "Bio yozilmagan"
    
    # Rejimga mos ma'lumot
    mode_info = ""
    if profile_data['mode'] == 'nikoh':
        p = profile_data.get('profile', {})
        mode_info = f"""
🕌 NIKOH REJIMI
Din: {p.get('religion', '-')}
Kasb: {p.get('occupation', '-')}
Ta'lim: {p.get('education', '-')}
Oilaviy holat: {p.get('marital_status', '-')}
Bolalar: {p.get('children', '-')}
"""
    elif profile_data['mode'] == 'dost':
        p = profile_data.get('profile', {})
        interests = ', '.join(p.get('interests', [])) if p.get('interests') else '-'
        languages = ', '.join(p.get('languages', [])) if p.get('languages') else '-'
        mode_info = f"""
👥 DO'ST REJIMI
Qiziqishlar: {interests}
Tillar: {languages}
"""
    elif profile_data['mode'] == 'talaba':
        p = profile_data.get('profile', {})
        mode_info = f"""
🎓 TALABA REJIMI
Universitet: {p.get('university', '-')}
Fakultet: {p.get('faculty', '-')}
Kurs: {p.get('course', '-')}
"""
    
    # Gender emoji
    gender_emoji = "👨" if profile_data['gender'] == 'erkak' else "👩"
    
    text = PROFILE_VIEW_MESSAGE.format(
        photo_status=photo_status,
        full_name=profile_data['full_name'],
        age=age,
        birth_year=profile_data['birth_year'],
        gender=f"{gender_emoji} {profile_data['gender'].capitalize()}",
        city=profile_data['city'],
        mode=profile_data['mode'].capitalize(),
        bio=bio,
        mode_info=mode_info,
        views=profile_data['profile_views']
    )
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Tahrirlash", callback_data="edit_profile")],
            [InlineKeyboardButton(text="🔄 Rejimni o'zgartirish", callback_data="change_mode")],
            [InlineKeyboardButton(text="⚙️ Qidiruv parametrlari", callback_data="edit_search_prefs")],
        ]
    )
    
    if profile_data['photo_file_id']:
        await message.answer_photo(
            photo=profile_data['photo_file_id'],
            caption=text,
            reply_markup=keyboard
        )
    else:
        await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "edit_profile")
async def edit_profile_menu(callback: CallbackQuery):
    """Tahrirlash menyusi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Ism", callback_data="edit_name")],
            [InlineKeyboardButton(text="📸 Rasm", callback_data="edit_photo")],
            [InlineKeyboardButton(text="✏️ Bio", callback_data="edit_bio")],
            [InlineKeyboardButton(text="🏙 Shahar", callback_data="edit_city")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_profile")],
        ]
    )
    
    await callback.message.edit_text(
        PROFILE_EDIT_MESSAGE,
        reply_markup=keyboard
    )


@router.callback_query(F.data == "edit_name")
async def start_edit_name(callback: CallbackQuery, state: FSMContext):
    """Ismni tahrirlash"""
    await callback.message.edit_text("📝 Yangi ismingizni kiriting:")
    await state.set_state(ProfileStates.editing_name)


@router.message(ProfileStates.editing_name)
async def process_edit_name(message: Message, state: FSMContext):
    """Yangi ismni saqlash"""
    new_name = message.text.strip()
    
    if len(new_name) < 3:
        await message.answer("❌ Ism juda qisqa. Qaytadan kiriting:")
        return
    
    user = await db.get_user_by_telegram_id(message.from_user.id)
    await db.update_user(user['id'], full_name=new_name)
    
    await state.clear()
    await message.answer("✅ Ism muvaffaqiyatli yangilandi!")
    await show_profile(message)


@router.callback_query(F.data == "edit_photo")
async def start_edit_photo(callback: CallbackQuery, state: FSMContext):
    """Rasmni tahrirlash"""
    await callback.message.edit_text("📸 Yangi rasmingizni yuboring:")
    await state.set_state(ProfileStates.editing_photo)


@router.message(ProfileStates.editing_photo, F.photo)
async def process_edit_photo(message: Message, state: FSMContext):
    """Yangi rasmni saqlash"""
    photo_file_id = message.photo[-1].file_id
    
    user = await db.get_user_by_telegram_id(message.from_user.id)
    await db.update_user(user['id'], photo_file_id=photo_file_id)
    
    await state.clear()
    await message.answer("✅ Rasm muvaffaqiyatli yangilandi!")
    await show_profile(message)


@router.callback_query(F.data == "edit_bio")
async def start_edit_bio(callback: CallbackQuery, state: FSMContext):
    """Bio tahrirlash"""
    await callback.message.edit_text("✏️ Yangi bio yozing (200 belgigacha):")
    await state.set_state(ProfileStates.editing_bio)


@router.message(ProfileStates.editing_bio)
async def process_edit_bio(message: Message, state: FSMContext):
    """Yangi bio saqlash"""
    new_bio = message.text.strip()
    
    if len(new_bio) > 200:
        await message.answer("❌ Bio 200 belgidan oshmasligi kerak. Qaytadan yozing:")
        return
    
    user = await db.get_user_by_telegram_id(message.from_user.id)
    await db.update_user(user['id'], bio=new_bio)
    
    await state.clear()
    await message.answer("✅ Bio muvaffaqiyatli yangilandi!")
    await show_profile(message)


@router.callback_query(F.data == "edit_city")
async def start_edit_city(callback: CallbackQuery, state: FSMContext):
    """Shaharni tahrirlash"""
    from keyboards.main_menu import get_city_keyboard
    
    await callback.message.edit_text(
        "🏙 Yangi shaharingizni tanlang:",
        reply_markup=get_city_keyboard(config.CITIES)
    )
    await state.set_state(ProfileStates.editing_city)


@router.callback_query(ProfileStates.editing_city, F.data.startswith("city_"))
async def process_edit_city(callback: CallbackQuery, state: FSMContext):
    """Yangi shaharni saqlash"""
    city = callback.data.split("_", 1)[1]
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    await db.update_user(user['id'], city=city)
    
    await state.clear()
    await callback.message.delete()
    await callback.message.answer("✅ Shahar muvaffaqiyatli yangilandi!")
    
    # Profilni qayta ko'rsatish
    await show_profile(callback.message)


@router.callback_query(F.data == "edit_search_prefs")
async def edit_search_preferences(callback: CallbackQuery):
    """Qidiruv parametrlarini tahrirlash"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    prefs = await db.get_user_profile_data(user['id'])
    search_prefs = prefs.get('search_prefs', {})
    
    text = f"""
🔍 QIDIRUV PARAMETRLARI

Jins: {search_prefs.get('looking_for_gender', '-')}
Yosh: {search_prefs.get('age_min', '-')} - {search_prefs.get('age_max', '-')}
Masofa: {search_prefs.get('distance_km', 'Cheklanmagan')} km

Yangilash uchun tanlang:
"""
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Jins", callback_data="pref_gender")],
            [InlineKeyboardButton(text="📅 Yosh", callback_data="pref_age")],
            [InlineKeyboardButton(text="📍 Masofa", callback_data="pref_distance")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_profile")],
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "back_to_profile")
async def back_to_profile(callback: CallbackQuery):
    """Profilga qaytish"""
    await callback.message.delete()
    await show_profile(callback.message)


# ========== REJIMLAR ==========

@router.message(F.text == "🧭 Rejimlar")
async def show_modes_menu(message: Message):
    """Rejimlar menyusi"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz. /start ni bosing")
        return
    
    current_mode = user['mode']
    mode_names = {'nikoh': '🕌 Nikoh', 'dost': '👥 Do\'st', 'talaba': '🎓 Talaba'}
    
    text = f"""
🧭 <b>REJIMLAR</b>

Hozirgi rejim: <b>{mode_names.get(current_mode, current_mode)}</b>

Boshqa rejimga o'tish uchun tanlang:

🕌 <b>Nikoh</b> - Jiddiy munosabat
👥 <b>Do'st</b> - Do'stlik topish
🎓 <b>Talaba</b> - Talabalar tanishuvi
"""
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕌 Nikoh rejimi", callback_data="switch_mode_nikoh")],
            [InlineKeyboardButton(text="👥 Do'st rejimi", callback_data="switch_mode_dost")],
            [InlineKeyboardButton(text="🎓 Talaba rejimi", callback_data="switch_mode_talaba")],
        ]
    )
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "change_mode")
async def change_mode_callback(callback: CallbackQuery):
    """Profildan rejim o'zgartirish"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    current_mode = user['mode']
    mode_names = {'nikoh': '🕌 Nikoh', 'dost': '👥 Do\'st', 'talaba': '🎓 Talaba'}
    
    text = f"""
🧭 <b>Rejimni o'zgartirish</b>

Hozirgi: <b>{mode_names.get(current_mode, current_mode)}</b>

Yangi rejim tanlang:
"""
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕌 Nikoh", callback_data="switch_mode_nikoh")],
            [InlineKeyboardButton(text="👥 Do'st", callback_data="switch_mode_dost")],
            [InlineKeyboardButton(text="🎓 Talaba", callback_data="switch_mode_talaba")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_profile")],
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("switch_mode_"))
async def switch_mode(callback: CallbackQuery):
    """Rejimni almashtirish"""
    new_mode = callback.data.split("_")[2]  # nikoh, dost, talaba
    
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if user['mode'] == new_mode:
        await callback.answer("Siz allaqachon bu rejimdaziz!", show_alert=True)
        return
    
    # Rejimni yangilash
    await db.update_user(user['id'], mode=new_mode)
    
    mode_names = {'nikoh': '🕌 Nikoh', 'dost': '👥 Do\'st', 'talaba': '🎓 Talaba'}
    
    await callback.message.edit_text(
        f"✅ Rejim o'zgartirildi!\n\nYangi rejim: <b>{mode_names.get(new_mode, new_mode)}</b>",
        parse_mode="HTML"
    )
    await callback.answer("Rejim o'zgartirildi!")