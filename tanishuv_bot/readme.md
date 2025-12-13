# 💝 Tanishuv Telegram Bot

O'zbekiston uchun mo'ljallangan tanishuv va do'stlik Telegram boti. Uchta rejim: Nikoh, Do'st, Talaba.

## 🌟 Xususiyatlar

### 👥 Uchta rejim
- **🕌 Nikoh** - Jiddiy munosabat va oila qurish
- **👥 Do'st** - Do'stlik va suhbatdosh topish  
- **🎓 Talaba** - Talaba do'stlar bilan tanishuv

### ⚡ Asosiy funksiyalar
- ✅ To'liq ro'yxatdan o'tish (onboarding)
- 🔍 Moslik topish (matching) tizimi
- 💬 Real-time suhbat
- 👤 Profil boshqaruvi
- ⭐ Premium obuna
- 🎯 Keng qidiruv filtrlari
- 📊 Admin panel

### 🔒 Xavfsizlik
- 18+ majburiy
- Shikoyat tizimi
- Bloklash imkoniyati
- Admin nazorati

## 📁 Loyiha strukturasi

```
tanishuv_bot/
│
├── bot.py                 # Asosiy bot fayli
├── config.py              # Konfiguratsiya
├── database.py            # Database bilan ishlash
├── states.py              # FSM holatlari
├── requirements.txt       # Kerakli kutubxonalar
├── .env                   # Muhit o'zgaruvchilari
├── .env.example          # .env namunasi
├── docker-compose.yml    # Docker
├── Dockerfile
├── .gitignore
└── README.md
│
├── handlers/              # Handler funksiyalar
│   ├── __init__.py
│   ├── start.py          # Start va onboarding
│   ├── profile.py        # Profil boshqaruvi
│   ├── matching.py       # Moslik topish
│   ├── chat.py           # Suhbatlar
│   ├── premium.py        # Premium
│   ├── settings.py       # Sozlamalar
│   ├── admin.py          # Admin panel
│   └── help.py           # Yordam
│
├── keyboards/             # Klaviaturalar
│   ├── __init__.py
│   ├── main_menu.py      # Asosiy menyu
│   ├── matching.py       # Moslik topish
│   └── admin.py          # Admin
│
├── utils/                 # Yordamchi funksiyalar
│   ├── __init__.py
│   ├── filters.py        # Filtrlash
│   ├── validators.py     # Validatsiya
│   └── helpers.py        # Boshqa funksiyalar
│
└── texts/                 # Matnlar
    ├── __init__.py
    └── messages.py        # Bot matnlari
```

## 🚀 O'rnatish

### 1. Talablar
- Python 3.10+
- PostgreSQL 13+
- Git

### 2. Klonlash
```bash
git clone https://github.com/yourusername/tanishuv-bot.git
cd tanishuv-bot
```

### 3. Virtual muhit
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 4. Kutubxonalarni o'rnatish
```bash
pip install -r requirements.txt
```

### 5. PostgreSQL sozlash

#### Windows:
1. https://www.postgresql.org/download/windows/ dan yuklab oling
2. O'rnatish jarayonida parol o'rnating
3. pgAdmin orqali yangi database yarating:
   ```sql
   CREATE DATABASE tanishuv_bot;
   ```

#### Linux:
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo -u postgres psql
CREATE DATABASE tanishuv_bot;
\q
```

### 6. Environment sozlash
`.env` faylini yarating va to'ldiring:

```bash
cp .env.example .env
nano .env  # yoki boshqa editor
```

`.env` fayli:
```env
# Bot
BOT_TOKEN=123456:ABC-DEF...  # @BotFather dan
ADMIN_IDS=123456789          # @userinfobot dan

# Database  
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tanishuv_bot
DB_USER=postgres
DB_PASSWORD=your_password

# Limitlar (ixtiyoriy)
MAX_DAILY_SWIPES_FREE=10
MAX_DAILY_SWIPES_PREMIUM=50
```

### 7. Botni ishga tushirish
```bash
python bot.py
```

Agar hammasi to'g'ri bo'lsa:
```
INFO - ✅ Database ulandi
INFO - 🚀 Bot ishga tushdi!
INFO - 👤 Admin IDs: [123456789]
```

## 🐳 Docker bilan ishga tushirish

```bash
# Build va run
docker-compose up -d

# Loglarni ko'rish
docker-compose logs -f bot

# To'xtatish
docker-compose down
```

## 📝 Foydalanish

### Foydalanuvchi uchun:
1. Botni ishga tushiring: `/start`
2. Rejim tanlang (Nikoh/Do'st/Talaba)
3. Shaxsiy ma'lumotlar kiriting
4. Qidiruv parametrlarini sozlang
5. Moslik topishni boshlang: `🔍 Moslik topish`

### Admin uchun:
- Admin panel: `/admin`
- Statistika: `📊 Statistika`
- Foydalanuvchilar: `👥 Foydalanuvchilar`
- Shikoyatlar: `⚠️ Shikoyatlar`
- Ban: `/ban [telegram_id]`
- Unban: `/unban [telegram_id]`

## 🛠 Texnologiyalar

- **Bot Framework**: aiogram 3.x
- **Database**: PostgreSQL + asyncpg
- **FSM**: aiogram FSM
- **Environment**: python-dotenv
- **Containerization**: Docker

## 📊 Database sxemasi

### Asosiy jadvallar:
- `users` - Foydalanuvchilar
- `nikoh_profiles` - Nikoh profillari
- `dost_profiles` - Do'st profillari  
- `talaba_profiles` - Talaba profillari
- `search_preferences` - Qidiruv parametrlari
- `likes` - Yoqtirishlar
- `matches` - Mosliklar
- `messages` - Xabarlar
- `blocks` - Bloklar
- `reports` - Shikoyatlar
- `premium_transactions` - Premium to'lovlar

## 🔧 Xatolarni bartaraf etish

### Database ulanish xatosi
```
Error: connection refused
```
**Yechim:** PostgreSQL ishga tushganini tekshiring
```bash
# Windows: services.msc
# Linux:
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### Import xatosi
```
ModuleNotFoundError: No module named 'aiogram'
```
**Yechim:**
```bash
pip install -r requirements.txt
```

### Bot token xatosi
```
Unauthorized
```
**Yechim:** `.env` faylidagi `BOT_TOKEN` ni tekshiring

### Emoji ko'rinmasligi
**Yechim:** Terminal encoding UTF-8 ga o'zgartiring

## 📈 Keyingi qadamlar

- [ ] To'lov tizimi integratsiyasi
- [ ] SMS tasdiqlash
- [ ] Geolokatsiya
- [ ] Voice xabarlar
- [ ] Video call
- [ ] AI-powered matching
- [ ] Mobile ilovalar

## 🤝 Hissa qo'shish

Pull request'lar qabul qilinadi! Katta o'zgarishlar uchun avval issue oching.

## 📄 Litsenziya

MIT License - [LICENSE](LICENSE) faylini ko'ring

## 📞 Aloqa

- **Developer**: [@yourusername](https://t.me/yourusername)
- **Email**: your.email@example.com
- **Website**: https://yourwebsite.com

## ⚠️ Disclaimer

Bu bot faqat ta'lim maqsadida yaratilgan. Ishlatishdan oldin o'z mas'uliyatingizni tushunib oling.

---

Made with ❤️ in Uzbekistan