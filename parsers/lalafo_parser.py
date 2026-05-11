from datetime import datetime
import re


def parse_lalafo() -> list[dict]:
    from playwright.sync_api import sync_playwright

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            locale="ru-RU",
            viewport={"width": 1280, "height": 800},
            extra_http_headers={
                "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
            },
        )

        # Скрываем следы автоматизации
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en'] });
            window.chrome = { runtime: {} };
        """)

        page = context.new_page()

        for page_num in range(1, 6):
            url = "https://lalafo.kg/kyrgyzstan/noutbuki"
            if page_num > 1:
                url += f"?page={page_num}"

            try:
                page.goto(url, wait_until="networkidle", timeout=45000)
            except Exception as e:
                print(f"[Lalafo] Страница {page_num} goto: {e}")
                # Пробуем продолжить — иногда networkidle не достигается, но контент есть
                try:
                    page.wait_for_timeout(3000)
                except Exception:
                    break

            # Пробуем найти объявления несколькими способами
            html = page.content()
            print(f"[Lalafo] Страница {page_num}: HTML размер {len(html)} байт")

            # Ищем ссылки на объявления
            cards = page.query_selector_all("a[href*='/kyrgyzstan/noutbuki/']")
            print(f"[Lalafo] Страница {page_num}: найдено ссылок = {len(cards)}")

            if not cards:
                # Пробуем другие селекторы
                cards = page.query_selector_all("a[href*='lalafo.kg/kyrgyzstan/noutbuki/']")

            if not cards:
                # Парсим HTML через регулярки как запасной вариант
                hrefs = re.findall(r'href="(/kyrgyzstan/noutbuki/[^"]+)"', html)
                hrefs += re.findall(r'href="(https://lalafo\.kg/kyrgyzstan/noutbuki/[^"]+)"', html)
                unique_hrefs = list(dict.fromkeys(hrefs))
                print(f"[Lalafo] Страница {page_num}: regex нашёл {len(unique_hrefs)} href")

                for href in unique_hrefs[:30]:
                    link = href if href.startswith("http") else f"https://lalafo.kg{href}"
                    results.append({
                        "source": "Lalafo.kg",
                        "title": link.split("/")[-1].replace("-", " ")[:80],
                        "price": "—",
                        "location": "—",
                        "link": link,
                        "parsed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })

                if not unique_hrefs:
                    break
                continue

            page_results_count = 0
            for card in cards:
                try:
                    href = card.get_attribute("href") or ""
                    if not href:
                        continue
                    link = href if href.startswith("http") else f"https://lalafo.kg{href}"

                    title_el = card.query_selector("h3, h2, [class*='title'], [class*='name'], [class*='Title']")
                    price_el = card.query_selector("[class*='price'], [class*='Price']")
                    location_el = card.query_selector("[class*='location'], [class*='city'], [class*='Location']")

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
