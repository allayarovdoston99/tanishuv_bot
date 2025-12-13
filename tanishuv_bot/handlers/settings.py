# ==================== handlers/settings.py ====================

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import db
from texts.messages import SETTINGS_MESSAGE, ACCOUNT_DELETED_MESSAGE

router = Router()


# 🔹 ASOSIY SOZLAMALAR OYNASI
@router.message(F.text == "⚙️ Sozlamalar")
async def show_settings(message: Message):
    user = await db.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("❌ Siz ro'yxatdan o'tmagansiz. /start ni bosing")
        return

    # Dinamik menyu - status ga qarab
    buttons = [
        [InlineKeyboardButton(text="🔔 Bildirishnomalar", callback_data="settings_notifications")],
        [InlineKeyboardButton(text="🔒 Maxfiylik", callback_data="settings_privacy")],
        [InlineKeyboardButton(text="🌐 Til", callback_data="settings_language")],
    ]
    
    # Agar hisob to'xtatilgan bo'lsa - davom ettirish tugmasi
    if user['status'] == 'pause':
        buttons.append([InlineKeyboardButton(text="▶️ Hisobni davom ettirish", callback_data="settings_resume")])
    else:
        buttons.append([InlineKeyboardButton(text="⏸ Hisobni to'xtatish", callback_data="settings_pause")])
    
    buttons.append([InlineKeyboardButton(text="🗑 Hisobni o'chirish", callback_data="settings_delete")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    # Status xabari
    status_text = ""
    if user['status'] == 'pause':
        status_text = "\n\n⚠️ Hisobingiz to'xtatilgan. Profilingiz boshqalarga ko'rinmaydi."
    
    await message.answer(SETTINGS_MESSAGE + status_text, reply_markup=keyboard)


# 🔹 HISOBNI TO'XTATISH
@router.callback_query(F.data == "settings_pause")
async def pause_account(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ha, to'xtatish", callback_data="confirm_pause")],
            [InlineKeyboardButton(text="❌ Yo'q", callback_data="back_to_settings")],
        ]
    )

    await callback.message.edit_text(
        "⏸ Hisobni to'xtatilsinmi?\n\n"
        "To'xtatilgandan keyin profilingiz boshqalarga ko'rinmaydi.",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "confirm_pause")
async def confirm_pause_account(callback: CallbackQuery):
    user = await db.get_user_by_telegram_id(callback.from_user.id)

    if user:
        await db.update_user(user["id"], status="pause")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Sozlamalarga qaytish", callback_data="back_to_settings")],
        ]
    )

    await callback.message.edit_text(
        "✅ Hisobingiz to'xtatildi.\n\n"
        "Qayta faollashtirish uchun ⚙️ Sozlamalar bo'limiga kiring.",
        reply_markup=keyboard
    )


# 🔹 HISOBNI DAVOM ETTIRISH
@router.callback_query(F.data == "settings_resume")
async def resume_account(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Ha, davom ettirish", callback_data="confirm_resume")],
            [InlineKeyboardButton(text="❌ Yo'q", callback_data="back_to_settings")],
        ]
    )

    await callback.message.edit_text(
        "▶️ Hisobni davom ettirilsinmi?\n\n"
        "Faollashtirilgandan keyin profilingiz boshqalarga ko'rinadi.",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "confirm_resume")
async def confirm_resume_account(callback: CallbackQuery):
    user = await db.get_user_by_telegram_id(callback.from_user.id)

    if user:
        await db.update_user(user["id"], status="active")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Sozlamalarga qaytish", callback_data="back_to_settings")],
        ]
    )

    await callback.message.edit_text(
        "✅ Hisobingiz faollashtirildi!\n\n"
        "Endi profilingiz boshqalarga ko'rinadi va match topishingiz mumkin.",
        reply_markup=keyboard
    )


