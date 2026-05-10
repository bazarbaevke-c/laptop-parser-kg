import re
from datetime import datetime, timedelta, timezone
from telethon.sync import TelegramClient
from telethon.sessions import StringSession
from config import (
    TG_API_ID, TG_API_HASH, TG_SESSION_STRING,
    TG_CHANNELS, LAPTOP_KEYWORDS, TG_POSTS_LIMIT
)


def is_laptop_post(text: str) -> bool:
    """Проверяет, относится ли пост к ноутбукам."""
    if not text:
        return False
    text_lower = text.lower()
    return any(kw in text_lower for kw in LAPTOP_KEYWORDS)


def extract_price(text: str) -> str:
    """Извлекает цену из текста поста."""
    patterns = [
        r"(\d[\d\s]{2,})\s*(?:сом|KGS|сомов|тыс|тг)",
        r"(\d[\d\s]{3,})\s*(?:\$|USD|usd|долл)",
        r"(?:цена|стоимость|price)[:\s]+(\d[\d\s]+)",
        r"(\d{4,})",  # просто число от 4 цифр
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m.group(1).replace(" ", "") + " сом"
    return "уточнить"


def parse_telegram_channels() -> list[dict]:
    """Читает посты из Telegram-каналов за последние 2 дня."""
    results = []
    two_days_ago = datetime.now(timezone.utc) - timedelta(days=2)

    with TelegramClient(
        StringSession(TG_SESSION_STRING), TG_API_ID, TG_API_HASH
    ) as client:
        for channel in TG_CHANNELS:
            try:
                entity = client.get_entity(channel)
                channel_name = getattr(entity, "title", str(channel))
                print(f"[TG] Читаю канал: {channel_name}")

                messages = client.get_messages(
                    entity, limit=TG_POSTS_LIMIT
                )

                for msg in messages:
                    if not msg.date or msg.date < two_days_ago:
                        continue
                    if not msg.text:
                        continue
                    if not is_laptop_post(msg.text):
                        continue

                    price = extract_price(msg.text)
                    short_text = msg.text[:200].replace("\n", " ")

                    # Формируем ссылку на пост
                    if hasattr(entity, "username") and entity.username:
                        link = f"https://t.me/{entity.username}/{msg.id}"
                    else:
                        link = f"https://t.me/c/{entity.id}/{msg.id}"

                    results.append({
                        "source": f"TG: {channel_name}",
                        "title": short_text[:80],
                        "price": price,
                        "location": "Кыргызстан",
                        "link": link,
                        "parsed_at": msg.date.strftime("%Y-%m-%d %H:%M"),
                    })

            except Exception as e:
                print(f"[TG] Ошибка в канале {channel}: {e}")
                continue

    print(f"[TG] Найдено постов о ноутбуках: {len(results)}")
    return results
