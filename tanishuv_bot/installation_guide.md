# 📚 O'rnatish bo'yicha batafsil qo'llanma

## 📋 Mundarija
1. [Tizim talablari](#-tizim-talablari)
2. [Python o'rnatish](#-python-ornatish)
3. [PostgreSQL o'rnatish](#-postgresql-ornatish)
4. [Loyihani sozlash](#-loyihani-sozlash)
5. [Bot yaratish](#-bot-yaratish)
6. [Ishga tushirish](#-ishga-tushirish)
7. [Tez-tez uchraydigan xatolar](#-tez-tez-uchraydigan-xatolar)

---

## 🖥 Tizim talablari

- **OS**: Windows 10/11, Linux (Ubuntu 20.04+), macOS
- **RAM**: Minimum 2GB (4GB tavsiya etiladi)
- **Disk**: 500MB bo'sh joy
- **Internet**: Tezkor aloqa

---

## 🐍 Python o'rnatish

### Windows:

1. https://www.python.org/downloads/ ga o'ting
2. **Python 3.11** yoki undan yuqori versiyani yuklab oling
3. O'rnatish jarayonida:
   - ✅ "Add Python to PATH" ni belgilang
   - "Install Now" ni bosing

4. Tekshirish (CMD yoki PowerShell):
```cmd
python --version
```
Natija: `Python 3.11.x` ko'rinishi kerak

### Linux (Ubuntu/Debian):

```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

Tekshirish:
```bash
python3 --version
```

### macOS:

```bash
# Homebrew orqali
brew install python@3.11
```

---

## 🐘 PostgreSQL o'rnatish

### Windows:

1. https://www.postgresql.org/download/windows/ dan yuklab oling
2. Installer ni ishga tushiring
3. O'rnatish sozlamalari:
   - Port: `5432` (standart)
   - Superuser parol: **eslab qoling!** (masalan: `postgres`)
   - Locale: `Default`

4. pgAdmin 4 avtomatik o'rnatiladi

5. Database yaratish:
   - pgAdmin 4 ni oching
   - Servers → PostgreSQL → Databases → o'ng tugma → Create → Database
   - Database name: `tanishuv_bot`
   - Save

### Linux (Ubuntu/Debian):

```bash
# PostgreSQL o'rnatish
sudo apt update
sudo apt install postgresql postgresql-contrib

# PostgreSQL ishga tushirish
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Database yaratish
sudo -u postgres psql
CREATE DATABASE tanishuv_bot;
\q
```

### macOS:

```bash
# Homebrew orqali
brew install postgresql@15
brew services start postgresql@15

# Database yaratish
createdb tanishuv_bot
```

---

## 📦 Loyihani sozlash

### 1. Git o'rnatish (agar yo'q bo'lsa)

**Windows:**
- https://git-scm.com/download/win

**Linux:**
```bash
sudo apt install git
```

### 2. Loyihani klonlash

```bash
git clone https://github.com/yourusername/tanishuv-bot.git
cd tanishuv-bot
```

Yoki ZIP faylini yuklab olib, ochib oling.

### 3. Virtual muhit yaratish

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate
```

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

Agar xato chiqsa:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Virtual muhit faollashganda `(venv)` ko'rinadi:
```
(venv) C:\tanishuv-bot>
```

### 4. Kutubxonalarni o'rnatish

```bash
pip install -r requirements.txt
```

Bu 1-2 daqiqa davom etishi mumkin.

---

## 🤖 Bot yaratish

### 1. BotFather ga borish

Telegram da [@BotFather](https://t.me/BotFather) ni toping

### 2. Bot yaratish

```
/newbot
```

Bot nomi:
```
Tanishuv Bot
```

Bot username (noyob bo'lishi kerak):
```
tanishuv_uz_bot
```

### 3. Tokenni saqlash

BotFather token beradi:
```
123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

**⚠️ Bu tokenni hech kimga ko'rsatmang!**

### 4. Admin ID ni topish

[@userinfobot](https://t.me/userinfobot) ga `/start` yuboring

Natija:
```
Your ID: 123456789
```

Bu sizning admin ID ingiz.

---

## ⚙️ Environment sozlash

### 1. .env faylini yaratish

**Windows Explorer:**
- Loyiha papkasida yangi fayl yarating: `.env`
- Agar kengaytma ko'rinmasa: View → File name extensions

**CMD/Terminal:**
```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/macOS
```

### 2. .env ni tahrirlash

Notepad yoki VSCode da oching:

```env
# Bot sozlamalari
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
ADMIN_IDS=123456789

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=tanishuv_bot
DB_USER=postgres
DB_PASSWORD=postgres

# Limitlar (o'zgartirish ixtiyoriy)
MAX_DAILY_SWIPES_FREE=10
MAX_DAILY_SWIPES_PREMIUM=50
MAX_MESSAGES_PER_DAY=50
```

**⚠️ Muhim:**
- `BOT_TOKEN` - BotFather dan olgan token
- `ADMIN_IDS` - userinfobot dan olgan ID
- `DB_PASSWORD` - PostgreSQL parolingiz

---

## 🚀 Ishga tushirish

### 1. PostgreSQL ishlab turganini tekshiring

**Windows:**
1. `services.msc` ni oching (Win+R)
2. `postgresql-x64-15` qatorini toping
3. Status: `Running` bo'lishi kerak

**Linux:**
```bash
sudo systemctl status postgresql
```

Agar ishlamasa:
```bash
sudo systemctl start postgresql
```

### 2. Database ulanishini tekshiring

Python interpreter oching:
```bash
python
```

Test qiling:
```python
import asyncpg
import asyncio

async def test():
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        database='tanishuv_bot',
        user='postgres',
        password='postgres'  # Sizning parolingiz
    )
    print("✅ Database ulandi!")
    await conn.close()

asyncio.run(test())
```

Agar xato chiqsa, parol yoki database nomini tekshiring.

### 3. Botni ishga tushirish

```bash
python bot.py
```

**Kutilgan natija:**
```
INFO - ✅ Database ulandi
INFO - 🚀 Bot ishga tushdi!
INFO - 👤 Admin IDs: [123456789]
```

### 4. Botni test qilish

1. Telegram da botingizni oching
2. `/start` ni yuboring
3. Ro'yxatdan o'tishni boshlang

---

## 🔧 Tez-tez uchraydigan xatolar

### ❌ `No module named 'aiogram'`

**Sabab:** Kutubxonalar o'rnatilmagan yoki virtual muhit faollashtirilmagan

**Yechim:**
```bash
# Virtual muhitni faollashtiring
venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/macOS

# Qayta o'rnating
pip install -r requirements.txt
```

### ❌ `connection refused` (PostgreSQL)

**Sabab:** PostgreSQL ishlamayapti

**Yechim:**

**Windows:**
```
services.msc → postgresql-x64-15 → Start
```

**Linux:**
```bash
sudo systemctl start postgresql
```

### ❌ `Unauthorized` (Bot token)

**Sabab:** Noto'g'ri token

**Yechim:**
1. `.env` faylini oching
2. `BOT_TOKEN` ni tekshiring
3. BotFather da `/mybots` → botingiz → API Token

### ❌ `password authentication failed`

**Sabab:** Noto'g'ri PostgreSQL parol

**Yechim:**

**Windows (parolni reset qilish):**
1. `C:\Program Files\PostgreSQL\15\data\pg_hba.conf` ni oching
2. `md5` ni `trust` ga o'zgartiring
3. PostgreSQL ni restart qiling
4. Yangi parol o'rnating:
```sql
ALTER USER postgres PASSWORD 'yangi_parol';
```
5. `pg_hba.conf` ni qaytaring
6. `.env` dagi `DB_PASSWORD` ni yangilang

**Linux:**
```bash
sudo -u postgres psql
ALTER USER postgres PASSWORD 'yangi_parol';
\q
```

### ❌ Emoji ko'rinmaydi

**Sabab:** Terminal encoding muammosi

**Yechim:**

**Windows CMD:**
```cmd
chcp 65001
```

**PowerShell:**
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

**VSCode:**
File → Preferences → Settings → Terminal Encoding → utf8

---

## 🎯 Keyingi qadamlar

✅ Bot ishga tushdi!

Endi:
1. Botni test qiling
2. Admin panel tekshiring: `/admin`
3. Premium funksiyalarni sozlang
4. Production uchun deploy qiling

---

## 📞 Yordam kerakmi?

- **Telegram:** [@yourusername](https://t.me/yourusername)
- **Email:** your.email@example.com
- **Issues:** GitHub Issues bo'limi

---

**Omad! 🚀**