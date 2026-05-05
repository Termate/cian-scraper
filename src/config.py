from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / 'data'
RAW_DIR = DATA_DIR / 'raw'
ARTIFACTS_DIR = DATA_DIR / 'artifacts'
EXPORTS_DIR = RAW_DIR / 'exports'
DB_PATH = RAW_DIR / 'cian_studios.db'

TARGET_PAGES: dict[str, str] = {
    # 'ВАО': 'https://www.cian.ru/snyat-kvartiru-studiu-moskva-vao-047/',
    "ЮВАО": "https://www.cian.ru/cat.php?deal_type=rent&district%5B0%5D=8&engine_version=2&offer_type=flat&room9=1&type=4"
}

REQUEST_TIMEOUT_MS = 60000
HEADLESS = False
SCROLL_STEPS = 5
SCROLL_PAUSE_SEC = 2.7
MAX_PAGES = 3
DEBUG = False

for path in (RAW_DIR, ARTIFACTS_DIR, EXPORTS_DIR):
    path.mkdir(parents=True, exist_ok=True)
