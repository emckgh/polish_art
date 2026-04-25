"""Orchestrates the auction-house / gallery crawl cycle.

Responsibilities:
  - Load active ScraperTargets due for a crawl
  - Gather all known-looted phashes from image_features as reference
  - Run AuctionSpider per target
  - Persist ScrapedURL rows (dedup via url_hash), committing after every URL
  - Create Artwork stubs for interesting finds and re-download image bytes
  - Update target.last_scraped_at
"""
from __future__ import annotations

import hashlib
import logging
import urllib.parse
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID, uuid4

import requests
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import Session, sessionmaker

from src.constants import ScraperConstants
from src.domain.entities import ArtworkStatus, ScrapedURL, ScraperTarget
from src.repositories.models import (
    ArtworkModel,
    Base,
    ImageFeaturesModel,
    ScrapedURLModel,
    ScraperTargetModel,
)
from src.scrapers.auction_spider import AuctionSpider

logger = logging.getLogger(__name__)


def _enable_wal(dbapi_connection, connection_record):
    """Enable WAL mode so SQLite allows concurrent reads during writes."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=10000")  # 10 s retry on locked
    cursor.close()


class ScraperService:
    """Run weekly crawls for all due scraper targets."""

    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url, connect_args={"timeout": 15})
        if database_url.startswith("sqlite"):
            event.listen(self._engine, "connect", _enable_wal)
        Base.metadata.create_all(self._engine, checkfirst=True)
        self._SessionFactory = sessionmaker(bind=self._engine)
        self._spider = AuctionSpider()

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def run_due_targets(self, force: bool = False) -> dict[str, int]:
        """Crawl all active targets whose next-scrape time has passed.

        Returns mapping target_name → interesting_images_found.
        """
        results: dict[str, int] = {}

        # Load reference data once (read-only session)
        with self._SessionFactory() as session:
            targets = self._load_due_targets(session, force)
            reference_phashes = self._load_reference_phashes(session)
            seen_hashes = self._load_seen_url_hashes(session)

        logger.info("Running scrape for %d target(s).", len(targets))
        logger.info("Loaded %d reference phashes.", len(reference_phashes))
        logger.info("Loaded %d already-seen URL hashes.", len(seen_hashes))

        for target in targets:
            count = self._crawl_target(target, seen_hashes, reference_phashes)
            results[target.name] = count

        return results

    def run_single_target(self, target_id: str, force: bool = True) -> int:
        """Crawl one specific target by ID. Returns interesting count."""
        with self._SessionFactory() as session:
            row = session.get(ScraperTargetModel, UUID(target_id))
            if row is None:
                raise ValueError(f"Target not found: {target_id}")
            target = _model_to_target(row)
            reference_phashes = self._load_reference_phashes(session)
            seen_hashes = self._load_seen_url_hashes(session)

        return self._crawl_target(target, seen_hashes, reference_phashes)

    # ------------------------------------------------------------------
    # Private — crawl one target
    # ------------------------------------------------------------------

    def _crawl_target(
        self,
        target: ScraperTarget,
        seen_hashes: set[str],
        reference_phashes: list[str],
    ) -> int:
        """Run spider for one target; commit each URL individually."""
        interesting_count = 0
        url_count = 0

        for scraped_url in self._spider.crawl(target, seen_hashes, reference_phashes):
            url_count += 1
            try:
                with self._SessionFactory() as session:
                    self._persist_scraped_url(session, scraped_url)

                    if scraped_url.was_interesting:
                        artwork_id = self._create_artwork_stub(
                            session, scraped_url.url, scraped_url.image_phash or ""
                        )
                        if artwork_id:
                            su_row = session.execute(
                                select(ScrapedURLModel).where(
                                    ScrapedURLModel.url_hash == scraped_url.url_hash
                                )
                            ).scalar_one_or_none()
                            if su_row:
                                su_row.artwork_id = UUID(artwork_id)
                            interesting_count += 1

                    session.commit()
            except Exception as exc:
                logger.warning(
                    "Failed to persist URL for %s: %s", scraped_url.url, exc
                )

        # Mark target as scraped in its own short transaction
        try:
            with self._SessionFactory() as session:
                row = session.get(ScraperTargetModel, target.id)
                if row:
                    row.last_scraped_at = datetime.utcnow()
                session.commit()
        except Exception as exc:
            logger.warning("Could not update last_scraped_at for %s: %s", target.name, exc)

        logger.info(
            "Done %s — %d URLs processed, %d interesting.",
            target.name,
            url_count,
            interesting_count,
        )
        return interesting_count

    def _persist_scraped_url(self, session: Session, su: ScrapedURL) -> None:
        """Insert or touch a ScrapedURL row (no commit — caller commits)."""
        existing = session.execute(
            select(ScrapedURLModel).where(ScrapedURLModel.url_hash == su.url_hash)
        ).scalar_one_or_none()

        if existing:
            existing.last_seen_at = datetime.utcnow()
            if su.was_interesting and not existing.was_interesting:
                existing.was_interesting = True
                existing.discarded_image = False
        else:
            session.add(
                ScrapedURLModel(
                    id=su.id,
                    url=su.url,
                    url_hash=su.url_hash,
                    domain=su.domain,
                    target_id=su.target_id,
                    first_seen_at=su.first_seen_at,
                    last_seen_at=su.last_seen_at,
                    image_phash=su.image_phash,
                    was_interesting=su.was_interesting,
                    discarded_image=su.discarded_image,
                    artwork_id=None,
                )
            )

    def _create_artwork_stub(
        self, session: Session, img_url: str, phash: str
    ) -> Optional[str]:
        """Download image bytes and create a minimal Artwork + Features row."""
        try:
            resp = requests.get(
                img_url,
                timeout=ScraperConstants.REQUEST_TIMEOUT_SECONDS,
                headers={"User-Agent": ScraperConstants.USER_AGENT},
                stream=True,
            )
            if resp.status_code != 200:
                return None

            content_type = resp.headers.get("content-type", "image/jpeg")
            if not content_type.startswith("image/"):
                return None

            raw = resp.content
            image_hash = hashlib.sha256(raw).hexdigest()
            domain = urllib.parse.urlparse(img_url).netloc
            artwork_id = uuid4()

            session.add(
                ArtworkModel(
                    id=artwork_id,
                    title=f"[Candidate from {domain}]",
                    status=ArtworkStatus.SUSPECTED,
                    image_url=img_url,
                    image_data=raw,
                    image_mime_type=content_type,
                    image_hash=image_hash,
                    include_image_on_server=True,
                )
            )
            session.add(
                ImageFeaturesModel(
                    id=uuid4(),
                    artwork_id=artwork_id,
                    phash=phash,
                    dhash=phash,
                    ahash=phash,
                    width_pixels=0,
                    height_pixels=0,
                    aspect_ratio=0.0,
                    format="",
                    file_size_bytes=len(raw),
                    model_version="spider-v1",
                )
            )
            return str(artwork_id)

        except Exception as exc:
            logger.warning("Failed to create artwork stub for %s: %s", img_url, exc)
            return None

    # ------------------------------------------------------------------
    # Loaders
    # ------------------------------------------------------------------

    def _load_due_targets(self, session: Session, force: bool) -> list[ScraperTarget]:
        rows = (
            session.execute(
                select(ScraperTargetModel).where(ScraperTargetModel.is_active == True)
            )
            .scalars()
            .all()
        )
        now = datetime.utcnow()
        due: list[ScraperTarget] = []
        for row in rows:
            target = _model_to_target(row)
            if force or row.last_scraped_at is None:
                due.append(target)
                continue
            if now >= row.last_scraped_at + timedelta(days=target.scrape_frequency_days):
                due.append(target)
        return due

    def _load_reference_phashes(self, session: Session) -> list[str]:
        rows = session.execute(
            text("SELECT phash FROM image_features WHERE phash IS NOT NULL AND phash != ''")
        ).fetchall()
        return [r[0] for r in rows]

    def _load_seen_url_hashes(self, session: Session) -> set[str]:
        rows = session.execute(
            text(
                "SELECT url_hash FROM scraped_urls "
                "WHERE was_interesting = 0 OR was_interesting IS NULL"
            )
        ).fetchall()
        return {r[0] for r in rows}


def _model_to_target(row: ScraperTargetModel) -> ScraperTarget:
    return ScraperTarget(
        id=row.id,
        name=row.name,
        base_url=row.base_url,
        category=row.category,
        country=row.country,
        scrape_frequency_days=row.scrape_frequency_days,
        last_scraped_at=row.last_scraped_at,
        is_active=row.is_active,
        notes=row.notes,
    )
