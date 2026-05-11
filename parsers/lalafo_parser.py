from datetime import datetime
import re


def parse_lalafo() -> list[dict]:
    from playwright.sync_api import sync_playwright

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        for page_num in range(1, 6):
            url = "https://lalafo.kg/kyrgyzstan/noutbuki"
            if page_num > 1:
                url += f"?page={page_num}"

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Ждём появления карточек
                page.wait_for_selector(
                    "article, .feed-item, [class*='listing'], a[href*='/noutbuki/']",
                    timeout=15000,
                )
            except Exception as e:
                print(f"[Lalafo] Страница {page_num}: {e}")
                break

            # Перехватываем все ссылки на объявления
            cards = page.query_selector_all("a[href*='/kyrgyzstan/noutbuki/']")

            if not cards:
                # Попробуем общие карточки
                cards = page.query_selector_all("article, li.listing-item, div.feed-item")

            if not cards:
                break

            page_results_count = 0
            for card in cards:
                try:
                    href = card.get_attribute("href") or ""
                    if not href:
                        continue
                    link = href if href.startswith("http") else f"https://lalafo.kg{href}"

                    # Пробуем взять текст из карточки
                    title_el = card.query_selector("h3, h2, [class*='title'], [class*='name']")
                    price_el = card.query_selector("[class*='price']")
                    location_el = card.query_selector("[class*='location'], [class*='city']")

                    title = title_el.inner_text().strip() if title_el else card.inner_text()[:60].strip()
                    title = re.sub(r"\s+", " ", title)

                    price = price_el.inner_text().strip() if price_el else "—"
                    price = re.sub(r"\s+", " ", price)

                    location = location_el.inner_text().strip() if location_el else "—"

                    if not title or title == "—":
                        continue

                    results.append({
                        "source": "Lalafo.kg",
                        "title": title[:80],
                        "price": price[:50],
                        "location": location[:50],
                        "link": link,
                        "parsed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                    page_results_count += 1
                except Exception:
                    continue

            if page_results_count == 0:
                break

        browser.close()

    # Дедуплицируем по ссылке
    seen = set()
    unique = []
    for item in results:
        if item["link"] not in seen:
            seen.add(item["link"])
            unique.append(item)

    print(f"[Lalafo] Найдено: {len(unique)} объявлений")
    return unique
