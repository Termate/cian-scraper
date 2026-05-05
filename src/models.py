from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class ListingRecord:
    listing_id: str
    district: str
    url: str
    title: str
    price_rub: Optional[int]
    area_m2: Optional[float]
    floor: Optional[int]
    total_floors: Optional[int]
    metro: Optional[str]
    address: Optional[str]
    description_snippet: Optional[str]
    source_page: str
    scraped_at: str
