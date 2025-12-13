from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database import db
from states import AdminStates
from keyboards.admin import *
from texts.messages import *
import config

router = Router()


def is_admin(user_id: int) -> bool:
    """Admin ekanligini tekshirish"""
    return user_id in config.ADMIN_IDS


@router.message(Command("admin"))
async def admin_panel(message: Message):
    """Admin panel"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q")
        return
    
    await message.answer(
        ADMIN_MENU_MESSAGE,
        reply_markup=get_admin_keyboard()
    )


@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery):
    """Statistika"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q")
        return
    
    stats = await db.get_stats()
    
    text = f"""
📊 STATISTIKA

👥 Foydalanuvchilar:
• Jami: {stats['total_users']}
• Faol: {stats['active_users']}
• To'xtatilgan: {stats['paused_users']}
• Bloklangan: {stats['banned_users']}

🧭 Rejimlar:
• Nikoh: {stats['nikoh_users']}
• Do'st: {stats['dost_users']}
• Talaba: {stats['talaba_users']}

💫 Match:
• Bugungi matchlar: {stats['today_matches']}

⭐ Premium:
• Premium foydalanuvchilar: {stats['premium_users']}
• Bugungi daromad: {stats['today_revenue']:,} so'm
"""
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Yangilash", callback_data="admin_stats")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_back")],
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "admin_users")
async def show_users(callback: CallbackQuery):
    """Foydalanuvchilar"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q")
        return
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👥 Barcha", callback_data="users_all")],
            [InlineKeyboardButton(text="✅ Faol", callback_data="users_active")],
            [InlineKeyboardButton(text="⏸ To'xtatilgan", callback_data="users_paused")],
            [InlineKeyboardButton(text="🚫 Bloklangan", callback_data="users_banned")],
            [InlineKeyboardButton(text="⭐ Premium", callback_data="users_premium")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_back")],
        ]
    )
    
    await callback.message.edit_text(
        "👥 Foydalanuvchilar\n\nFiltr tanlang:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("users_"))
async def filter_users(callback: CallbackQuery):
    """Foydalanuvchilarni filtrlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q")
        return
    
    filter_type = callback.data.split("_")[1]
    
    filters = {}
    if filter_type == "active":
        filters['status'] = 'active'
    elif filter_type == "paused":
        filters['status'] = 'pause'
    elif filter_type == "banned":
        filters['status'] = 'banned'
    elif filter_type == "premium":
        filters['is_premium'] = True
    
    users = await db.search_users(**filters)
    
    if not users:
        await callback.answer("Foydalanuvchilar topilmadi")
        return
    
    text = f"👥 Foydalanuvchilar ({len(users)} ta):\n\n"
    
    for user in users[:20]:  # Faqat 20 ta
        text += f"• {user['full_name']} (@{user['username'] or 'username_yoq'})\n"
        text += f"  ID: {user['telegram_id']}, Shahar: {user['city']}\n\n"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_users")],
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == "admin_reports")
async def show_reports(callback: CallbackQuery):
    """Shikoyatlar"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q")
        return
    
    reports = await db.get_pending_reports()
    
    if not reports:
        await callback.message.edit_text(
            "✅ Yangi shikoyatlar yo'q",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_back")]
                ]
            )
        )
        return
    
    text = "⚠️ SHIKOYATLAR\n\n"
    
    for report in reports[:5]:
        text += f"📋 Shikoyat #{report['id']}\n"
        text += f"Shikoyatchi: {report['reporter_name']} (@{report['reporter_username']})\n"
        text += f"Ayblanuvchi: {report['reported_name']} (@{report['reported_username']})\n"
        text += f"Sabab: {report['reason']}\n"
        if report['details']:
            text += f"Tafsilot: {report['details']}\n"
        text += "\n"
    
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👀 Ko'rib chiqish", callback_data=f"review_report_{reports[0]['id']}")],
            [InlineKeyboardButton(text="◀️ Orqaga", callback_data="admin_back")],
        ]
    )
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("review_report_"))
async def review_report(callback: CallbackQuery):
    """Shikoyatni ko'rib chiqish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q")
        return
    
    report_id = int(callback.data.split("_")[2])
    
    reports = await db.get_pending_reports()
    report = next((r for r in reports if r['id'] == report_id), None)
    
    if not report:
        await callback.answer("Shikoyat topilmadi")
        return
    
    text = f"""
⚠️ Shikoyat #{report['id']}

Shikoyatchi: {report['reporter_name']} (@{report['reporter_username']})
Ayblanuvchi: {report['reported_name']} (@{report['reported_username']})

Sabab: {report['reason']}
Tafsilot: {report['details'] or '-'}

Amal tanlang:
"""
    
    keyboard = get_report_actions_keyboard(report_id, report['reported_id'])
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("ban_"))
async def ban_user(callback: CallbackQuery):
    """Foydalanuvchini ban qilish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q")
        return
    
    parts = callback.data.split("_")
    user_id = int(parts[1])
    duration = parts[2]  # "7" yoki "permanent"
    
    await db.ban_user(user_id, callback.from_user.id, f"Ban: {duration}")
    
    await callback.message.edit_text(BAN_SUCCESS_MESSAGE)


@router.callback_query(F.data.startswith("warn_"))
async def warn_user(callback: CallbackQuery):
    """Ogohlantirish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q")
        return
    
    user_id = int(callback.data.split("_")[1])
    
    # Ogohlantirishni yuborish
    try:
        await callback.bot.send_message(
            user_id,
            "⚠️ OGOHLANTIRISH\n\nSizga shikoyat qilingan. Bot qoidalariga rioya qiling, aks holda hisobingiz bloklanadi."
        )
        await callback.message.edit_text("✅ Ogohlantirish yuborildi")
    except:
        await callback.message.edit_text("❌ Xabar yuborilmadi (foydalanuvchi botni to'xtatgan)")


