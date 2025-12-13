# ==================== handlers/start.py ====================
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database import db
from states import OnboardingStates
from keyboards.main_menu import *
from texts.messages import *
import config

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Start buyrug'i"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if user:
        # Foydalanuvchi mavjud
        await state.clear()
        await message.answer(
            MAIN_MENU_MESSAGE,
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        # Yangi foydalanuvchi
        await message.answer(
            WELCOME_MESSAGE,
            reply_markup=get_start_keyboard(),
            parse_mode="HTML"
        )


@router.callback_query(F.data == "start_onboarding")
async def start_onboarding(callback: CallbackQuery, state: FSMContext):
    """Ro'yxatdan o'tishni boshlash"""
    await callback.message.edit_text(
        CHOOSE_MODE_MESSAGE,
        reply_markup=get_mode_keyboard()
    )
    await state.set_state(OnboardingStates.choose_mode)


@router.callback_query(OnboardingStates.choose_mode, F.data.startswith("mode_"))
async def choose_mode(callback: CallbackQuery, state: FSMContext):
    """Rejim tanlash"""
    mode = callback.data.split("_")[1]
    await state.update_data(mode=mode)
    
    await callback.message.edit_text(INPUT_NAME_MESSAGE)
    await state.set_state(OnboardingStates.input_name)


@router.message(OnboardingStates.input_name)
async def input_name(message: Message, state: FSMContext):
    """Ism kiritish"""
    full_name = message.text.strip()
    
    if len(full_name) < 3:
        await message.answer("❌ Ism juda qisqa. Qaytadan kiriting:")
        return
    
    await state.update_data(full_name=full_name)
    await message.answer(INPUT_BIRTH_YEAR_MESSAGE)
    await state.set_state(OnboardingStates.input_birth_year)


@router.message(OnboardingStates.input_birth_year)
async def input_birth_year(message: Message, state: FSMContext):
    """Tug'ilgan yil"""
    try:
        birth_year = int(message.text.strip())
        current_year = 2024
        age = current_year - birth_year
        
        if age < 18:
            await message.answer(AGE_ERROR_MESSAGE)
            return
        
        if birth_year < 1920 or birth_year > 2006:
            await message.answer("❌ Noto'g'ri yil. Qaytadan kiriting:")
            return
        
        await state.update_data(birth_year=birth_year)
        await message.answer(
            INPUT_GENDER_MESSAGE,
            reply_markup=get_gender_keyboard()
        )
        await state.set_state(OnboardingStates.input_gender)
        
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting. Misol: 1995")


@router.callback_query(OnboardingStates.input_gender, F.data.startswith("gender_"))
async def input_gender(callback: CallbackQuery, state: FSMContext):
    """Jins tanlash"""
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    
    await callback.message.edit_text(
        INPUT_CITY_MESSAGE,
        reply_markup=get_city_keyboard(config.CITIES)
    )
    await state.set_state(OnboardingStates.input_city)


@router.callback_query(OnboardingStates.input_city, F.data.startswith("city_"))
async def input_city(callback: CallbackQuery, state: FSMContext):
    """Shahar tanlash"""
    city = callback.data.split("_", 1)[1]
    await state.update_data(city=city)
    
    await callback.message.edit_text(
        INPUT_PHOTO_MESSAGE,
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(OnboardingStates.input_photo)


@router.message(OnboardingStates.input_photo, F.photo)
async def input_photo(message: Message, state: FSMContext):
    """Rasm yuklash"""
    photo_file_id = message.photo[-1].file_id
    await state.update_data(photo_file_id=photo_file_id)
    
    await message.answer(
        INPUT_BIO_MESSAGE,
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(OnboardingStates.input_bio)


@router.callback_query(OnboardingStates.input_photo, F.data == "skip")
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    """Rasmni o'tkazish"""
    await callback.message.edit_text(
        INPUT_BIO_MESSAGE,
        reply_markup=get_skip_keyboard()
    )
    await state.set_state(OnboardingStates.input_bio)


@router.message(OnboardingStates.input_bio)
async def input_bio(message: Message, state: FSMContext):
    """Bio kiritish"""
    bio = message.text.strip()
    
    if len(bio) > 200:
        await message.answer("❌ Bio 200 belgidan oshmasligi kerak. Qaytadan yozing:")
        return
    
    await state.update_data(bio=bio)
    
    # Rejimga qarab qo'shimcha savollar
    data = await state.get_data()
    mode = data['mode']
    
    if mode == 'nikoh':
        await message.answer(
            NIKOH_RELIGION_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=r, callback_data=f"religion_{r}")] 
                    for r in config.RELIGIONS
                ]
            )
        )
        await state.set_state(OnboardingStates.nikoh_religion)
    elif mode == 'dost':
        await message.answer(
            DOST_INTERESTS_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=i, callback_data=f"interest_{i}")] 
                    for i in config.INTERESTS[:5]
                ] + [[InlineKeyboardButton(text="✅ Davom etish", callback_data="interests_done")]]
            )
        )
        await state.update_data(selected_interests=[])
        await state.set_state(OnboardingStates.dost_interests)
    elif mode == 'talaba':
        await message.answer(TALABA_UNIVERSITY_MESSAGE)
        await state.set_state(OnboardingStates.talaba_university)


