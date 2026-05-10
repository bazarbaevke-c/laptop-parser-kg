"""
Запустить ОДИН РАЗ локально для получения TG_SESSION_STRING.
После получения строки — добавить её в GitHub Secrets.
"""
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = int(input("Введите TG_API_ID: "))
API_HASH = input("Введите TG_API_HASH: ")

with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    session_string = client.session.save()

print("\n✅ Ваша SESSION_STRING:")
print(session_string)
print("\nСкопируйте её в GitHub Secrets → TG_SESSION_STRING")
