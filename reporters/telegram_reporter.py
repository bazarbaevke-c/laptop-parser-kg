import requests
from datetime import datetime
from config import BOT_TOKEN, REPORT_CHAT_ID, EXCEL_FILE


def _extract_price_number(price_str: str) -> float:
    """Вытаскивает число из строки цены для сортировки."""
    import re
    nums = re.findall(r"\d+", price_str.replace(" ", ""))
    return float(nums[0]) if nums else float("inf")


def _build_report(all_items: list[dict]) -> str:
    """Формирует текст Telegram-отчёта."""
    now = datetime.now().strftime("%d.%m.%Y")

    olx_items = [x for x in all_items if "OLX" in x["source"]]
    lalafo_items = [x for x in all_items if "Lalafo" in x["source"]]
    tg_items = [x for x in all_items if "TG" in x["source"]]

    # Топ-5 дешёвых (у которых цена не "уточнить" и не "—")
    priced = [
        x for x in all_items
        if x["price"] not in ("уточнить", "—", "")
    ]
    priced_sorted = sorted(priced, key=lambda x: _extract_price_number(x["price"]))
    top5 = priced_sorted[:5]

    lines = [
        f"📊 *Отчёт по ноутбукам — {now}*",
        "",
        f"🆕 Всего объявлений: *{len(all_items)}*",
        f"   └ OLX.kg: {len(olx_items)}",
        f"   └ Lalafo.kg: {len(lalafo_items)}",
        f"   └ Telegram каналы: {len(tg_items)}",
        "",
    ]

    if top5:
        lines.append("🔥 *Топ-5 выгодных предложений:*")
        for i, item in enumerate(top5, 1):
            title = item["title"][:45].strip()
            price = item["price"]
            source = item["source"].replace("TG: ", "")
            link = item["link"]
            lines.append(f"{i}\\. [{title}]({link})")
            lines.append(f"   💰 {price} | 📍 {source}")
        lines.append("")

    lines += [
        "📎 Excel\\-файл с полной таблицей прикреплён ниже",
        "",
        f"🕐 Следующий отчёт через 2 дня",
    ]

    return "\n".join(lines)


def send_report(all_items: list[dict], excel_path: str) -> bool:
    """Отправляет текстовый отчёт и Excel-файл в Telegram."""
    if not BOT_TOKEN or not REPORT_CHAT_ID:
        print("[Reporter] BOT_TOKEN или REPORT_CHAT_ID не заданы")
        return False

    report_text = _build_report(all_items)

    # Отправляем текст
    text_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    text_resp = requests.post(text_url, json={
        "chat_id": REPORT_CHAT_ID,
        "text": report_text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
    }, timeout=15)

    if not text_resp.ok:
        print(f"[Reporter] Ошибка отправки текста: {text_resp.text}")
        return False

    # Отправляем Excel
    doc_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
    with open(excel_path, "rb") as f:
        doc_resp = requests.post(doc_url, data={
            "chat_id": REPORT_CHAT_ID,
            "caption": f"📋 Ноутбуки {datetime.now().strftime('%d.%m.%Y')} — полная таблица",
        }, files={"document": (excel_path, f)}, timeout=30)

    if doc_resp.ok:
        print("[Reporter] Отчёт и файл успешно отправлены в Telegram")
        return True
    else:
        print(f"[Reporter] Ошибка отправки файла: {doc_resp.text}")
        return False
