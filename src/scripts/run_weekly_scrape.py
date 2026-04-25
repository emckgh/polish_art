"""Weekly auction-house / gallery crawl runner.

Designed to be called by a cron job or systemd timer.

Usage (manual):
    python -m src.scripts.run_weekly_scrape
    python -m src.scripts.run_weekly_scrape --force
    python -m src.scripts.run_weekly_scrape --target-id <uuid>
    python -m src.scripts.run_weekly_scrape --seed

Cron example (run every Monday at 03:00):
    0 3 * * 1 cd /home/polishart/polish_art && \
        ./venv/bin/python -m src.scripts.run_weekly_scrape >> logs/scrape.log 2>&1

Systemd timer: see docs/deploy-vps.md for a full service + timer unit example.

Environment variables respected (same as the main app):
    DATABASE_URL   — SQLite or PostgreSQL connection string
    READ_ONLY      — must be unset or "false" for writes to work
"""
from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Allow running as: python -m src.scripts.run_weekly_scrape
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.constants import get_database_url
from src.scripts.seed_scraper_targets import seed as seed_targets
from src.services.scraper_service import ScraperService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_weekly_scrape")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the weekly auction-house / gallery crawl."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=False,
        help="Ignore scrape_frequency_days; crawl all active targets now.",
    )
    parser.add_argument(
        "--target-id",
        metavar="UUID",
        default=None,
        help="Crawl a single target by its UUID (implies --force).",
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        default=False,
        help="Seed scraper_targets from data/scraper_targets.json before crawling.",
    )
    args = parser.parse_args()

    db_url = get_database_url()
    if "mode=ro" in db_url:
        logger.error(
            "READ_ONLY mode is active — cannot write crawl results. "
            "Unset READ_ONLY env var before running the scraper."
        )
        sys.exit(1)

    if args.seed:
        logger.info("Seeding scraper targets from JSON…")
        inserted = seed_targets(db_url)
        logger.info("Seeded %d new target(s).", inserted)

    service = ScraperService(db_url)
    start = time.time()

    if args.target_id:
        logger.info("Crawling single target: %s (forced)", args.target_id)
        count = service.run_single_target(args.target_id, force=True)
        logger.info("Done — %d interesting image(s) found.", count)
    else:
        logger.info(
            "Starting %s crawl at %s",
            "forced" if args.force else "scheduled",
            datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        )
        results = service.run_due_targets(force=args.force)
        total_interesting = sum(results.values())
        elapsed = time.time() - start
        logger.info(
            "Crawl complete in %.1fs — %d target(s) processed, "
            "%d interesting image(s) found.",
            elapsed,
            len(results),
            total_interesting,
        )
        for name, count in sorted(results.items()):
            logger.info("  %-50s  %d interesting", name, count)


if __name__ == "__main__":
    main()
