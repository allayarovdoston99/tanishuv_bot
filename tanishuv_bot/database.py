import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import config


class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Database bilan ulanish"""
        self.pool = await asyncpg.create_pool(**config.DB_CONFIG)
        await self._create_tables()

    async def disconnect(self):
        """Ulanishni yopish"""
        if self.pool:
            await self.pool.close()

    async def _create_tables(self):
        """Jadvallarni yaratish"""
        async with self.pool.acquire() as conn:
            # Users jadvali
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    telegram_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(100),
                    full_name VARCHAR(200) NOT NULL,
                    birth_year INTEGER NOT NULL CHECK (birth_year <= EXTRACT(YEAR FROM CURRENT_DATE) - 18),
                    gender VARCHAR(10) NOT NULL CHECK (gender IN ('erkak', 'ayol')),
                    city VARCHAR(100) NOT NULL,
                    bio TEXT,
                    photo_file_id VARCHAR(200),
                    photo_verified BOOLEAN DEFAULT FALSE,
                    mode VARCHAR(20) NOT NULL CHECK (mode IN ('nikoh', 'dost', 'talaba')),
                    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'pause', 'banned')),
                    is_premium BOOLEAN DEFAULT FALSE,
                    premium_until TIMESTAMP,
                    profile_views INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Indexlar
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_mode ON users(mode)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)")

            # Nikoh profillari
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS nikoh_profiles (
                    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    religion VARCHAR(50),
                    occupation VARCHAR(100),
                    education VARCHAR(100),
                    marital_status VARCHAR(50),
                    children VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Do'st profillari
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS dost_profiles (
                    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    interests TEXT[],
                    languages TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Talaba profillari
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS talaba_profiles (
                    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    university VARCHAR(200),
                    faculty VARCHAR(200),
                    course INTEGER CHECK (course BETWEEN 1 AND 6),
                    academic_interests TEXT[],
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Qidiruv parametrlari
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS search_preferences (
                    user_id BIGINT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                    looking_for_gender VARCHAR(20) CHECK (looking_for_gender IN ('erkak', 'ayol', 'farqi_yoq')),
                    age_min INTEGER CHECK (age_min >= 18),
                    age_max INTEGER CHECK (age_max <= 100),
                    distance_km INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Likes
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS likes (
                    id BIGSERIAL PRIMARY KEY,
                    liker_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    liked_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(liker_id, liked_id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_likes_liker ON likes(liker_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_likes_liked ON likes(liked_id)")

            # Matches
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id BIGSERIAL PRIMARY KEY,
                    user1_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    user2_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    CHECK (user1_id < user2_id),
                    UNIQUE(user1_id, user2_id)
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_user1 ON matches(user1_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_user2 ON matches(user2_id)")

            # Messages
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id BIGSERIAL PRIMARY KEY,
                    match_id BIGINT NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
                    sender_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    receiver_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    message_text TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_match ON messages(match_id)")

            # Blocks
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS blocks (
                    id BIGSERIAL PRIMARY KEY,
                    blocker_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    blocked_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(blocker_id, blocked_id)
                )
            """)

            # Reports
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS reports (
                    id BIGSERIAL PRIMARY KEY,
                    reporter_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    reported_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    reason VARCHAR(50) NOT NULL,
                    details TEXT,
                    status VARCHAR(20) DEFAULT 'pending',
                    reviewed_by BIGINT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Premium transactions
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS premium_transactions (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    package VARCHAR(20) NOT NULL,
                    amount INTEGER NOT NULL,
                    payment_provider VARCHAR(50) DEFAULT 'telegram_stars',
                    payment_id VARCHAR(200) UNIQUE,
                    status VARCHAR(20) DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Admin actions
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_actions (
                    id BIGSERIAL PRIMARY KEY,
                    admin_id BIGINT NOT NULL,
                    action VARCHAR(50) NOT NULL,
                    target_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Stories (24 soatlik hikoyalar)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS stories (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    file_id VARCHAR(200) NOT NULL,
                    file_type VARCHAR(20) NOT NULL CHECK (file_type IN ('photo', 'video')),
                    caption TEXT,
                    views_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP DEFAULT (CURRENT_TIMESTAMP + INTERVAL '24 hours')
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_stories_user ON stories(user_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_stories_expires ON stories(expires_at)")

            # Story Views (kim ko'rdi)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS story_views (
                    id BIGSERIAL PRIMARY KEY,
                    story_id BIGINT NOT NULL REFERENCES stories(id) ON DELETE CASCADE,
                    viewer_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(story_id, viewer_id)
                )
            """)

            # Sent Gifts (yuborilgan sovg'alar)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS sent_gifts (
                    id BIGSERIAL PRIMARY KEY,
                    sender_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    receiver_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    gift_type VARCHAR(50) NOT NULL,
                    amount INTEGER NOT NULL,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_gifts_sender ON sent_gifts(sender_id)")
            await conn.execute("CREATE INDEX IF NOT EXISTS idx_gifts_receiver ON sent_gifts(receiver_id)")

            # Daily Limits (kunlik limitlar)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_limits (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    limit_type VARCHAR(50) NOT NULL,
                    count INTEGER DEFAULT 0,
                    date DATE DEFAULT CURRENT_DATE,
                    UNIQUE(user_id, limit_type, date)
                )
            """)

    # ============ USER METHODS ============

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict]:
        """Telegram ID orqali foydalanuvchi"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE telegram_id = $1",
                telegram_id
            )
            return dict(row) if row else None

    async def create_user(self, telegram_id: int, username: str, full_name: str,
                         birth_year: int, gender: str, city: str, mode: str) -> int:
        """Yangi foydalanuvchi yaratish"""
        async with self.pool.acquire() as conn:
            user_id = await conn.fetchval("""
                INSERT INTO users (telegram_id, username, full_name, birth_year, gender, city, mode)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                RETURNING id
            """, telegram_id, username, full_name, birth_year, gender, city, mode)
            return user_id

    async def update_user(self, user_id: int, **kwargs):
        """Foydalanuvchi ma'lumotlarini yangilash"""
        if not kwargs:
            return
        
        fields = ", ".join([f"{k} = ${i+2}" for i, k in enumerate(kwargs.keys())])
        query = f"UPDATE users SET {fields} WHERE id = $1"
        
        async with self.pool.acquire() as conn:
            await conn.execute(query, user_id, *kwargs.values())

    async def get_user_profile_data(self, user_id: int) -> Dict:
        """To'liq profil ma'lumotlari"""
        async with self.pool.acquire() as conn:
            user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            if not user:
                return None
            
            user_dict = dict(user)
            mode = user_dict['mode']
            
            # Rejimga mos profil
            if mode == 'nikoh':
                profile = await conn.fetchrow(
                    "SELECT * FROM nikoh_profiles WHERE user_id = $1", user_id
                )
            elif mode == 'dost':
                profile = await conn.fetchrow(
                    "SELECT * FROM dost_profiles WHERE user_id = $1", user_id
                )
            elif mode == 'talaba':
                profile = await conn.fetchrow(
                    "SELECT * FROM talaba_profiles WHERE user_id = $1", user_id
                )
            else:
                profile = None
            
            user_dict['profile'] = dict(profile) if profile else {}
            
            # Qidiruv parametrlari
            prefs = await conn.fetchrow(
                "SELECT * FROM search_preferences WHERE user_id = $1", user_id
            )
            user_dict['search_prefs'] = dict(prefs) if prefs else {}
            
            return user_dict

    # ============ PROFILE METHODS ============

    async def create_nikoh_profile(self, user_id: int, religion: str, occupation: str,
                                   education: str, marital_status: str, children: str):
        """Nikoh profili yaratish"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO nikoh_profiles (user_id, religion, occupation, education, marital_status, children)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, user_id, religion, occupation, education, marital_status, children)

    async def create_dost_profile(self, user_id: int, interests: List[str], languages: List[str]):
        """Do'st profili yaratish"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO dost_profiles (user_id, interests, languages)
                VALUES ($1, $2, $3)
            """, user_id, interests, languages)

    async def create_talaba_profile(self, user_id: int, university: str, faculty: str, course: int):
        """Talaba profili yaratish"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO talaba_profiles (user_id, university, faculty, course)
                VALUES ($1, $2, $3, $4)
            """, user_id, university, faculty, course)

    async def create_search_preferences(self, user_id: int, gender: str, age_min: int,
                                       age_max: int, distance_km: Optional[int]):
        """Qidiruv parametrlarini saqlash"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO search_preferences (user_id, looking_for_gender, age_min, age_max, distance_km)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) DO UPDATE
                SET looking_for_gender = $2, age_min = $3, age_max = $4, distance_km = $5, updated_at = CURRENT_TIMESTAMP
            """, user_id, gender, age_min, age_max, distance_km)

    # ============ MATCHING METHODS ============

    async def get_potential_matches(self, user_id: int, limit: int = 1) -> List[Dict]:
        """Mos keladigan profillarni topish"""
        async with self.pool.acquire() as conn:
            # Foydalanuvchi ma'lumotlari
            user = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
            prefs = await conn.fetchrow("SELECT * FROM search_preferences WHERE user_id = $1", user_id)
            
            if not user or not prefs:
                return []
            
            current_year = datetime.now().year
            user_age = current_year - user['birth_year']
            
            # Mos profillarni topish
            query = """
                SELECT u.*, 
                       (EXTRACT(YEAR FROM CURRENT_DATE) - u.birth_year) as age
                FROM users u
                WHERE u.id != $1
                AND u.mode = $2
                AND u.status = 'active'
                AND (EXTRACT(YEAR FROM CURRENT_DATE) - u.birth_year) BETWEEN $3 AND $4
                AND ($5 = 'farqi_yoq' OR u.gender = $5)
                AND u.id NOT IN (SELECT liked_id FROM likes WHERE liker_id = $1)
                AND u.id NOT IN (SELECT blocked_id FROM blocks WHERE blocker_id = $1)
                AND u.id NOT IN (SELECT blocker_id FROM blocks WHERE blocked_id = $1)
                ORDER BY u.is_premium DESC, u.last_active DESC, u.profile_views ASC
                LIMIT $6
            """
            
            rows = await conn.fetch(
                query,
                user_id,
                user['mode'],
                prefs['age_min'],
                prefs['age_max'],
                prefs['looking_for_gender'],
                limit
            )
            
            return [dict(row) for row in rows]

    async def add_like(self, liker_id: int, liked_id: int) -> bool:
        """Like qo'shish va match tekshirish"""
        async with self.pool.acquire() as conn:
            # Like qo'shish
            try:
                await conn.execute("""
                    INSERT INTO likes (liker_id, liked_id)
                    VALUES ($1, $2)
                """, liker_id, liked_id)
            except:
                return False  # Already liked
            
            # Mutual like tekshirish
            mutual = await conn.fetchval("""
                SELECT COUNT(*) FROM likes
                WHERE liker_id = $1 AND liked_id = $2
            """, liked_id, liker_id)
            
            if mutual > 0:
                # Match yaratish
                user1, user2 = sorted([liker_id, liked_id])
                await conn.execute("""
                    INSERT INTO matches (user1_id, user2_id)
                    VALUES ($1, $2)
                    ON CONFLICT (user1_id, user2_id) DO NOTHING
                """, user1, user2)
                return True
            
            return False

    async def get_user_matches(self, user_id: int) -> List[Dict]:
        """Foydalanuvchining matchlari"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT m.id as match_id, u.*
                FROM matches m
                JOIN users u ON (
                    CASE 
                        WHEN m.user1_id = $1 THEN u.id = m.user2_id
                        ELSE u.id = m.user1_id
                    END
                )
                WHERE m.user1_id = $1 OR m.user2_id = $1
                ORDER BY m.created_at DESC
            """, user_id)
            
            return [dict(row) for row in rows]

    async def count_today_swipes(self, user_id: int) -> int:
        """Bugungi swipe lar soni"""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM likes
                WHERE liker_id = $1 AND created_at::date = CURRENT_DATE
            """, user_id)
            return count

    # ============ CHAT METHODS ============

    async def send_message(self, match_id: int, sender_id: int, receiver_id: int, text: str) -> int:
        """Xabar yuborish"""
        async with self.pool.acquire() as conn:
            msg_id = await conn.fetchval("""
                INSERT INTO messages (match_id, sender_id, receiver_id, message_text)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, match_id, sender_id, receiver_id, text)
            return msg_id

    async def get_chat_messages(self, match_id: int, limit: int = 50) -> List[Dict]:
        """Suhbat xabarlari"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT m.*, u.full_name as sender_name
                FROM messages m
                JOIN users u ON m.sender_id = u.id
                WHERE m.match_id = $1
                ORDER BY m.created_at DESC
                LIMIT $2
            """, match_id, limit)
            
            return [dict(row) for row in reversed(rows)]

    async def get_match_id_between_users(self, user1_id: int, user2_id: int) -> Optional[int]:
        """Ikki foydalanuvchi o'rtasidagi match ID"""
        user1, user2 = sorted([user1_id, user2_id])
        async with self.pool.acquire() as conn:
            match_id = await conn.fetchval("""
                SELECT id FROM matches
                WHERE user1_id = $1 AND user2_id = $2
            """, user1, user2)
            return match_id

    # ============ BLOCK & REPORT ============

    async def block_user(self, blocker_id: int, blocked_id: int):
        """Foydalanuvchini bloklash"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO blocks (blocker_id, blocked_id)
                VALUES ($1, $2)
                ON CONFLICT (blocker_id, blocked_id) DO NOTHING
            """, blocker_id, blocked_id)

    async def create_report(self, reporter_id: int, reported_id: int, reason: str, details: str = None):
        """Shikoyat yaratish"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO reports (reporter_id, reported_id, reason, details)
                VALUES ($1, $2, $3, $4)
            """, reporter_id, reported_id, reason, details)

    async def get_pending_reports(self) -> List[Dict]:
        """Pending shikoyatlar"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT r.*, 
                       u1.full_name as reporter_name, u1.username as reporter_username,
                       u2.full_name as reported_name, u2.username as reported_username
                FROM reports r
                JOIN users u1 ON r.reporter_id = u1.id
                JOIN users u2 ON r.reported_id = u2.id
                WHERE r.status = 'pending'
                ORDER BY r.created_at DESC
            """)
            return [dict(row) for row in rows]

    # ============ ADMIN METHODS ============

    async def get_stats(self) -> Dict:
        """Statistika"""
        async with self.pool.acquire() as conn:
            stats = {}
            
            # Jami foydalanuvchilar
            stats['total_users'] = await conn.fetchval("SELECT COUNT(*) FROM users")
            stats['active_users'] = await conn.fetchval("SELECT COUNT(*) FROM users WHERE status = 'active'")
            stats['paused_users'] = await conn.fetchval("SELECT COUNT(*) FROM users WHERE status = 'pause'")
            stats['banned_users'] = await conn.fetchval("SELECT COUNT(*) FROM users WHERE status = 'banned'")
            
            # Rejimlar
            stats['nikoh_users'] = await conn.fetchval("SELECT COUNT(*) FROM users WHERE mode = 'nikoh'")
            stats['dost_users'] = await conn.fetchval("SELECT COUNT(*) FROM users WHERE mode = 'dost'")
            stats['talaba_users'] = await conn.fetchval("SELECT COUNT(*) FROM users WHERE mode = 'talaba'")
            
            # Bugungi matchlar
            stats['today_matches'] = await conn.fetchval("""
                SELECT COUNT(*) FROM matches WHERE created_at::date = CURRENT_DATE
            """)
            
            # Premium
            stats['premium_users'] = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_premium = TRUE")
            
            # Bugungi daromad
            stats['today_revenue'] = await conn.fetchval("""
                SELECT COALESCE(SUM(amount), 0) FROM premium_transactions 
                WHERE status = 'success' AND created_at::date = CURRENT_DATE
            """) or 0
            
            return stats

    async def ban_user(self, user_id: int, admin_id: int, reason: str):
        """Foydalanuvchini ban qilish"""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE users SET status = 'banned' WHERE id = $1", user_id)
            await conn.execute("""
                INSERT INTO admin_actions (admin_id, action, target_user_id, details)
                VALUES ($1, 'ban', $2, $3)
            """, admin_id, user_id, reason)

    async def unban_user(self, user_id: int, admin_id: int):
        """Ban bekor qilish"""
        async with self.pool.acquire() as conn:
            await conn.execute("UPDATE users SET status = 'active' WHERE id = $1", user_id)
            await conn.execute("""
                INSERT INTO admin_actions (admin_id, action, target_user_id)
                VALUES ($1, 'unban', $2)
            """, admin_id, user_id)

    async def search_users(self, **filters) -> List[Dict]:
        """Foydalanuvchilarni qidirish"""
        conditions = ["1=1"]
        params = []
        param_num = 1
        
        if 'mode' in filters:
            conditions.append(f"mode = ${param_num}")
            params.append(filters['mode'])
            param_num += 1
        
        if 'city' in filters:
            conditions.append(f"city = ${param_num}")
            params.append(filters['city'])
            param_num += 1
        
        if 'status' in filters:
            conditions.append(f"status = ${param_num}")
            params.append(filters['status'])
            param_num += 1
        
        if 'is_premium' in filters:
            conditions.append(f"is_premium = ${param_num}")
            params.append(filters['is_premium'])
            param_num += 1
        
        query = f"""
            SELECT * FROM users 
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT 50
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(query, *params)
            return [dict(row) for row in rows]

    # ============ ADDITIONAL USER METHODS ============

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """ID orqali foydalanuvchi"""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM users WHERE id = $1",
                user_id
            )
            return dict(row) if row else None

    async def update_last_active(self, user_id: int):
        """Oxirgi faollik vaqtini yangilash"""
        async with self.pool.acquire() as conn:
            await conn.execute(
                "UPDATE users SET last_active = CURRENT_TIMESTAMP WHERE telegram_id = $1",
                user_id
            )

    async def is_blocked(self, user1_id: int, user2_id: int) -> bool:
        """Ikki foydalanuvchi orasida blok bormi"""
        async with self.pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM blocks 
                WHERE (blocker_id = $1 AND blocked_id = $2)
                   OR (blocker_id = $2 AND blocked_id = $1)
            """, user1_id, user2_id)
            return count > 0

    # ============ DAILY LIMITS ============

    async def check_today_limit(self, user_id: int, limit_type: str) -> tuple:
        """Bugungi limitni tekshirish"""
        import config
        
        # Foydalanuvchi premium emasmi
        user = await self.get_user_by_id(user_id)
        is_premium = user.get('is_premium', False) if user else False
        
        # Max limitni aniqlash
        if limit_type == 'stories':
            max_limit = config.MAX_STORIES_PREMIUM if is_premium else config.MAX_STORIES_FREE
        elif limit_type == 'swipes':
            max_limit = config.MAX_DAILY_SWIPES_PREMIUM if is_premium else config.MAX_DAILY_SWIPES_FREE
        elif limit_type == 'messages':
            max_limit = config.MAX_MESSAGES_PER_DAY_PREMIUM if is_premium else config.MAX_MESSAGES_PER_DAY_FREE
        else:
            max_limit = 10
        
        async with self.pool.acquire() as conn:
            current = await conn.fetchval("""
                SELECT count FROM daily_limits 
                WHERE user_id = $1 AND limit_type = $2 AND date = CURRENT_DATE
            """, user_id, limit_type)
            
            return (current or 0, max_limit)

    async def increment_daily_limit(self, user_id: int, limit_type: str):
        """Kunlik limitni oshirish"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO daily_limits (user_id, limit_type, count, date)
                VALUES ($1, $2, 1, CURRENT_DATE)
                ON CONFLICT (user_id, limit_type, date) 
                DO UPDATE SET count = daily_limits.count + 1
            """, user_id, limit_type)

    # ============ STORIES METHODS ============

    async def create_story(self, user_id: int, file_id: str, file_type: str, 
                          caption: str = None) -> int:
        """Yangi hikoya yaratish"""
        async with self.pool.acquire() as conn:
            story_id = await conn.fetchval("""
                INSERT INTO stories (user_id, file_id, file_type, caption)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            """, user_id, file_id, file_type, caption)
            return story_id

    async def get_active_stories(self, exclude_user_id: int = None) -> List[Dict]:
        """Faol hikoyalarni olish (24 soat ichida)"""
        async with self.pool.acquire() as conn:
            if exclude_user_id:
                rows = await conn.fetch("""
                    SELECT s.*, u.full_name, u.photo_verified as is_verified
                    FROM stories s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.expires_at > CURRENT_TIMESTAMP
                    AND s.user_id != $1
                    AND u.status = 'active'
                    ORDER BY s.created_at DESC
                """, exclude_user_id)
            else:
                rows = await conn.fetch("""
                    SELECT s.*, u.full_name, u.photo_verified as is_verified
                    FROM stories s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.expires_at > CURRENT_TIMESTAMP
                    AND u.status = 'active'
                    ORDER BY s.created_at DESC
                """)
            return [dict(row) for row in rows]

    async def get_user_stories(self, user_id: int) -> List[Dict]:
        """Foydalanuvchining hikoyalari"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM stories 
                WHERE user_id = $1 AND expires_at > CURRENT_TIMESTAMP
                ORDER BY created_at DESC
            """, user_id)
            return [dict(row) for row in rows]

    async def view_story(self, story_id: int, viewer_id: int):
        """Hikoyani ko'rdi deb belgilash"""
        async with self.pool.acquire() as conn:
            try:
                await conn.execute("""
                    INSERT INTO story_views (story_id, viewer_id)
                    VALUES ($1, $2)
                    ON CONFLICT (story_id, viewer_id) DO NOTHING
                """, story_id, viewer_id)
                
                # Ko'rishlar sonini oshirish
                await conn.execute("""
                    UPDATE stories SET views_count = views_count + 1 WHERE id = $1
                """, story_id)
            except:
                pass

    async def get_story_viewers(self, story_id: int) -> List[Dict]:
        """Hikoyani ko'rganlar"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT u.full_name, u.photo_verified as is_verified, sv.viewed_at
                FROM story_views sv
                JOIN users u ON sv.viewer_id = u.id
                WHERE sv.story_id = $1
                ORDER BY sv.viewed_at DESC
            """, story_id)
            return [dict(row) for row in rows]

    # ============ GIFTS METHODS ============

    async def send_gift(self, sender_id: int, receiver_id: int, gift_type: str,
                       amount: int, message: str = None) -> int:
        """Sovg'a yuborish"""
        async with self.pool.acquire() as conn:
            gift_id = await conn.fetchval("""
                INSERT INTO sent_gifts (sender_id, receiver_id, gift_type, amount, message)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, sender_id, receiver_id, gift_type, amount, message)
            return gift_id

    async def get_received_gifts(self, user_id: int) -> List[Dict]:
        """Qabul qilingan sovg'alar"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT sg.*, u.full_name as sender_name
                FROM sent_gifts sg
                JOIN users u ON sg.sender_id = u.id
                WHERE sg.receiver_id = $1
                ORDER BY sg.created_at DESC
            """, user_id)
            return [dict(row) for row in rows]


db = Database()