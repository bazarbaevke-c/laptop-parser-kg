"""
Координатор-агент: запускает все парсеры, сохраняет данные, отправляет отчёт.
Запуск: python main.py
"""

import sys
from parsers.olx_parser import parse_olx
from parsers.lalafo_parser import parse_lalafo
from parsers.telegram_parser import parse_telegram_channels
from storage.excel_writer import save_to_excel
from reporters.telegram_reporter import send_report


def deduplicate(items: list[dict]) -> list[dict]:
    """Убирает дубли по ссылке."""
    seen = set()
    unique = []
    for item in items:
        key = item.get("link", "")
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


def run():
    print("=" * 50)
    print("🤖 Агент закупа запущен")
    print("=" * 50)

    all_items = []

    # 1. OLX.kg
    print("\n[1/3] Парсим OLX.kg...")
    try:
        olx_data = parse_olx()
        all_items.extend(olx_data)
    except Exception as e:
        print(f"[OLX] Критическая ошибка: {e}")

    # 2. Lalafo.kg
    print("\n[2/3] Парсим Lalafo.kg...")
    try:
        lalafo_data = parse_lalafo()
        all_items.extend(lalafo_data)
    except Exception as e:
        print(f"[Lalafo] Критическая ошибка: {e}")

    # 3. Telegram каналы
    print("\n[3/3] Читаем Telegram-каналы...")
    try:
        tg_data = parse_telegram_channels()
        all_items.extend(tg_data)
    except Exception as e:
        print(f"[TG] Критическая ошибка: {e}")

    if not all_items:
        print("\n❌ Данные не получены. Проверьте подключение.")
        sys.exit(1)

    # Дедупликация
    all_items = deduplicate(all_items)
    print(f"\n✅ Итого уникальных объявлений: {len(all_items)}")

    # 4. Сохранение в Excel
    print("\n[4/4] Сохраняем в Excel...")
    excel_path = save_to_excel(all_items)

    # 5. Отправка в Telegram
    print("\n[5/5] Отправляем отчёт в Telegram...")
    send_report(all_items, excel_path)

    print("\n✅ Готово!")


if __name__ == "__main__":
    run()