@router.callback_query(OnboardingStates.input_bio, F.data == "skip")
async def skip_bio(callback: CallbackQuery, state: FSMContext):
    """Bio o'tkazish"""
    data = await state.get_data()
    mode = data['mode']
    
    if mode == 'nikoh':
        await callback.message.edit_text(
            NIKOH_RELIGION_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=r, callback_data=f"religion_{r}")] 
                    for r in config.RELIGIONS
                ]
            )
        )
        await state.set_state(OnboardingStates.nikoh_religion)
    elif mode == 'dost':
        await callback.message.edit_text(
            DOST_INTERESTS_MESSAGE,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text=i, callback_data=f"interest_{i}")] 
                    for i in config.INTERESTS[:5]
                ] + [[InlineKeyboardButton(text="✅ Davom etish", callback_data="interests_done")]]
            )
        )
        await state.update_data(selected_interests=[])
        await state.set_state(OnboardingStates.dost_interests)
    elif mode == 'talaba':
        await callback.message.edit_text(TALABA_UNIVERSITY_MESSAGE)
        await state.set_state(OnboardingStates.talaba_university)


# ========== NIKOH REJIMI ==========

@router.callback_query(OnboardingStates.nikoh_religion, F.data.startswith("religion_"))
async def nikoh_religion(callback: CallbackQuery, state: FSMContext):
    """Din tanlash"""
    religion = callback.data.split("_", 1)[1]
    await state.update_data(religion=religion)
    
    await callback.message.edit_text(NIKOH_OCCUPATION_MESSAGE)
    await state.set_state(OnboardingStates.nikoh_occupation)


@router.message(OnboardingStates.nikoh_occupation)
async def nikoh_occupation(message: Message, state: FSMContext):
    """Kasb"""
    occupation = message.text.strip()
    await state.update_data(occupation=occupation)
    
    await message.answer(
        NIKOH_EDUCATION_MESSAGE,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=e, callback_data=f"education_{e}")] 
                for e in config.EDUCATION_LEVELS
            ]
        )
    )
    await state.set_state(OnboardingStates.nikoh_education)


@router.callback_query(OnboardingStates.nikoh_education, F.data.startswith("education_"))
async def nikoh_education(callback: CallbackQuery, state: FSMContext):
    """Ta'lim"""
    education = callback.data.split("_", 1)[1]
    await state.update_data(education=education)
    
    await callback.message.edit_text(
        NIKOH_MARITAL_STATUS_MESSAGE,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Turmushga chiqmagan", callback_data="marital_turmushga_chiqmagan")],
                [InlineKeyboardButton(text="Ajrashgan", callback_data="marital_ajrashgan")],
                [InlineKeyboardButton(text="Beva", callback_data="marital_beva")],
            ]
        )
    )
    await state.set_state(OnboardingStates.nikoh_marital_status)


@router.callback_query(OnboardingStates.nikoh_marital_status, F.data.startswith("marital_"))
async def nikoh_marital_status(callback: CallbackQuery, state: FSMContext):
    """Oilaviy holat"""
    marital_status = callback.data.split("_", 1)[1]
    await state.update_data(marital_status=marital_status)
    
    await callback.message.edit_text(
        NIKOH_CHILDREN_MESSAGE,
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Bor", callback_data="children_bor")],
                [InlineKeyboardButton(text="Yo'q", callback_data="children_yoq")],
                [InlineKeyboardButton(text="Keyinchalik", callback_data="children_keyinchalik")],
            ]
        )
    )
    await state.set_state(OnboardingStates.nikoh_children)


