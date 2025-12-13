from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from datetime import datetime
import logging

import config
from database import db
from states import StoryStates

router = Router()
logger = logging.getLogger(__name__)


# ============ STORY YARATISH ============

@router.message(Command("stories"))
async def cmd_stories(message: Message, state: FSMContext):
    """Hikoyalar bo'limi"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    if not user:
        await message.answer("❌ Avval ro'yxatdan o'ting: /start")
        return
    
    # Limitni tekshirish
    current_count, max_limit = await db.check_today_limit(user['id'], 'stories')
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📸 Story yuklash", callback_data="story_upload"),
            InlineKeyboardButton(text="👀 Hikoyalar", callback_data="story_view_all")
        ],
        [
            InlineKeyboardButton(text="📊 Mening hikoyalarim", callback_data="story_my_stories")
        ],
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="main_menu")]
    ])
    
    text = (
        f"📸 <b>Hikoyalar</b>\n\n"
        f"24 soat davomida ko'rinadigan rasm yoki video yuklang!\n\n"
        f"📊 Bugungi limitingiz: {current_count}/{max_limit}\n"
    )
    
    if not user['is_premium']:
        text += f"\n💎 Premium: {config.MAX_STORIES_PREMIUM} ta/kun"
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "story_upload")
async def story_upload_start(callback: CallbackQuery, state: FSMContext):
    """Story yuklashni boshlash"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    # Limitni tekshirish
    current_count, max_limit = await db.check_today_limit(user['id'], 'stories')
    
    if current_count >= max_limit:
        await callback.answer(
            f"❌ Bugungi limitingiz tugadi! Premium oling: /premium",
            show_alert=True
        )
        return
    
    await state.set_state(StoryStates.upload_story)
    await callback.message.answer(
        "📸 <b>Story yuklash</b>\n\n"
        "Rasm yoki video yuboring (max 10 MB):\n\n"
        "⚠️ Hikoya 24 soat davomida ko'rinadi."
    )
    await callback.answer()


@router.message(StoryStates.upload_story, F.photo | F.video)
async def story_photo_received(message: Message, state: FSMContext):
    """Story rasm/video qabul qilish"""
    user = await db.get_user_by_telegram_id(message.from_user.id)
    
    # Fayl turini aniqlash
    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
    elif message.video:
        # Video hajmini tekshirish
        if message.video.file_size > config.MAX_STORY_FILE_SIZE_MB * 1024 * 1024:
            await message.answer(
                f"❌ Video hajmi {config.MAX_STORY_FILE_SIZE_MB} MB dan katta!"
            )
            return
        file_id = message.video.file_id
        file_type = "video"
    else:
        await message.answer("❌ Faqat rasm yoki video yuboring!")
        return
    
    # Caption so'rash
    await state.update_data(file_id=file_id, file_type=file_type)
    await state.set_state(StoryStates.add_caption)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭️ Caption'siz davom etish", callback_data="story_no_caption")]
    ])
    
    await message.answer(
        "✍️ Story uchun matn yozing yoki 'Caption'siz davom etish' tugmasini bosing:",
        reply_markup=keyboard
    )


@router.message(StoryStates.add_caption, F.text)
async def story_caption_received(message: Message, state: FSMContext):
    """Caption qabul qilish"""
    data = await state.get_data()
    file_id = data['file_id']
    file_type = data['file_type']
    caption = message.text
    
    await create_story_final(message, state, file_id, file_type, caption)


@router.callback_query(F.data == "story_no_caption")
async def story_no_caption(callback: CallbackQuery, state: FSMContext):
    """Caption'siz story yaratish"""
    data = await state.get_data()
    file_id = data['file_id']
    file_type = data['file_type']
    
    await create_story_final(callback.message, state, file_id, file_type, None)
    await callback.answer()


async def create_story_final(message: Message, state: FSMContext, file_id: str, 
                            file_type: str, caption: str = None):
    """Story yaratish (final step)"""
    user = await db.get_user_by_telegram_id(message.from_user.id if message.from_user else message.chat.id)
    
    try:
        # Story yaratish
        story_id = await db.create_story(user['id'], file_id, file_type, caption)
        
        # Limitni oshirish
        await db.increment_daily_limit(user['id'], 'stories')
        
        await state.clear()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👀 Hikoyalarni ko'rish", callback_data="story_view_all")],
            [InlineKeyboardButton(text="🔙 Asosiy menyu", callback_data="main_menu")]
        ])
        
        await message.answer(
            "✅ <b>Story yuklandi!</b>\n\n"
            "Story 24 soat davomida ko'rinadi.\n"
            "Kim ko'rganini bilish uchun: /stories",
            reply_markup=keyboard
        )
        
        logger.info(f"Story yaratildi: user_id={user['id']}, story_id={story_id}")
        
    except Exception as e:
        logger.error(f"Story yaratish xatosi: {e}")
        await message.answer("❌ Xatolik yuz berdi. Qayta urinib ko'ring.")
        await state.clear()


# ============ STORY KO'RISH ============

