from __future__ import annotations

import random
import re
import time
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from playwright.sync_api import Browser, Page, sync_playwright

from src.config import (
    DEBUG,
    HEADLESS,
    MAX_PAGES,
    REQUEST_TIMEOUT_MS,
    SCROLL_PAUSE_SEC,
    SCROLL_STEPS,
    TARGET_PAGES,
)
from src.models import ListingRecord

AREA_RE = re.compile(r"(\d+[\.,]?\d*)\s*м²")
FLOOR_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s*этаж")
LISTING_ID_RE = re.compile(r"/rent/flat/(\d+)/")
METRO_HINT_RE = re.compile(r"^[А-ЯA-ZЁ].{1,80}$")


class CianScraper:
    def __init__(self) -> None:
        self.scraped_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

    def scrape_all(self) -> list[ListingRecord]:
        records: list[ListingRecord] = []

        with sync_playwright() as pw:
            browser = pw.chromium.launch(
                headless=HEADLESS,
                slow_mo=300 if not HEADLESS else 0,
            )
            try:
                for district, url in TARGET_PAGES.items():
                    district_records = self._scrape_district(browser, district, url)
                    print(f"{district}: найдено записей {len(district_records)}")
                    records.extend(district_records)
                    time.sleep(random.uniform(8, 15))
            finally:
                browser.close()

        return records

    def _scrape_district(
        self,
        browser: Browser,
        district: str,
        base_url: str,
    ) -> list[ListingRecord]:
        all_records: list[ListingRecord] = []

        for page_num in range(1, MAX_PAGES + 1):
            separator = "&" if "?" in base_url else "?"
            url = f"{base_url}{separator}p={page_num}"

            if DEBUG:
                print(f"\n=== {district} | страница {page_num}: {url}")

            context = browser.new_context(
                viewport={"width": 1440, "height": 2200},
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/123.0.0.0 Safari/537.36"
                ),
                locale="ru-RU",
            )
            page = context.new_page()
            page.set_default_timeout(REQUEST_TIMEOUT_MS)

            try:
                page.goto(url, wait_until="domcontentloaded")
                page.wait_for_timeout(5000)

                self._soft_scroll(page)
                page.wait_for_timeout(3000)

                html = page.content()

                if DEBUG:
                    ids = re.findall(r"/rent/flat/(\d+)/", html)
                    unique_ids = list(dict.fromkeys(ids))
                    print(f"{district} страница {page_num}: первые 10 id {unique_ids[:10]}")

                records = self._extract_records(
                    html=html,
                    district=district,
                    source_page=url,
                )

                print(f"{district} страница {page_num}: найдено {len(records)}")
                all_records.extend(records)

                time.sleep(random.uniform(5, 10))

            except Exception as exc:
                print(f"Ошибка на странице {page_num}: {exc}")
                break

            finally:
                context.close()

        return all_records

    def _soft_scroll(self, page: Page) -> None:
        for _ in range(SCROLL_STEPS):
            page.mouse.wheel(0, 2500)
            time.sleep(SCROLL_PAUSE_SEC)

    def _extract_records(
        self,
        html: str,
        district: str,
        source_page: str,
    ) -> list[ListingRecord]:
        soup = BeautifulSoup(html, "lxml")
        anchors = soup.find_all("a", href=True)

        if DEBUG:
            hrefs = [a.get("href", "") for a in anchors]
            rent_hrefs = [h for h in hrefs if re.search(r"/rent/flat/\d+/", h)]
            print(f"{district}: всего ссылок <a> = {len(anchors)}")
            print(f"{district}: ссылок с /rent/flat/ = {len(rent_hrefs)}")
            if rent_hrefs[:5]:
                print(f"{district}: примеры ссылок: {rent_hrefs[:5]}")

        seen_ids: set[str] = set()
        records: list[ListingRecord] = []

        for anchor in anchors:
            href = anchor.get("href") or ""
            if not re.search(r"/rent/flat/\d+/", href):
                continue

            match = LISTING_ID_RE.search(href)
            if not match:
                continue

            listing_id = match.group(1)
            if listing_id in seen_ids:
                continue
            seen_ids.add(listing_id)

            card_text = self._collect_card_text(anchor)
            title = self._clean_text(anchor.get_text(" ", strip=True)) or "Без названия"
            url = urljoin("https://www.cian.ru", href)
            parsed = self._parse_card_text(card_text)

            records.append(
                ListingRecord(
                    listing_id=listing_id,
                    district=district,
                    url=url,
                    title=title,
                    price_rub=parsed["price_rub"],
                    area_m2=parsed["area_m2"],
                    floor=parsed["floor"],
                    total_floors=parsed["total_floors"],
                    metro=parsed["metro"],
                    address=parsed["address"],
                    description_snippet=parsed["description_snippet"],
                    source_page=source_page,
                    scraped_at=self.scraped_at,
                )
            )

        return records

    def _collect_card_text(self, anchor: Any) -> str:
        node = anchor

        for _ in range(7):
            parent = getattr(node, "parent", None)
            if parent is None:
                break

            text = self._clean_text(parent.get_text(" ", strip=True))
            if "₽" in text and len(text) >= 80:
                return text[:2500]

            node = parent

        return self._clean_text(anchor.get_text(" ", strip=True))

    def _parse_card_text(self, text: str) -> dict[str, Any]:
        cleaned = self._clean_text(text)
        lines = [part.strip() for part in re.split(r"\s{2,}|\n+", cleaned) if part.strip()]

        price_rub = None
        price_candidates: list[int] = []

        for match in re.finditer(r"(\d{2,3}(?:\s?\d{3})?)\s*₽", cleaned):
            value = int(re.sub(r"\D", "", match.group(1)))

            # Реалистичный диапазон месячной аренды студий в Москве.
            # Так мы отсекаем миллионы и прочие лишние числа из карточки.
            if 15000 <= value <= 500000:
                price_candidates.append(value)

        if price_candidates:
            price_rub = price_candidates[0]

        area_m2 = None
        area_match = AREA_RE.search(cleaned)
        if area_match:
            area_m2 = float(area_match.group(1).replace(",", "."))

        floor = None
        total_floors = None
        floor_match = FLOOR_RE.search(cleaned)
        if floor_match:
            floor = int(floor_match.group(1))
            total_floors = int(floor_match.group(2))

        metro = None
        address = None
        description_snippet = None

        for i, line in enumerate(lines):
            if re.search(r"минут", line, flags=re.IGNORECASE) and i > 0:
                candidate = lines[i - 1]
                if METRO_HINT_RE.match(candidate):
                    metro = candidate
                    break

        for line in lines:
            if "Москва" in line:
                address = line
                break

        skip_words = (
            "₽",
            "этаж",
            "Москва",
            "минут",
            "агентство",
            "риелтор",
            "документы проверены",
        )
        long_lines = [
            line
            for line in lines
            if len(line) > 70 and not any(word.lower() in line.lower() for word in skip_words)
        ]
        if long_lines:
            description_snippet = long_lines[0][:500]

        return {
            "price_rub": price_rub,
            "area_m2": area_m2,
            "floor": floor,
            "total_floors": total_floors,
            "metro": metro,
            "address": address,
            "description_snippet": description_snippet,
        }

    @staticmethod
    def _clean_text(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()