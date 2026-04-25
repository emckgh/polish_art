"""Auction-house / gallery web crawler.

Crawls a single ScraperTarget, extracts image URLs from listing pages,
deduplicates via SHA-256 URL hash, downloads only unseen or interesting
images, runs phash comparison against known-looted artworks, and persists
results — discarding image bytes for non-matches to save disk space.
"""
from __future__ import annotations

import hashlib
import io
import logging
import time
import urllib.parse
from dataclasses import dataclass
from datetime import datetime
from typing import Iterator, Optional
from uuid import uuid4

import requests
from bs4 import BeautifulSoup
from PIL import Image
import imagehash

from src.constants import ImageDownloadConstants, ScraperConstants
from src.domain.entities import Artwork, ArtworkStatus, ScrapedURL, ScraperTarget

logger = logging.getLogger(__name__)

_IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tiff", ".tif"}


@dataclass
class CrawlResult:
    """Summary of a single target crawl."""

    target_id: str
    pages_visited: int = 0
    images_found: int = 0
    images_skipped_cached: int = 0
    images_downloaded: int = 0
    images_interesting: int = 0
    images_discarded: int = 0
    errors: int = 0


class AuctionSpider:
    """Crawl one auction-house / gallery target for artwork images.

    Caller is responsible for:
      - providing the set of already-seen url_hashes (``seen_hashes``)
      - providing the list of known-looted phashes (``reference_phashes``)
      - persisting the yielded ``ScrapedURL`` objects
      - creating ``Artwork`` rows for interesting finds

    The spider itself is stateless beyond a ``requests.Session``.
    """

    def __init__(
        self,
        delay_seconds: float = ScraperConstants.DEFAULT_CRAWL_DELAY_SECONDS,
    ) -> None:
        self._delay = delay_seconds
        self._last_request: float = 0.0
        self._session = self._build_session()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def crawl(
        self,
        target: ScraperTarget,
        seen_hashes: set[str],
        reference_phashes: list[str],
    ) -> Iterator[ScrapedURL]:
        """Yield one ``ScrapedURL`` record for every image URL discovered.

        Non-matching images will have ``was_interesting=False`` and
        ``discarded_image=True``; the caller should NOT store image bytes
        for those.  Interesting images will have ``image_phash`` set and
        ``was_interesting=True``; the caller should create an Artwork row
        and store bytes.
        """
        result = CrawlResult(target_id=str(target.id))
        listing_urls = list(self._discover_listing_pages(target.base_url))

        for page_url in listing_urls[: ScraperConstants.MAX_PAGES_PER_TARGET]:
            try:
                soup = self._fetch_page(page_url)
                if soup is None:
                    result.errors += 1
                    continue
                result.pages_visited += 1

                img_urls = list(
                    self._extract_image_urls(soup, page_url)
                )[: ScraperConstants.MAX_IMAGES_PER_PAGE]

                for img_url in img_urls:
                    result.images_found += 1
                    url_hash = _sha256(img_url)

                    if url_hash in seen_hashes:
                        result.images_skipped_cached += 1
                        continue

                    seen_hashes.add(url_hash)
                    scraped = self._evaluate_image(
                        img_url, url_hash, target, reference_phashes
                    )
                    if scraped is None:
                        result.errors += 1
                        continue

                    result.images_downloaded += 1
                    if scraped.was_interesting:
                        result.images_interesting += 1
                    else:
                        result.images_discarded += 1

                    yield scraped

            except Exception as exc:
                logger.warning("Error on page %s: %s", page_url, exc)
                result.errors += 1

        logger.info(
            "Crawl complete for %s — pages=%d images=%d interesting=%d "
            "skipped=%d discarded=%d errors=%d",
            target.name,
            result.pages_visited,
            result.images_found,
            result.images_interesting,
            result.images_skipped_cached,
            result.images_discarded,
            result.errors,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _discover_listing_pages(self, base_url: str) -> Iterator[str]:
        """Yield candidate listing-page URLs for a site.

        Heuristic: start with the base URL; follow paginated hrefs that
        share the same netloc and look like listing pages (contain page/
        lot/auction/gallery in path or query params).
        """
        yield base_url

        try:
            soup = self._fetch_page(base_url)
            if soup is None:
                return

            base_netloc = urllib.parse.urlparse(base_url).netloc
            seen: set[str] = {base_url}

            for a in soup.find_all("a", href=True):
                href = a["href"].strip()
                full = urllib.parse.urljoin(base_url, href)
                parsed = urllib.parse.urlparse(full)

                if parsed.netloc != base_netloc:
                    continue
                if full in seen:
                    continue

                path_lower = parsed.path.lower()
                if any(
                    kw in path_lower
                    for kw in (
                        "/auction",
                        "/lot",
                        "/sale",
                        "/catalogue",
                        "/gallery",
                        "/artworks",
                        "/paintings",
                    )
                ):
                    seen.add(full)
                    yield full

        except Exception as exc:
            logger.debug("Discovery error for %s: %s", base_url, exc)

    def _fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch an HTML page, respecting crawl delay."""
        self._wait()
        try:
            resp = self._session.get(
                url, timeout=ScraperConstants.REQUEST_TIMEOUT_SECONDS
            )
            if resp.status_code != 200:
                logger.debug("HTTP %d for %s", resp.status_code, url)
                return None
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as exc:
            logger.debug("Fetch error %s: %s", url, exc)
            return None

    def _extract_image_urls(
        self, soup: BeautifulSoup, page_url: str
    ) -> Iterator[str]:
        """Yield image URLs from a parsed page."""
        base_netloc = urllib.parse.urlparse(page_url).netloc

        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
            if not src:
                continue

            full = urllib.parse.urljoin(page_url, src.strip())
            parsed = urllib.parse.urlparse(full)

            # Keep only same-domain or absolute http(s) images
            if parsed.scheme not in ("http", "https"):
                continue

            path_lower = parsed.path.lower()
            ext = "." + path_lower.rsplit(".", 1)[-1] if "." in path_lower else ""

            # Skip icons / logos / UI chrome by extension or tiny dimensions
            if ext and ext not in _IMG_EXTENSIONS:
                continue

            width = _parse_int(img.get("width"))
            height = _parse_int(img.get("height"))
            if width and width < ScraperConstants.MIN_IMAGE_DIMENSION_PX:
                continue
            if height and height < ScraperConstants.MIN_IMAGE_DIMENSION_PX:
                continue

            yield full

    def _evaluate_image(
        self,
        img_url: str,
        url_hash: str,
        target: ScraperTarget,
        reference_phashes: list[str],
    ) -> Optional[ScrapedURL]:
        """Download image, compute phash, decide if interesting.

        Returns a ``ScrapedURL``; image bytes are NOT returned — the caller
        creates an Artwork row with bytes only when ``was_interesting=True``
        and re-downloads (or caches) the bytes separately.  This keeps the
        spider itself lean.
        """
        self._wait()
        try:
            resp = self._session.get(
                img_url,
                timeout=ScraperConstants.REQUEST_TIMEOUT_SECONDS,
                stream=True,
            )
            if resp.status_code != 200:
                return None

            content_type = resp.headers.get("content-type", "")
            if not content_type.startswith("image/"):
                return None

            raw = resp.content
            phash_str = _compute_phash(raw)
            if phash_str is None:
                return None

            interesting = _is_match(phash_str, reference_phashes)
            domain = urllib.parse.urlparse(img_url).netloc

            return ScrapedURL(
                id=uuid4(),
                url=img_url,
                url_hash=url_hash,
                domain=domain,
                target_id=target.id,
                first_seen_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
                image_phash=phash_str,
                was_interesting=interesting,
                discarded_image=not interesting,
                artwork_id=None,
            )

        except Exception as exc:
            logger.debug("Image eval error %s: %s", img_url, exc)
            return None

    def _build_session(self) -> requests.Session:
        s = requests.Session()
        s.headers.update({"User-Agent": ScraperConstants.USER_AGENT})
        return s

    def _wait(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < self._delay:
            time.sleep(self._delay - elapsed)
        self._last_request = time.time()


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def _compute_phash(raw: bytes) -> Optional[str]:
    """Return hex phash string for image bytes, or None on failure."""
    try:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        return str(imagehash.phash(img))
    except Exception:
        return None


def _is_match(phash_str: str, reference_phashes: list[str]) -> bool:
    """True if phash is within threshold of any reference phash."""
    try:
        candidate = imagehash.hex_to_hash(phash_str)
    except Exception:
        return False

    for ref_str in reference_phashes:
        try:
            ref = imagehash.hex_to_hash(ref_str)
            if abs(candidate - ref) <= ScraperConstants.PHASH_MATCH_THRESHOLD:
                return True
        except Exception:
            continue
    return False


def _parse_int(value: Optional[str]) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None
