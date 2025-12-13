import os
from dotenv import load_dotenv

load_dotenv()

# ==================== BOT ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN topilmadi! .env faylni tekshiring")

ADMIN_IDS = [int(id.strip()) for id in os.getenv("ADMIN_IDS", "").split(",") if id.strip()]

# ==================== DATABASE ====================
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "database": os.getenv("DB_NAME", "tanishuv_bot"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", ""),
}

# ==================== REDIS ====================
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# ==================== LIMITS ====================
# Free foydalanuvchi limitlari
MAX_DAILY_SWIPES_FREE = int(os.getenv("MAX_DAILY_SWIPES_FREE", 10))
MAX_MESSAGES_PER_DAY_FREE = int(os.getenv("MAX_MESSAGES_PER_DAY_FREE", 30))
MAX_STORIES_FREE = int(os.getenv("MAX_STORIES_FREE", 1))

# Premium foydalanuvchi limitlari
MAX_DAILY_SWIPES_PREMIUM = int(os.getenv("MAX_DAILY_SWIPES_PREMIUM", 100))
MAX_MESSAGES_PER_DAY_PREMIUM = int(os.getenv("MAX_MESSAGES_PER_DAY_PREMIUM", 200))
MAX_STORIES_PREMIUM = int(os.getenv("MAX_STORIES_PREMIUM", 5))

# VIP foydalanuvchi limitlari
MAX_DAILY_SWIPES_VIP = int(os.getenv("MAX_DAILY_SWIPES_VIP", -1))  # -1 = cheksiz
MAX_MESSAGES_PER_DAY_VIP = int(os.getenv("MAX_MESSAGES_PER_DAY_VIP", -1))
MAX_STORIES_VIP = int(os.getenv("MAX_STORIES_VIP", 10))

# ==================== PREMIUM NARXLARI ====================
PREMIUM_PRICES = {
    "premium_week": 19000,      # 1 hafta
    "premium_month": 49000,     # 1 oy
    "premium_3months": 129000,  # 3 oy
    "vip_month": 99000,         # VIP 1 oy
    "vip_year": 999000,         # VIP 1 yil
}

# Virtual sovg'alar narxlari
GIFT_PRICES = {
    "rose": 5000,           # 🌹 Gul
    "heart": 10000,         # ❤️ Yurak
    "cake": 15000,          # 🎂 Tort
    "diamond": 25000,       # 💎 Olmos
    "crown": 50000,         # 👑 Toj
}

# ==================== PAYMENT ====================
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN", "")

# ==================== STORIES ====================
STORY_DURATION_HOURS = 24  # Story necha soat ko'rinadi
MAX_STORY_FILE_SIZE_MB = 10  # Max fayl hajmi (MB)

# ==================== VERIFICATION ====================
VERIFICATION_REQUIRED_FOR_PREMIUM = True  # Premium olish uchun verification kerakmi
MIN_AGE_FOR_VERIFICATION = 18  # Minimal yosh

# ==================== MATCHING ====================
DEFAULT_DISTANCE_KM = 50  # Default qidiruv masofasi
MAX_DISTANCE_KM = 500     # Maksimal qidiruv masofasi

# ==================== SHAHARLAR ====================
CITIES = [
    "Toshkent", "Samarqand", "Buxoro", "Andijon", "Namangan",
    "Farg'ona", "Qo'qon", "Qarshi", "Termiz", "Urganch",
    "Nukus", "Guliston", "Jizzax", "Navoiy", "Xiva",
    "Marg'ilon", "Shahrisabz", "Denov", "Oltiariq"
]

# ==================== QIZIQISHLAR ====================
INTERESTS = [
    "⚽ Sport", "🎵 Musiqa", "✈️ Sayohat", "💻 Texnologiya", 
    "🎨 San'at", "📚 Kitob", "🎬 Kino", "🍕 Ovqat", 
    "👗 Moda", "💼 Biznes", "🎮 O'yin", "📸 Fotosurat",
    "🏋️ Fitnes", "🧘 Yoga", "🎭 Teatr", "🎪 Konsert"
]

# ==================== DINLAR ====================
RELIGIONS = ["Musulmon", "Xristian", "Buddist", "Ateist", "Boshqa"]

# ==================== TA'LIM ====================
EDUCATION_LEVELS = [
    "O'rta", "O'rta maxsus", "To'liqsiz oliy", 
    "Oliy (Bakalavr)", "Magistr", "Doktor (PhD)"
]

# ==================== TILLAR ====================
LANGUAGES = [
    "O'zbek", "Rus", "Ingliz", "Turk", 
    "Arab", "Fors", "Xitoy", "Koreys"
]

# ==================== UNIVERSITETLAR ====================
UNIVERSITIES = [
    "TDIU", "O'zMU", "TATU", "TDTU", "SamDU",
    "BuxDU", "AndDU", "NamDU", "FarDU", "QarDU",
    "UrDU", "NukDU", "TDPU", "UzGJTU", "TIIAME"
]

# ==================== ICEBREAKER SAVOLLAR ====================
ICEBREAKER_QUESTIONS = [
    "Eng sevimli ovqatingiz nima?",
    "Qaysi mamlakatga sayohat qilishni xohlaysiz?",
    "Eng yaxshi ko'rgan filmingiz?",
    "Dam olish kunlarini qanday o'tkazasiz?",
    "Eng katta orzuingiz nima?",
    "Qaysi musiqani tinglaysiz?",
    "Yoshligingizda kim bo'lishni orzu qilgansiz?",
    "Ideal dam olish joyingiz qaysi?",
    "Sevimli fasl qaysi va nega?",
    "Bir kunlik super qudrat olsangiz nima bo'lardi?",
]

# ==================== SHIKOYAT SABABLARI ====================
REPORT_REASONS = {
    "fake": "Soxta profil",
    "inappropriate": "Nomaqbul xatti-harakat",
    "spam": "Spam/Reklama",
    "harassment": "Ta'qib qilish",
    "underage": "18 yoshdan kichik",
    "scam": "Firibgarlik",
    "other": "Boshqa sabab"
}

# ==================== FILE PATHS ====================
PHOTOS_DIR = "photos"
VOICES_DIR = "voices"
STORIES_DIR = "stories"
TEMP_DIR = "temp"

# Papkalarni yaratish
for directory in [PHOTOS_DIR, VOICES_DIR, STORIES_DIR, TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)

# ==================== FEATURE FLAGS ====================
FEATURES = {
    "stories_enabled": True,
    "voice_messages_enabled": True,
    "verification_enabled": True,
    "gifts_enabled": True,
    "icebreaker_enabled": True,
    "geolocation_enabled": False,  # Keyinroq qo'shamiz
    "video_call_enabled": False,   # Keyinroq qo'shamiz
}

# ==================== TEKSHIRISH ====================
def validate_config():
    """Konfiguratsiya to'g'riligini tekshirish"""
    errors = []
    
    if not BOT_TOKEN:
        errors.append("BOT_TOKEN mavjud emas")
    
    if not ADMIN_IDS:
        errors.append("ADMIN_IDS mavjud emas")
    
    if not DB_CONFIG.get("password"):
        errors.append("DB_PASSWORD mavjud emas")
    
    if errors:
        raise ValueError(f"Konfiguratsiya xatolari: {', '.join(errors)}")

# Config yuklanganda tekshirish
if __name__ != "__main__":
    try:
        validate_config()
    except ValueError as e:
        print(f"[ERROR] {e}")
        print("[INFO] .env faylni to'ldiring va qayta urinib ko'ring")