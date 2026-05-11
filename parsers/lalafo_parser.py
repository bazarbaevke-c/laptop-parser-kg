import requests
from datetime import datetime
import re
import time


HEADERS_MOBILE = {
    "User-Agent": "LalafoApp/5.0 (Android 12; SM-G991B) okhttp/4.9.3",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "X-Country-Id": "117",
    "X-Language": "ru",
}

HEADERS_WEB = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 12; SM-G991B) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36"
    ),
    "Accept": "application/json, text/html, */*",
    "Accept-Language": "ru-RU,ru;q=0.9",
    "Referer": "https://lalafo.kg/",
}

# Возможные API endpoints Lalafo
API_CANDIDATES = [
    "https://lalafo.kg/api/v3/ad/search/category/kyrgyzstan/noutbuki?page={page}&per-page=50",
    "https://lalafo.kg/api/v1/general/classifieds?category_id=218&country_id=117&page={page}",
    "https://lalafo.kg/api/v3/general/feeds/category/kyrgyzstan/noutbuki?page={page}",
    "https://lalafo.kg/api/v2/feed?category=noutbuki&country=kyrgyzstan&page={page}",
]


def _try_api(session: requests.Session) -> list[dict]:
    """Пробует найти рабочий API endpoint Lalafo."""
    results = []

    for template in API_CANDIDATES:
        url = template.format(page=1)
        try:
            resp = session.get(url, timeout=15)
            print(f"[Lalafo] API {url[:60]}... → {resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                print(f"[Lalafo] API ответ ключи: {list(data.keys())[:5]}")
                # Извлекаем объявления из разных форматов ответа
                items = (
                    data.get("data", {}).get("items", [])
                    or data.get("items", [])
                    or data.get("feed", [])
                    or data.get("classifieds", [])
                    or (data if isinstance(data, list) else [])
                )
                for item in items[:50]:
                    title = item.get("title") or item.get("name") or "—"
                    price = str(item.get("price") or item.get("params", {}).get("price") or "—")
                    city = item.get("city", {})
                    location = city.get("name") if isinstance(city, dict) else str(city or "—")
                    link = item.get("url") or item.get("link") or ""
                    if not link:
                        item_id = item.get("id") or item.get("ad_id")
                        slug = item.get("slug") or ""
                        if item_id and slug:
                            link = f"https://lalafo.kg/kyrgyzstan/noutbuki/{slug}-i{item_id}"
                        elif item_id:
                            link = f"https://lalafo.kg/ad/{item_id}"

                    results.append({
                        "source": "Lalafo.kg",
                        "title": str(title)[:80],
                        "price": str(price)[:50],
                        "location": str(location)[:50],
                        "link": link,
                        "parsed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })

                if results:
                    print(f"[Lalafo] API сработал: {url[:60]}")
                    return results
        except requests.exceptions.JSONDecodeError:
            pass
        except Exception as e:
            print(f"[Lalafo] API ошибка: {e}")

    return results


def _try_web_scrape(session: requests.Session) -> list[dict]:
    """Попытка получить HTML страницу с мобильным UA."""
    results = []
    session.headers.update(HEADERS_WEB)

    url = "https://lalafo.kg/kyrgyzstan/noutbuki"
    try:
        resp = session.get(url, timeout=20)
        print(f"[Lalafo] Web GET → {resp.status_code}, {len(resp.text)} байт")
        if resp.status_code != 200:
            return []

        html = resp.text
        if "challenge-platform" in html or "cf-browser-verification" in html:
            print("[Lalafo] Cloudflare challenge в ответе")
            return []

        # Ищем JSON в HTML (Next.js / React __NEXT_DATA__)
        next_data = re.search(r'<script id="__NEXT_DATA__"[^>]*>({.*?})</script>', html, re.DOTALL)
        if next_data:
            import json
            try:
                data = json.loads(next_data.group(1))
                # Ищем объявления рекурсивно
                text = str(data)
                titles = re.findall(r'"title"\s*:\s*"([^"]{10,80})"', text)
                prices = re.findall(r'"price"\s*:\s*"?(\d+)"?', text)
                slugs = re.findall(r'"slug"\s*:\s*"([^"]+noutbuk[^"]*)"', text, re.IGNORECASE)
                print(f"[Lalafo] __NEXT_DATA__ titles={len(titles)}, slugs={len(slugs)}")
                for i, slug in enumerate(slugs[:30]):
                    title = titles[i] if i < len(titles) else slug
                    price = prices[i] if i < len(prices) else "—"
                    results.append({
                        "source": "Lalafo.kg",
                        "title": title[:80],
                        "price": price[:50],
                        "location": "—",
                        "link": f"https://lalafo.kg/kyrgyzstan/noutbuki/{slug}",
                        "parsed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                if results:
                    return results
            except Exception:
                pass

        # Fallback: ищем href
        hrefs = re.findall(r'href=["\']([^"\']*noutbuki/[^"\']{10,})["\']', html)
        hrefs = list(dict.fromkeys(hrefs))
        print(f"[Lalafo] Найдено href с noutbuki: {len(hrefs)}")
        for href in hrefs[:30]:
            link = href if href.startswith("http") else f"https://lalafo.kg{href}"
            slug = href.rstrip("/").split("/")[-1]
            results.append({
                "source": "Lalafo.kg",
                "title": slug.replace("-", " ")[:80],
                "price": "—",
                "location": "—",
                "link": link,
                "parsed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
            })
    except Exception as e:
        print(f"[Lalafo] Web ошибка: {e}")

    return results


def parse_lalafo() -> list[dict]:
    session = requests.Session()
    session.headers.update(HEADERS_MOBILE)

    # Сначала пробуем API
    results = _try_api(session)

    # Если API не дал результатов — пробуем HTML
    if not results:
        results = _try_web_scrape(session)

    if not results:
        print("[Lalafo] Сайт недоступен с серверов GitHub (Cloudflare), пропускаем")

    # Дедуплицируем
    seen = set()
    unique = []
    for item in results:
        if item["link"] not in seen:
            seen.add(item["link"])
            unique.append(item)

    print(f"[Lalafo] Найдено: {len(unique)} объявлений")
    return unique
