from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Bosh menyu"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔍 Moslik topish")],
            [KeyboardButton(text="👤 Profilim"), KeyboardButton(text="💬 Suhbatlar")],
            [KeyboardButton(text="🧭 Rejimlar"), KeyboardButton(text="⭐ Premium")],
            [KeyboardButton(text="ℹ️ Ma'lumot"), KeyboardButton(text="⚙️ Sozlamalar")],
        ],
        resize_keyboard=True
    )
    return keyboard


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Start tugmasi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🚀 Boshlash", callback_data="start_onboarding")]
        ]
    )
    return keyboard


def get_mode_keyboard() -> InlineKeyboardMarkup:
    """Rejim tanlash"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🕌 Nikoh", callback_data="mode_nikoh")],
            [InlineKeyboardButton(text="👥 Do'st", callback_data="mode_dost")],
            [InlineKeyboardButton(text="🎓 Talaba", callback_data="mode_talaba")],
        ]
    )
    return keyboard


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Jins tanlash"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👨 Erkak", callback_data="gender_erkak")],
            [InlineKeyboardButton(text="👩 Ayol", callback_data="gender_ayol")],
        ]
    )
    return keyboard


def get_city_keyboard(cities: list) -> InlineKeyboardMarkup:
    """Shahar tanlash"""
    buttons = []
    for i in range(0, len(cities), 2):
        row = []
        row.append(InlineKeyboardButton(text=cities[i], callback_data=f"city_{cities[i]}"))
        if i + 1 < len(cities):
            row.append(InlineKeyboardButton(text=cities[i+1], callback_data=f"city_{cities[i+1]}"))
        buttons.append(row)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_skip_keyboard() -> InlineKeyboardMarkup:
    """O'tkazish tugmasi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭ O'tkazish", callback_data="skip")]
        ]
    )
    return keyboard


def get_confirm_rules_keyboard() -> InlineKeyboardMarkup:
    """Qoidalarni tasdiqlash"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Roziman", callback_data="confirm_rules")]
        ]
    )
    return keyboard


def get_looking_for_gender_keyboard() -> InlineKeyboardMarkup:
    """Qidiruv jinsi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👨 Erkak", callback_data="looking_erkak")],
            [InlineKeyboardButton(text="👩 Ayol", callback_data="looking_ayol")],
            [InlineKeyboardButton(text="🤷 Farqi yo'q", callback_data="looking_farqi_yoq")],
        ]
    )
    return keyboard


def get_distance_keyboard() -> InlineKeyboardMarkup:
    """Masofa radiusi"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📍 5 km", callback_data="distance_5")],
            [InlineKeyboardButton(text="📍 20 km", callback_data="distance_20")],
            [InlineKeyboardButton(text="📍 50 km", callback_data="distance_50")],
            [InlineKeyboardButton(text="🌍 Butun mamlakat", callback_data="distance_all")],
        ]
    )
    return keyboard