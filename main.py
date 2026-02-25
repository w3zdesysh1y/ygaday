import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import system_settings
from database.models import async_main
from database.requests import add_questions

from user_handlers import user_router
from admin_handlers import admin_router

# Создаем бота
bot = Bot(
    token=system_settings['token'],
    default=DefaultBotProperties(
        parse_mode='HTML',
        link_preview_is_disabled=True
    )
)
dp = Dispatcher(storage=MemoryStorage())

async def main():
    print("🚀 Бот запускается...")
    
    # Инициализация базы данных
    await async_main()
    await add_questions()
    
    # Подключаем роутеры
    dp.include_routers(user_router, admin_router)
    
    print("✅ Бот успешно запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⛔ Бот остановлен")