@router.callback_query(OnboardingStates.nikoh_children, F.data.startswith("children_"))
async def nikoh_children(callback: CallbackQuery, state: FSMContext):
    """Bolalar"""
    children = callback.data.split("_", 1)[1]
    await state.update_data(children=children)
    
    # Qidiruv parametrlari
    await callback.message.edit_text(
        SEARCH_GENDER_MESSAGE,
        reply_markup=get_looking_for_gender_keyboard()
    )
    await state.set_state(OnboardingStates.search_gender)


# ========== DO'ST REJIMI ==========

@router.callback_query(OnboardingStates.dost_interests, F.data.startswith("interest_"))
async def dost_select_interest(callback: CallbackQuery, state: FSMContext):
    """Qiziqish tanlash"""
    interest = callback.data.split("_", 1)[1]
    data = await state.get_data()
    interests = data.get('selected_interests', [])
    
    if interest in interests:
        interests.remove(interest)
    else:
        if len(interests) < 5:
            interests.append(interest)
    
    await state.update_data(selected_interests=interests)
    await callback.answer(f"Tanlandi: {len(interests)}/5")


@router.callback_query(OnboardingStates.dost_interests, F.data == "interests_done")
async def dost_interests_done(callback: CallbackQuery, state: FSMContext):
    """Qiziqishlar tayyor"""
    data = await state.get_data()
    interests = data.get('selected_interests', [])
    
    if not interests:
        await callback.answer("❌ Kamida 1 ta qiziqish tanlang!")
        return
    
    await callback.message.edit_text(DOST_LANGUAGES_MESSAGE)
    await state.set_state(OnboardingStates.dost_languages)


@router.message(OnboardingStates.dost_languages)
async def dost_languages(message: Message, state: FSMContext):
    """Tillar"""
    languages = [lang.strip() for lang in message.text.split(",")]
    await state.update_data(languages=languages)
    
    # Qidiruv parametrlari
    await message.answer(
        SEARCH_GENDER_MESSAGE,
        reply_markup=get_looking_for_gender_keyboard()
    )
    await state.set_state(OnboardingStates.search_gender)


# ========== TALABA REJIMI ==========

@router.message(OnboardingStates.talaba_university)
async def talaba_university(message: Message, state: FSMContext):
    """Universitet"""
    university = message.text.strip()
    await state.update_data(university=university)
    
    await message.answer(TALABA_FACULTY_MESSAGE)
    await state.set_state(OnboardingStates.talaba_faculty)


@router.message(OnboardingStates.talaba_faculty)
async def talaba_faculty(message: Message, state: FSMContext):
    """Fakultet"""
    faculty = message.text.strip()
    await state.update_data(faculty=faculty)
    
    await message.answer(TALABA_COURSE_MESSAGE)
    await state.set_state(OnboardingStates.talaba_course)


@router.message(OnboardingStates.talaba_course)
async def talaba_course(message: Message, state: FSMContext):
    """Kurs"""
    try:
        course = int(message.text.strip())
        if course < 1 or course > 6:
            await message.answer("❌ Kurs 1 dan 6 gacha bo'lishi kerak")
            return
        
        await state.update_data(course=course)
        
        # Qidiruv parametrlari
        await message.answer(
            SEARCH_GENDER_MESSAGE,
            reply_markup=get_looking_for_gender_keyboard()
        )
        await state.set_state(OnboardingStates.search_gender)
        
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting (1-6)")


# ========== QIDIRUV PARAMETRLARI ==========

@router.callback_query(OnboardingStates.search_gender, F.data.startswith("looking_"))
async def search_gender(callback: CallbackQuery, state: FSMContext):
    """Qidiruv jinsi"""
    gender = callback.data.split("_", 1)[1]
    await state.update_data(looking_gender=gender)
    
    await callback.message.edit_text(SEARCH_AGE_MESSAGE)
    await state.set_state(OnboardingStates.search_age_min)