# 🔹 HISOBNI O'CHIRISH
@router.callback_query(F.data == "settings_delete")
async def delete_account(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🗑 Ha, o'chirish", callback_data="confirm_delete")],
            [InlineKeyboardButton(text="❌ Yo'q", callback_data="back_to_settings")],
        ]
    )

    await callback.message.edit_text(
        "⚠️ DIQQAT!\n\n"
        "Hisobingizni o'chirmoqchimisiz?\n"
        "Bu amal qaytarilmaydi!",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "confirm_delete")
async def confirm_delete_account(callback: CallbackQuery):
    user = await db.get_user_by_telegram_id(callback.from_user.id)

    if user:
        await db.update_user(user["id"], status="banned")

    await callback.message.edit_text(ACCOUNT_DELETED_MESSAGE)


# 🔹 BILDIRISHNOMALAR
@router.callback_query(F.data == "settings_notifications")
async def settings_notifications(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔔 Yoqish", callback_data="notif_on"),
             InlineKeyboardButton(text="🔕 O'chirish", callback_data="notif_off")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_settings")],
        ]
    )
    
    await callback.message.edit_text(
        "🔔 Bildirishnomalar sozlamalari\n\n"
        "Match va xabarlar haqida bildirishnoma olasizmi?",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("notif_"))
async def toggle_notifications(callback: CallbackQuery):
    status = "yoqildi" if callback.data == "notif_on" else "o'chirildi"
    await callback.answer(f"🔔 Bildirishnomalar {status}", show_alert=True)


# 🔹 MAXFIYLIK
@router.callback_query(F.data == "settings_privacy")
async def settings_privacy(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👁 Profil ko'rinishi", callback_data="privacy_visibility")],
            [InlineKeyboardButton(text="📍 Joylashuv", callback_data="privacy_location")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_settings")],
        ]
    )
    
    await callback.message.edit_text(
        "🔒 Maxfiylik sozlamalari\n\n"
        "Profilingiz ko'rinishini boshqaring:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("privacy_"))
async def toggle_privacy(callback: CallbackQuery):
    await callback.answer("Sozlama saqlandi ✅", show_alert=True)


# 🔹 TIL
@router.callback_query(F.data == "settings_language")
async def settings_language(callback: CallbackQuery):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇿 O'zbekcha", callback_data="lang_uz")],
            [InlineKeyboardButton(text="🇷🇺 Ruscha", callback_data="lang_ru")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="back_to_settings")],
        ]
    )
    
    await callback.message.edit_text(
        "🌐 Til sozlamalari\n\n"
        "Bot tilini tanlang:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("lang_"))
async def change_language(callback: CallbackQuery):
    lang = "O'zbekcha" if callback.data == "lang_uz" else "Ruscha"
    await callback.answer(f"Til: {lang} ✅", show_alert=True)


# 🔹 ORQAGA — SOZLAMALARGA QAYTISH
@router.callback_query(F.data == "back_to_settings")
async def back_to_settings(callback: CallbackQuery):
    user = await db.get_user_by_telegram_id(callback.from_user.id)
    
    if not user:
        await callback.answer("❌ Xatolik", show_alert=True)
        return
    
    # Dinamik menyu
    buttons = [
        [InlineKeyboardButton(text="🔔 Bildirishnomalar", callback_data="settings_notifications")],
        [InlineKeyboardButton(text="🔒 Maxfiylik", callback_data="settings_privacy")],
        [InlineKeyboardButton(text="🌐 Til", callback_data="settings_language")],
    ]
    
    if user['status'] == 'pause':
        buttons.append([InlineKeyboardButton(text="▶️ Hisobni davom ettirish", callback_data="settings_resume")])
    else:
        buttons.append([InlineKeyboardButton(text="⏸ Hisobni to'xtatish", callback_data="settings_pause")])
    
    buttons.append([InlineKeyboardButton(text="🗑 Hisobni o'chirish", callback_data="settings_delete")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    status_text = ""
    if user['status'] == 'pause':
        status_text = "\n\n⚠️ Hisobingiz to'xtatilgan."
    
    await callback.message.edit_text(SETTINGS_MESSAGE + status_text, reply_markup=keyboard)
