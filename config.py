import os

# === TELEGRAM API (для чтения каналов через Telethon) ===
TG_API_ID = int(os.getenv("TG_API_ID", "0"))
TG_API_HASH = os.getenv("TG_API_HASH", "")
TG_PHONE = os.getenv("TG_PHONE", "")          # ваш номер +996...
TG_SESSION_STRING = os.getenv("TG_SESSION_STRING", "")  # сохранённая сессия

# === TELEGRAM BOT (для отправки отчёта) ===
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
REPORT_CHAT_ID = os.getenv("REPORT_CHAT_ID", "")  # ваш chat_id или группа

# === КАНАЛЫ ДЛЯ ПАРСИНГА ===
TG_CHANNELS = [
    "computer_sales_in_kyrgyzstan",
    "compshop_kg",
]

# === САЙТЫ ===
OLX_URL = "https://www.olx.kg/elektronika/noutbuki-i-aksessuary/noutbuki/"
LALAFO_URL = "https://lalafo.kg/kyrgyzstan/noutbuki"

# === ФАЙЛЫ ===
EXCEL_FILE = "laptops_data.xlsx"

# === ФИЛЬТРЫ ===
LAPTOP_KEYWORDS = [
    "ноутбук", "laptop", "ноут", "macbook", "lenovo", "asus", "hp",
    "dell", "acer", "huawei", "msi", "samsung", "notebook"
]

# === СКОЛЬКО ПОСТОВ БРАТЬ ИЗ TG ===
TG_POSTS_LIMIT = 50  # последние 50 сообщений за 2 дня
