import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from aiogram import F
from aiogram.filters import Command

import config
from database import db

# Handlerlarni import qilish
from handlers import (
    start, profile, matching, chat, premium, 
    settings, help, admin, stories, voice, 
    gifts, icebreaker
)

# Logging sozlash
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    """Bot commandalarini sozlash"""
    commands = [
        BotCommand(command="start", description="Botni ishga tushirish"),
        BotCommand(command="profile", description="Mening profilim"),
        BotCommand(command="matching", description="Moslik topish"),
        BotCommand(command="matches", description="Mening matchlarim"),
        BotCommand(command="stories", description="Hikoyalar"),
        BotCommand(command="settings", description="Sozlamalar"),
        BotCommand(command="help", description="Yordam"),
    ]
    
    await bot.set_my_commands(commands)
    logger.info("Bot commandalari sozlandi")


async def on_startup(bot: Bot):
    """Bot ishga tushganda"""
    logger.info("=" * 50)
    logger.info("BOT ISHGA TUSHMOQDA...")
    logger.info("=" * 50)
    
    # Database ulanish
    try:
        await db.connect()
        logger.info("[OK] Database ulandi")
    except Exception as e:
        logger.error(f"[ERROR] Database ulanish xatosi: {e}")
        raise
    
    # Bot commandalarini sozlash
    await set_bot_commands(bot)
    
    # Bot ma'lumotlari
    bot_info = await bot.get_me()
    logger.info(f"[OK] Bot: @{bot_info.username}")
    logger.info(f"[OK] Admin IDs: {config.ADMIN_IDS}")
    logger.info(f"[OK] Max Daily Swipes (Free): {config.MAX_DAILY_SWIPES_FREE}")
    logger.info(f"[OK] Max Daily Swipes (Premium): {config.MAX_DAILY_SWIPES_PREMIUM}")
    logger.info("=" * 50)
    logger.info("BOT TAYYOR! Polling boshlandi...")
    logger.info("=" * 50)


async def on_shutdown(bot: Bot):
    """Bot to'xtaganda"""
    logger.info("=" * 50)
    logger.info("BOT TO'XTATILMOQDA...")
    logger.info("=" * 50)
    
    # Database yopish
    await db.disconnect()
    logger.info("[OK] Database ulandi uzildi")
    
    # Bot session yopish
    await bot.session.close()
    logger.info("[OK] Bot session yopildi")
    
    logger.info("=" * 50)
    logger.info("BOT TO'XTATILDI")
    logger.info("=" * 50)


async def update_user_activity(event, user_id: int):
    """Foydalanuvchi faolligini yangilash"""
    try:
        await db.update_last_active(user_id)
    except Exception as e:
        logger.error(f"Last active yangilash xatosi: {e}")


async def main():
    """Asosiy funksiya"""
    
    # Storage tanlash (Redis yoki Memory)
    try:
        from redis.asyncio import Redis
        redis = Redis(host=config.REDIS_HOST, port=config.REDIS_PORT, db=0)
        await redis.ping()
        storage = RedisStorage(redis=redis)
        logger.info("[OK] Redis Storage ishlatilmoqda")
    except Exception as e:
        logger.warning(f"[WARNING] Redis ulanmadi: {e}")
        logger.info("[OK] Memory Storage ishlatilmoqda (Ma'lumotlar restart'da yo'qoladi)")
        storage = MemoryStorage()
    
    # Bot va Dispatcher
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=storage)
    
    # Startup va shutdown handlerlar
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Middleware - foydalanuvchi faolligini kuzatish
    @dp.message.middleware()
    async def activity_middleware(handler, event, data):
        user = event.from_user
        if user and not user.is_bot:
            asyncio.create_task(update_user_activity(event, user.id))
        return await handler(event, data)
    
    # Handlerlarni ro'yxatdan o'tkazish
    # Tartib muhim! Admin birinchi bo'lishi kerak
    dp.include_router(admin.router)
    dp.include_router(start.router)
    dp.include_router(profile.router)
    dp.include_router(matching.router)
    dp.include_router(chat.router)
    dp.include_router(stories.router)
    dp.include_router(voice.router)
    dp.include_router(gifts.router)
    dp.include_router(icebreaker.router)
    dp.include_router(premium.router)
    dp.include_router(settings.router)
    dp.include_router(help.router)
    
    try:
        # Botni ishga tushirish
        await dp.start_polling(
            bot, 
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True  # Eski yangilanishlarni o'chirish
        )
    except Exception as e:
        logger.error(f"[ERROR] Polling xatosi: {e}")
        raise
    finally:
        await on_shutdown(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("[STOP] Bot to'xtatildi (Keyboard Interrupt)")
    except Exception as e:
        logger.critical(f"[CRITICAL ERROR] Fatal xato: {e}", exc_info=True)