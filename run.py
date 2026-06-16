import asyncio
import logging
import uvicorn
import config
import database

# Direct imports of handlers
import handlers.owner as owner
import handlers.helper as helper
import handlers.user as user
import handlers.common as common

from aiogram.exceptions import TelegramNetworkError

from bot_instance import bot, dp
from web.main import app

# Set up runner logging
logger = logging.getLogger("Runner")

async def start_services():
    # 1. Initialize Database
    logger.info("Initializing SQLite database...")
    await database.init_db()
    
    # 2. Setup Uvicorn configuration for the FastAPI app
    logger.info(f"Setting up Web Dashboard on http://{config.WEB_HOST}:{config.WEB_PORT}")
    web_config = uvicorn.Config(
        app=app, 
        host=config.WEB_HOST, 
        port=config.WEB_PORT, 
        log_level="info"
    )
    server = uvicorn.Server(web_config)
    
    # 3. Check if Telegram Bot is configured
    if not config.is_configured():
        logger.warning("\n" + "="*70 + "\n"
                       "⚠️ WARNING: TELEGRAM_BOT_TOKEN IS NOT CONFIGURED IN THE .env FILE!\n"
                       "The Telegram Support Bot will NOT start.\n"
                       f"However, the Web Dashboard is running at http://{config.WEB_HOST}:{config.WEB_PORT}\n"
                       "Please edit .env, replace 'YOUR_TELEGRAM_BOT_TOKEN' with a real token,\n"
                       "and restart this application.\n" + 
                       "="*70 + "\n")
        
        # Run only the web server
        await server.serve()
        return

    # 4. Register Telegram Bot Routers in proper order
    # Note: owner and helper commands first, user commands next, common forwarding bridge LAST.
    dp.include_router(owner.router)
    dp.include_router(helper.router)
    dp.include_router(user.router)
    dp.include_router(common.router) # Catch-all router for chat message forwarding
    
    from bot_instance import telegram_proxy

    if telegram_proxy:
        logger.info("Telegram API proxy: %s", telegram_proxy)
    elif not config.TELEGRAM_PROXY:
        logger.warning(
            "Прямое подключение к Telegram. AmneziaVPN: включите VPN ДО запуска start.bat. "
            "Если ошибка повторится — Amnezia Free может не пропускать Telegram; "
            "попробуйте Premium или укажите TELEGRAM_PROXY в .env."
        )

    logger.info("Starting Telegram Bot (polling)...")
    
    # Run FastAPI server and Telegram Bot concurrently
    await asyncio.gather(
        server.serve(),
        dp.start_polling(bot, skip_updates=True)
    )

if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except TelegramNetworkError:
        logger.error(
            "\n" + "=" * 70 + "\n"
            "Не удалось подключиться к api.telegram.org.\n"
            "Обычно это блокировка сети или отсутствие VPN/прокси.\n\n"
            "AmneziaVPN (Windows): локального SOCKS нет — сначала подключите VPN,\n"
            "затем запустите start.bat. Если не помогло — Free может не включать Telegram.\n\n"
            "Или укажите в .env прокси другого клиента (v2rayN / Clash), например:\n"
            "  TELEGRAM_PROXY=socks5://127.0.0.1:10808\n"
            "Затем перезапустите start.bat.\n" + "=" * 70
        )
        raise SystemExit(1) from None
    except (KeyboardInterrupt, SystemExit):
        logger.info("Services stopped by user.")
