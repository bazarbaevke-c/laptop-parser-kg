import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import random

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "ru-RU,ru;q=0.9",
}


def parse_lalafo() -> list[dict]:
    """Парсит ноутбуки с Lalafo.kg, возвращает список объявлений."""
    base_url = "https://lalafo.kg/kyrgyzstan/noutbuki"
    results = []
    page = 1

    while page <= 5:
        params = {"page": page} if page > 1 else {}
        try:
            resp = requests.get(base_url, headers=HEADERS, params=params, timeout=15)
            resp.raise_for_status()
        except Exception as e:
            print(f"[Lalafo] Ошибка страница {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        # Lalafo использует разные структуры — пробуем оба варианта
        cards = soup.select("article.ad-tile") or soup.select("div.feed-item")

        if not cards:
            break

        for card in cards:
            try:
                title_el = card.select_one("h3, h2, .ad-tile-title, .title")
                price_el = card.select_one(".price, .ad-price, [class*='price']")
                link_el = card.select_one("a[href]")
                location_el = card.select_one(".location, .city, [class*='location']")

                title = title_el.text.strip() if title_el else "—"
                price_raw = price_el.text.strip() if price_el else "—"
                href = link_el["href"] if link_el else ""
                link = href if href.startswith("http") else f"https://lalafo.kg{href}"
                location = location_el.text.strip() if location_el else "—"

                results.append({
                    "source": "Lalafo.kg",
                    "title": title,
                    "price": price_raw,
                    "location": location,
                    "link": link,
                    "parsed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })
            except Exception:
                continue

        page += 1
        time.sleep(random.uniform(1.5, 3.0))

    print(f"[Lalafo] Найдено: {len(results)} объявлений")
    return results