@router.callback_query(F.data.startswith("dismiss_report_"))
async def dismiss_report(callback: CallbackQuery):
    """Shikoyatni rad etish"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q")
        return
    
    report_id = int(callback.data.split("_")[2])
    
    # Shikoyatni rad etish
    # await db.update_report_status(report_id, 'dismissed')
    
    await callback.message.edit_text("✅ Shikoyat rad etildi")


@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    """Umumiy xabar yuborishni boshlash"""
    if not is_admin(callback.from_user.id):
        await callback.answer("❌ Sizda admin huquqi yo'q")
        return
    
    await callback.message.edit_text(BROADCAST_PROMPT_MESSAGE)
    await state.set_state(AdminStates.broadcast_message)


@router.message(AdminStates.broadcast_message)
async def send_broadcast(message: Message, state: FSMContext):
    """Umumiy xabarni yuborish"""
    if not is_admin(message.from_user.id):
        await message.answer("❌ Sizda admin huquqi yo'q")
        return
    
    broadcast_text = message.text
    
    # Barcha foydalanuvchilarni olish
    users = await db.search_users(status='active')
    
    success_count = 0
    
    for user in users:
        try:
            await message.bot.send_message(user['telegram_id'], f"📢 XABAR\n\n{broadcast_text}")
            success_count += 1
        except:
            pass  # Yuborilmasa o'tkazib yuborish
    
    await state.clear()
    await message.answer(BROADCAST_SUCCESS_MESSAGE.format(count=success_count))


@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Admin panelga qaytish"""
    await callback.message.edit_text(
        ADMIN_MENU_MESSAGE,
        reply_markup=get_admin_keyboard()
    )


# Ban/Unban buyruqlari
@router.message(Command("ban"))
async def cmd_ban_user(message: Message):
    """Ban buyrug'i"""
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Noto'g'ri format. Misol: /ban 123456789")
        return
    
    try:
        user_id = int(args[1])
        await db.ban_user(user_id, message.from_user.id, "Manual ban")
        await message.answer(BAN_SUCCESS_MESSAGE)
    except:
        await message.answer("❌ Xato. User ID ni tekshiring")


@router.message(Command("unban"))
async def cmd_unban_user(message: Message):
    """Unban buyrug'i"""
    if not is_admin(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("❌ Noto'g'ri format. Misol: /unban 123456789")
        return
    
    try:
        user_id = int(args[1])
        await db.unban_user(user_id, message.from_user.id)
        await message.answer(UNBAN_SUCCESS_MESSAGE)
    except:
        await message.answer("❌ Xato. User ID ni tekshiring")