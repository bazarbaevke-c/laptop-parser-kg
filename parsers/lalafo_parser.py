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
                "--window-size=1280,800",
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
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            },
        )

        # Stealth-патч
        try:
            from playwright_stealth import stealth_sync
            page = context.new_page()
            stealth_sync(page)
            print("[Lalafo] playwright-stealth применён")
        except ImportError:
            page = context.new_page()
            print("[Lalafo] playwright-stealth не установлен, работаем без него")
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3] });
                Object.defineProperty(navigator, 'languages', { get: () => ['ru-RU', 'ru', 'en'] });
                window.chrome = { runtime: {} };
            """)

        for page_num in range(1, 4):
            url = "https://lalafo.kg/kyrgyzstan/noutbuki"
            if page_num > 1:
                url += f"?page={page_num}"

            try:
                page.goto(url, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                print(f"[Lalafo] goto ошибка: {e}")
                break

            # Ждём прохождения Cloudflare challenge (15 сек)
            print(f"[Lalafo] Страница {page_num}: ждём Cloudflare challenge...")
            page.wait_for_timeout(15000)

            current_url = page.url
            html = page.content()
            print(f"[Lalafo] URL после ожидания: {current_url}")
            print(f"[Lalafo] HTML размер: {len(html)} байт")

            # Проверяем — всё ещё challenge?
            if "challenge-platform" in html or "cf-browser-verification" in html:
                print(f"[Lalafo] Страница {page_num}: Cloudflare challenge не прошёл")
                break

            # Ищем все href с noutbuki
            all_hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
            noutbuki_hrefs = [h for h in all_hrefs if "noutbuki" in h and len(h) > 20]
            noutbuki_hrefs = list(dict.fromkeys(noutbuki_hrefs))
            print(f"[Lalafo] Страница {page_num}: найдено href = {len(noutbuki_hrefs)}")

            if not noutbuki_hrefs:
                break

            for href in noutbuki_hrefs[:40]:
                link = href if href.startswith("http") else f"https://lalafo.kg{href}"
                # Пробуем взять заголовок из ссылки
                slug = href.rstrip("/").split("/")[-1]
                title = slug.replace("-", " ").strip()

                results.append({
                    "source": "Lalafo.kg",
                    "title": title[:80],
                    "price": "—",
                    "location": "—",
                    "link": link,
                    "parsed_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                })

        browser.close()

    seen = set()
    unique = []
    for item in results:
        if item["link"] not in seen:
            seen.add(item["link"])
            unique.append(item)

    print(f"[Lalafo] Найдено: {len(unique)} объявлений")
    return unique
