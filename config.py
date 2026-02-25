import os
from dotenv import load_dotenv
import sys

# Загружаем переменные из файла .env
load_dotenv()

# Получаем секреты из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Проверка, что токены загрузились
if not BOT_TOKEN or not ADMIN_ID:
    print("❌ ОШИБКА: Не удалось загрузить BOT_TOKEN или ADMIN_ID из файла .env")
    print("Убедитесь, что файл .env существует и содержит нужные переменные.")
    sys.exit(1)

system_settings = {
    'token': BOT_TOKEN,
    'mainadmin_id': ADMIN_ID
}

print("✅ Конфигурация успешно загружена из .env файла")