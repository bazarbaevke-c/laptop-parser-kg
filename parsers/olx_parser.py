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
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# Пробуем несколько вариантов домена
OLX_URLS = [
    "https://www.olx.kg/elektronika/noutbuki-i-aksessuary/noutbuki/",
    "https://olx.kg/elektronika/noutbuki-i-aksessuary/noutbuki/",
]


def parse_olx() -> list[dict]:
    results = []

    # Находим рабочий URL
    base_url = None
    session = requests.Session()
    session.headers.update(HEADERS)

    for url in OLX_URLS:
        try:
            resp = session.get(url, timeout=20)
            if resp.status_code == 200:
                base_url = url
                break
            print(f"[OLX] {url} → статус {resp.status_code}")
        except Exception as e:
            print(f"[OLX] {url} → ошибка: {e}")

    if not base_url:
        print("[OLX] Сайт недоступен с серверов GitHub, пропускаем")
        print("[OLX] Найдено: 0 объявлений")
        return []

    page = 1
    while page <= 5:
        url = base_url if page == 1 else f"{base_url}?page={page}"
        try:
            resp = session.get(url, timeout=20)
            resp.raise_for_status()
        except Exception as e:
            print(f"[OLX] Ошибка страница {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "html.parser")
        cards = soup.select("div[data-cy='l-card']")

        if not cards:
            break

        for card in cards:
            try:
                title_el = card.select_one("h6")
                price_el = card.select_one("p[data-testid='ad-price']")
                link_el = card.select_one("a[href]")
                location_el = card.select_one("p[data-testid='location-date']")

                title = title_el.text.strip() if title_el else "—"
                price_raw = price_el.text.strip() if price_el else "—"
                link = "https://www.olx.kg" + link_el["href"] if link_el else "—"
                location = location_el.text.strip() if location_el else "—"

                results.append({
                    "source": "OLX.kg",
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

    print(f"[OLX] Найдено: {len(results)} объявлений")
    return results
