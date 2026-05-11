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

        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
            Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en'] });
            window.chrome = { runtime: {} };
        """)

        page = context.new_page()

        for page_num in range(1, 4):
            url = "https://lalafo.kg/kyrgyzstan/noutbuki"
            if page_num > 1:
                url += f"?page={page_num}"

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
                # Ждём рендеринга JS
                page.wait_for_timeout(8000)
            except Exception as e:
                print(f"[Lalafo] Страница {page_num} goto: {e}")
                break

            html = page.content()
            print(f"[Lalafo] Страница {page_num}: HTML размер {len(html)} байт")
            # Логируем фрагмент для диагностики URL-паттернов
            snippet = html[2000:3500] if len(html) > 3500 else html
            snippet_clean = snippet.replace("\n", " ")[:800]
            print(f"[Lalafo] HTML snippet: {snippet_clean}")

            # Все ссылки на странице
            all_links = page.query_selector_all("a[href]")
            lalafo_links = []
            for a in all_links:
                href = a.get_attribute("href") or ""
                if "noutbuki" in href or "notebook" in href.lower():
                    lalafo_links.append(href)

            print(f"[Lalafo] Страница {page_num}: ссылок с 'noutbuki' = {len(lalafo_links)}")

            # Все href через regex
            all_hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
            noutbuki_hrefs = [h for h in all_hrefs if "noutbuki" in h or "notebook" in h.lower()]
            print(f"[Lalafo] Страница {page_num}: regex href с 'noutbuki' = {len(noutbuki_hrefs)}")
            if noutbuki_hrefs:
                print(f"[Lalafo] Примеры: {noutbuki_hrefs[:3]}")

            # Пробуем широкие CSS-селекторы
            card_selectors = [
                "a[href*='/kyrgyzstan/noutbuki/']",
                "a[href*='/noutbuki/']",
                "a[href*='lalafo.kg']",
                "article a",
                ".listing-item a",
                "[class*='item'] a",
                "[class*='card'] a",
                "[class*='feed'] a",
            ]

            cards = []
            for sel in card_selectors:
                found = page.query_selector_all(sel)
                if found:
                    print(f"[Lalafo] Селектор '{sel}' нашёл {len(found)} элементов")
                    cards = found
                    break

            if not cards and noutbuki_hrefs:
                # Используем regex-найденные ссылки
                unique_hrefs = list(dict.fromkeys(noutbuki_hrefs))
                for href in unique_hrefs[:30]:
                    link = href if href.startswith("http") else f"https://lalafo.kg{href}"
                    slug = href.split("/")[-1].replace("-", " ").strip()
                    results.append({
                        "source": "Lalafo.kg",
                        "title": slug[:80] if slug else link[:80],
                        "price": "—",
                        "location": "—",
                        "link": link,
                        "parsed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                continue

            page_count = 0
            for card in cards:
                try:
                    href = card.get_attribute("href") or ""
                    if not href or ("noutbuki" not in href and "notebook" not in href.lower()):
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

                    if not title:
                        continue

                    results.append({
                        "source": "Lalafo.kg",
                        "title": title[:80],
                        "price": price[:50],
                        "location": location[:50],
                        "link": link,
                        "parsed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    })
                    page_count += 1
                except Exception:
                    continue

            if page_count == 0 and not noutbuki_hrefs:
                break

        browser.close()

    seen = set()
    unique = []
    for item in results:
        if item["link"] not in seen:
            seen.add(item["link"])
            unique.append(item)

    print(f"[Lalafo] Найдено: {len(unique)} объявлений")
    return unique