@router.message(OnboardingStates.search_age_min)
async def search_age_min(message: Message, state: FSMContext):
    """Minimal yosh"""
    try:
        age_min = int(message.text.strip())
        if age_min < 18 or age_min > 100:
            await message.answer("❌ Yosh 18 dan 100 gacha bo'lishi kerak")
            return
        
        await state.update_data(age_min=age_min)
        await message.answer(SEARCH_AGE_MAX_MESSAGE)
        await state.set_state(OnboardingStates.search_age_max)
        
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting")


@router.message(OnboardingStates.search_age_max)
async def search_age_max(message: Message, state: FSMContext):
    """Maksimal yosh"""
    try:
        age_max = int(message.text.strip())
        data = await state.get_data()
        age_min = data['age_min']
        
        if age_max < age_min:
            await message.answer("❌ Maksimal yosh minimal yoshdan katta bo'lishi kerak")
            return
        
        if age_max > 100:
            await message.answer("❌ Yosh 100 dan oshmasligi kerak")
            return
        
        await state.update_data(age_max=age_max)
        
        await message.answer(
            SEARCH_DISTANCE_MESSAGE,
            reply_markup=get_distance_keyboard()
        )
        await state.set_state(OnboardingStates.search_distance)
        
    except ValueError:
        await message.answer("❌ Faqat raqam kiriting")


@router.callback_query(OnboardingStates.search_distance, F.data.startswith("distance_"))
async def search_distance(callback: CallbackQuery, state: FSMContext):
    """Masofa"""
    distance = callback.data.split("_")[1]
    
    if distance == "all":
        distance_km = None
    else:
        distance_km = int(distance)
    
    await state.update_data(distance_km=distance_km)
    
    # Qoidalarni ko'rsatish
    await callback.message.edit_text(
        CONFIRM_RULES_MESSAGE,
        reply_markup=get_confirm_rules_keyboard()
    )
    await state.set_state(OnboardingStates.confirm_rules)


@router.callback_query(OnboardingStates.confirm_rules, F.data == "confirm_rules")
async def confirm_rules(callback: CallbackQuery, state: FSMContext):
    """Qoidalarni tasdiqlash va ro'yxatdan o'tishni tugatish"""
    data = await state.get_data()
    
    # Foydalanuvchi yaratish
    user_id = await db.create_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        full_name=data['full_name'],
        birth_year=data['birth_year'],
        gender=data['gender'],
        city=data['city'],
        mode=data['mode']
    )
    
    # Rasm va bio yangilash
    if 'photo_file_id' in data:
        await db.update_user(user_id, photo_file_id=data['photo_file_id'])
    
    if 'bio' in data:
        await db.update_user(user_id, bio=data['bio'])
    
    # Rejimga mos profil yaratish
    mode = data['mode']
    
    if mode == 'nikoh':
        await db.create_nikoh_profile(
            user_id=user_id,
            religion=data.get('religion'),
            occupation=data.get('occupation'),
            education=data.get('education'),
            marital_status=data.get('marital_status'),
            children=data.get('children')
        )
    elif mode == 'dost':
        await db.create_dost_profile(
            user_id=user_id,
            interests=data.get('selected_interests', []),
            languages=data.get('languages', [])
        )
    elif mode == 'talaba':
        await db.create_talaba_profile(
            user_id=user_id,
            university=data.get('university'),
            faculty=data.get('faculty'),
            course=data.get('course')
        )
    
    # Qidiruv parametrlari
    await db.create_search_preferences(
        user_id=user_id,
        gender=data['looking_gender'],
        age_min=data['age_min'],
        age_max=data['age_max'],
        distance_km=data.get('distance_km')
    )
    
    await state.clear()
    
    await callback.message.edit_text(ONBOARDING_COMPLETE_MESSAGE)
    await callback.message.answer(
        MAIN_MENU_MESSAGE,
        reply_markup=get_main_menu_keyboard()
    )


# ========== UMUMIY CALLBACKLAR ==========

@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """Bosh menyuga qaytish"""
    await state.clear()
    await callback.message.delete()
    await callback.message.answer(
        MAIN_MENU_MESSAGE,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "show_premium")
async def show_premium_callback(callback: CallbackQuery):
    """Premium sahifasini ko'rsatish"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("❌ Siz ro'yxatdan o'tmagansiz. /start ni bosing", show_alert=True)
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
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="main_menu")],
        ]
    )
    
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "close_message")
async def close_message(callback: CallbackQuery):
    """Xabarni yopish"""
    await callback.message.delete()
    await callback.answer()