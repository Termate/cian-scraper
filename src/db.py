from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

from src.models import ListingRecord


def get_connection(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute('PRAGMA foreign_keys = ON;')
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        '''
        CREATE TABLE IF NOT EXISTS listings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_id TEXT NOT NULL,
            district TEXT NOT NULL,
            url TEXT NOT NULL,
            title TEXT NOT NULL,
            price_rub INTEGER,
            area_m2 REAL,
            floor INTEGER,
            total_floors INTEGER,
            metro TEXT,
            address TEXT,
            description_snippet TEXT,
            source_page TEXT NOT NULL,
            scraped_at TEXT NOT NULL,
            UNIQUE(listing_id, scraped_at)
        );

        CREATE INDEX IF NOT EXISTS idx_listings_scraped_at ON listings(scraped_at);
        CREATE INDEX IF NOT EXISTS idx_listings_district ON listings(district);
        CREATE INDEX IF NOT EXISTS idx_listings_listing_id ON listings(listing_id);
        '''
    )
    conn.commit()


def insert_listings(conn: sqlite3.Connection, rows: Iterable[ListingRecord]) -> int:
    inserted = 0
    for row in rows:
        cursor = conn.execute(
            '''
            INSERT OR IGNORE INTO listings (
                listing_id, district, url, title, price_rub, area_m2, floor, total_floors,
                metro, address, description_snippet, source_page, scraped_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                row.listing_id,
                row.district,
                row.url,
                row.title,
                row.price_rub,
                row.area_m2,
                row.floor,
                row.total_floors,
                row.metro,
                row.address,
                row.description_snippet,
                row.source_page,
                row.scraped_at,
            ),
        )
        inserted += cursor.rowcount
    conn.commit()
    return inserted
