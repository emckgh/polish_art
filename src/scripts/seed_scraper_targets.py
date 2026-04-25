"""Load scraper_targets.json into the scraper_targets database table.

Usage:
    python -m src.scripts.seed_scraper_targets

Run once after initial deployment (or re-run to add missing rows; existing
rows are skipped based on base_url uniqueness).
"""
import json
import os
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

# Allow running as: python -m src.scripts.seed_scraper_targets
_PROJECT_ROOT = Path(__file__).resolve().parents[2]  # src/scripts -> src -> project root
sys.path.insert(0, str(_PROJECT_ROOT))

from src.constants import get_database_url
from src.repositories.models import Base, ScraperTargetModel


_DATA_FILE = _PROJECT_ROOT / "data" / "scraper_targets.json"


def _ensure_tables(engine) -> None:
    Base.metadata.create_all(engine, checkfirst=True)


def seed(db_url: str | None = None) -> int:
    """Insert targets from JSON that are not already in the database.

    Returns the number of rows inserted.
    """
    url = db_url or get_database_url()
    engine = create_engine(url)
    _ensure_tables(engine)

    with open(_DATA_FILE, encoding="utf-8") as fh:
        targets = json.load(fh)

    inserted = 0
    with Session(engine) as session:
        existing_urls = {
            row[0]
            for row in session.execute(
                text("SELECT base_url FROM scraper_targets")
            )
        }
        for t in targets:
            if t["base_url"] in existing_urls:
                continue
            session.add(
                ScraperTargetModel(
                    name=t["name"],
                    base_url=t["base_url"],
                    category=t["category"],
                    country=t.get("country"),
                    scrape_frequency_days=t.get("scrape_frequency_days", 7),
                    is_active=t.get("is_active", True),
                    notes=t.get("notes"),
                )
            )
            inserted += 1
        session.commit()

    return inserted


def main() -> None:
    count = seed()
    print(f"Inserted {count} new scraper target(s).")


if __name__ == "__main__":
    main()