@router.callback_query(F.data == "story_view_all")
async def story_view_all(callback: CallbackQuery, state: FSMContext):
    """Barcha hikoyalarni ko'rish"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    # Faol hikoyalarni olish (o'zimnikidan tashqari)
    stories = await db.get_active_stories(exclude_user_id=user['id'])
    
    if not stories:
        await callback.answer("😔 Hozir hikoyalar yo'q", show_alert=True)
        return
    
    await state.update_data(stories=stories, current_index=0)
    await state.set_state(StoryStates.viewing_stories)
    
    await show_story(callback.message, state, callback.from_user.id)
    await callback.answer()


async def show_story(message: Message, state: FSMContext, user_telegram_id: int):
    """Bitta hikoyani ko'rsatish"""
    data = await state.get_data()
    stories = data.get('stories', [])
    current_index = data.get('current_index', 0)
    
    if current_index >= len(stories):
        await message.answer("✅ Barcha hikoyalarni ko'rdingiz!")
        await state.clear()
        return
    
    story = stories[current_index]
    user = await db.get_user_by_telegram_id(user_telegram_id)
    
    # Story'ni ko'rilgan deb belgilash
    await db.view_story(story['id'], user['id'])
    
    # Caption
    caption = (
        f"👤 <b>{story['full_name']}</b>"
        f"{' ✅' if story['is_verified'] else ''}\n"
    )
    if story.get('caption'):
        caption += f"\n{story['caption']}"
    
    caption += f"\n\n👁 {story['views_count'] + 1} ta ko'rish"
    
    # Klaviatura
    buttons = []
    
    # Keyingi/Oldingi
    nav_buttons = []
    if current_index > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Oldingi", callback_data="story_prev"))
    if current_index < len(stories) - 1:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi ➡️", callback_data="story_next"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Profil va yopish
    buttons.append([
        InlineKeyboardButton(text="👤 Profil", callback_data=f"view_profile_{story['user_id']}"),
        InlineKeyboardButton(text="❌ Yopish", callback_data="story_close")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    # Hikoyani yuborish
    try:
        if story['file_type'] == 'photo':
            await message.answer_photo(
                photo=story['file_id'],
                caption=caption,
                reply_markup=keyboard
            )
        else:  # video
            await message.answer_video(
                video=story['file_id'],
                caption=caption,
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Story yuborish xatosi: {e}")
        # Keyingi story'ga o'tish
        await state.update_data(current_index=current_index + 1)
        await show_story(message, state, user_telegram_id)


@router.callback_query(F.data == "story_next")
async def story_next(callback: CallbackQuery, state: FSMContext):
    """Keyingi story"""
    data = await state.get_data()
    current_index = data.get('current_index', 0)
    
    await state.update_data(current_index=current_index + 1)
    await callback.message.delete()
    await show_story(callback.message, state, callback.from_user.id)
    await callback.answer()


@router.callback_query(F.data == "story_prev")
async def story_prev(callback: CallbackQuery, state: FSMContext):
    """Oldingi story"""
    data = await state.get_data()
    current_index = data.get('current_index', 0)
    
    if current_index > 0:
        await state.update_data(current_index=current_index - 1)
        await callback.message.delete()
        await show_story(callback.message, state, callback.from_user.id)
    
    await callback.answer()


@router.callback_query(F.data == "story_close")
async def story_close(callback: CallbackQuery, state: FSMContext):
    """Hikoyani yopish"""
    await callback.message.delete()
    await state.clear()
    await callback.answer()


# ============ MENING HIKOYALARIM ============

@router.callback_query(F.data == "story_my_stories")
async def my_stories(callback: CallbackQuery):
    """Mening hikoyalarim"""
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    stories = await db.get_user_stories(user['id'])
    
    if not stories:
        await callback.answer("😔 Sizda hikoyalar yo'q", show_alert=True)
        return
    
    text = "📊 <b>Mening hikoyalarim</b>\n\n"
    
    for i, story in enumerate(stories, 1):
        text += f"{i}. 👁 {story['views_count']} ta ko'rish\n"
        text += f"   📅 {story['created_at'].strftime('%H:%M, %d.%m.%Y')}\n"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"👁 Story #{i+1} ko'rganlar", 
            callback_data=f"story_viewers_{story['id']}"
        )]
        for i, story in enumerate(stories[:5])  # Faqat 5 tasi
    ] + [[InlineKeyboardButton(text="🔙 Ortga", callback_data="cmd_stories")]])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("story_viewers_"))
async def story_viewers(callback: CallbackQuery):
    """Story ko'rganlarni ko'rsatish"""
    story_id = int(callback.data.split("_")[2])
    
    viewers = await db.get_story_viewers(story_id)
    
    if not viewers:
        await callback.answer("👁 Hech kim ko'rmagan", show_alert=True)
        return
    
    text = "👁 <b>Story ko'rganlar</b>\n\n"
    
    for viewer in viewers[:20]:  # Faqat 20 tasi
        text += f"• {viewer['full_name']}"
        if viewer['is_verified']:
            text += " ✅"
        text += f"\n   {viewer['viewed_at'].strftime('%H:%M, %d.%m')}\n"
    
    if len(viewers) > 20:
        text += f"\n... va yana {len(viewers) - 20} kishi"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Ortga", callback_data="story_my_stories")]
    ])
    
    await callback.message.edit_text(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data == "cmd_stories")
async def cmd_stories_callback(callback: CallbackQuery, state: FSMContext):
    """Stories menyu (callback)"""
    await callback.message.delete()
    await cmd_stories(callback.message, state)
    await callback.answer()