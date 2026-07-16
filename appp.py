import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# --- КОНФИГУРАЦИЯ СТАРОГО БОТА ---
OLD_BOT_TOKEN = "8843954886:AAFrGTDuOpI3Ly9YH6mvPnl5xuGw1JmY26Q"  # Замени на токен старого бота
NEW_BOT_USERNAME = "@Jfuglbot"        # Юзернейм нового бота

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

async def main():
    print("✅ Старый бот запущен. Отправляет сообщение о переезде.")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
