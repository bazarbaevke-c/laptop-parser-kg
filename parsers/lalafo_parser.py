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
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://lalafo.kg/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "same-origin",
}


def parse_lalafo() -> list[dict]:
    base_url = "https://lalafo.kg/kyrgyzstan/noutbuki"
    results = []
    page = 1

    session = requests.Session()
    session.headers.update(HEADERS)

    # Сначала заходим на главную чтобы получить куки
    try:
        session.get("https://lalafo.kg/", timeout=15)
        time.sleep(random.uniform(1.0, 2.0))
    except Exception:
        pass

    while page <= 5:
        params = {"page": page} if page > 1 else {}
        try:
            resp = session.get(base_url, params=params, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"[Lalafo] Ошибка страница {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")

        cards = (
            soup.select("article.ad-tile")
            or soup.select("div.feed-item")
            or soup.select("li.listing-item")
            or soup.select("[class*='ad-card']")
            or soup.select("[class*='listing']")
        )

        if not cards:
            # Попробуем найти любые ссылки на объявления
            cards = soup.select("a[href*='/kyrgyzstan/noutbuki/']")

        if not cards:
            break

        for card in cards:
            try:
                title_el = card.select_one("h3, h2, h1, .ad-tile-title, .title, [class*='title']")
                price_el = card.select_one(".price, .ad-price, [class*='price']")
                link_el = card if card.name == "a" else card.select_one("a[href]")
                location_el = card.select_one(".location, .city, [class*='location'], [class*='city']")

                title = title_el.text.strip() if title_el else "—"
                price_raw = price_el.text.strip() if price_el else "—"
                href = link_el.get("href", "") if link_el else ""
                link = href if href.startswith("http") else f"https://lalafo.kg{href}"
                location = location_el.text.strip() if location_el else "—"

                if title == "—":
                    continue

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
        time.sleep(random.uniform(2.0, 4.0))

    print(f"[Lalafo] Найдено: {len(results)} объявлений")
    return results
