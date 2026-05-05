from __future__ import annotations

from src.analysis import build_all_artifacts
from src.config import DB_PATH
from src.db import get_connection, init_db, insert_listings
from src.scraper import CianScraper


def run_once() -> None:
    scraper = CianScraper()
    records = scraper.scrape_all()

    conn = get_connection(DB_PATH)
    try:
        init_db(conn)
        inserted = insert_listings(conn, records)
        build_all_artifacts(conn, scraper.scraped_at)
    finally:
        conn.close()

    print(f'Всего найдено записей: {len(records)}')
    print(f'Новых записей добавлено в БД: {inserted}')
    print(f'Снимок запуска: {scraper.scraped_at}')
    print(f'База данных: {DB_PATH}')


if __name__ == '__main__':
    run_once()
