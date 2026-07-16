import asyncio
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# --- КОНФИГУРАЦИЯ СТАРОГО БОТА ---
OLD_BOT_TOKEN = "8843954886:AAFrGTDuOpI3Ly9YH6mvPnl5xuGw1JmY26Q"
NEW_BOT_USERNAME = "@Jfuglbot"

# --- ИНИЦИАЛИЗАЦИЯ ---
bot = Bot(token=OLD_BOT_TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    """Отправляет сообщение о переезде на нового бота."""
    text = (
        "🚀 **Бот переехал!**\n\n"
        "Мы переехали на новый, более быстрый и удобный бот.\n\n"
        f"👉 **Переходите по ссылке:** {NEW_BOT_USERNAME}\n\n"
        "Все доступы и бонусы сохранены. Подписка переносится автоматически.\n\n"
        "Спасибо, что вы с нами!"
    )
    await message.answer(text, parse_mode="Markdown")

# --- ВЕБ-СЕРВЕР ДЛЯ UPTIMEROBOT ---
async def handle(request):
    return web.Response(text="Bot is alive")

async def start_web_server():
    app = web.Application()
    app.router.add_get('/', handle)
    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host='0.0.0.0', port=port)
    await site.start()
    print(f"✅ Веб-сервер для UptimeRobot запущен на порту {port}")

async def main():
    await start_web_server()
    print("✅ Старый бот запущен. Отправляет сообщение о переезде.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
