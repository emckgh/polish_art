"""Import reference artworks (known-looted) into the master DB.

Two input modes:

  --image-dir PATH   Import every image file in a directory. One artwork row
                     per image; title defaults to the filename stem.

  --csv PATH         Import from a CSV file. See data/reference_import_template.csv
                     for the expected columns.

Both modes compute phash/dhash/ahash and write an image_features row so the
scraper can use them as reference hashes immediately.

Duplicate detection: images already in the DB (matched by SHA-256 hash of the
raw bytes) are skipped.

Usage examples:
    python -m src.scripts.import_reference_artworks --image-dir new_images/
    python -m src.scripts.import_reference_artworks --csv data/my_import.csv
    python -m src.scripts.import_reference_artworks --csv data/my_import.csv --dry-run
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import logging
import sys
from datetime import datetime
from pathlib import Path
from uuid import uuid4

import imagehash
import requests
from PIL import Image
from sqlalchemy import create_engine, event, select, text
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.constants import ScraperConstants, get_database_url
from src.domain.entities import ArtworkStatus
from src.repositories.models import ArtworkModel, Base, ImageFeaturesModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("import_reference_artworks")

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".tiff", ".tif", ".bmp"}

_CSV_COLUMNS = [
    "title",
    "artist_name",
    "artist_birth_year",
    "artist_death_year",
    "artist_nationality",
    "creation_year",
    "description",
    "image_url",
    "image_path",
    "last_known_location",
    "source",
]


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

def _build_session_factory(db_url: str):
    engine = create_engine(db_url, connect_args={"timeout": 15})
    if db_url.startswith("sqlite"):
        event.listen(engine, "connect", _enable_wal)
    Base.metadata.create_all(engine, checkfirst=True)
    return sessionmaker(bind=engine)


def _enable_wal(dbapi_connection, _record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=10000")
    cursor.close()


def _known_hashes(session) -> set[str]:
    rows = session.execute(
        text("SELECT image_hash FROM artworks WHERE image_hash IS NOT NULL")
    ).fetchall()
    return {r[0] for r in rows}


# ---------------------------------------------------------------------------
# Image helpers
# ---------------------------------------------------------------------------

def _load_image_bytes(image_url: str | None, image_path: str | None) -> bytes | None:
    """Return raw bytes from a local path or remote URL, or None on failure."""
    if image_path:
        p = Path(image_path)
        if not p.exists():
            logger.warning("Local file not found: %s", image_path)
            return None
        return p.read_bytes()

    if image_url:
        try:
            resp = requests.get(
                image_url,
                timeout=ScraperConstants.REQUEST_TIMEOUT_SECONDS,
                headers={"User-Agent": ScraperConstants.USER_AGENT},
                stream=True,
            )
            if resp.status_code != 200:
                logger.warning("HTTP %d fetching %s", resp.status_code, image_url)
                return None
            return resp.content
        except Exception as exc:
            logger.warning("Failed to fetch %s: %s", image_url, exc)
            return None

    return None


def _compute_hashes(raw: bytes) -> tuple[str, str, str, str] | None:
    """Return (sha256_hex, phash, dhash, ahash) or None if image is unreadable."""
    try:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
        sha256 = hashlib.sha256(raw).hexdigest()
        phash = str(imagehash.phash(img))
        dhash = str(imagehash.dhash(img))
        ahash = str(imagehash.average_hash(img))
        return sha256, phash, dhash, ahash
    except Exception as exc:
        logger.warning("Could not decode image: %s", exc)
        return None


def _image_meta(raw: bytes) -> dict:
    """Return width, height, aspect_ratio, format, color_space, is_grayscale."""
    try:
        img = Image.open(io.BytesIO(raw))
        w, h = img.size
        return {
            "width_pixels": w,
            "height_pixels": h,
            "aspect_ratio": round(w / h, 4) if h else 0.0,
            "format": (img.format or "").lower()[:10],
            "color_space": img.mode,
            "is_grayscale": img.mode in ("L", "LA"),
        }
    except Exception:
        return {
            "width_pixels": 0,
            "height_pixels": 0,
            "aspect_ratio": 0.0,
            "format": "",
            "color_space": "",
            "is_grayscale": False,
        }


# ---------------------------------------------------------------------------
# Core insert
# ---------------------------------------------------------------------------

def _insert_artwork(
    session,
    *,
    title: str,
    artist_name: str | None,
    artist_birth_year: int | None,
    artist_death_year: int | None,
    artist_nationality: str | None,
    creation_year: int | None,
    description: str | None,
    image_url: str | None,
    image_path: str | None,
    last_known_location: str | None,
    raw: bytes | None,
    sha256: str | None,
    phash: str,
    dhash: str,
    ahash: str,
    meta: dict,
    dry_run: bool,
) -> bool:
    """Insert one artwork + image_features row. Returns True if inserted."""
    artwork_id = uuid4()
    mime = None
    if raw:
        ext = (image_path or "").rsplit(".", 1)[-1].lower() if image_path else ""
        mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                    "webp": "image/webp", "tiff": "image/tiff", "tif": "image/tiff"}
        mime = mime_map.get(ext, "image/jpeg")

    if not dry_run:
        session.add(ArtworkModel(
            id=artwork_id,
            title=title,
            artist_name=artist_name,
            artist_birth_year=artist_birth_year,
            artist_death_year=artist_death_year,
            artist_nationality=artist_nationality,
            creation_year=creation_year,
            description=description or "",
            status=ArtworkStatus.KNOWN_LOOTED,
            image_url=image_url,
            image_data=raw,
            image_mime_type=mime,
            image_hash=sha256,
            last_known_location=last_known_location,
            include_image_on_server=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        ))
        session.add(ImageFeaturesModel(
            id=uuid4(),
            artwork_id=artwork_id,
            phash=phash,
            dhash=dhash,
            ahash=ahash,
            width_pixels=meta["width_pixels"],
            height_pixels=meta["height_pixels"],
            aspect_ratio=meta["aspect_ratio"],
            format=meta["format"],
            file_size_bytes=len(raw) if raw else 0,
            color_space=meta["color_space"],
            is_grayscale=meta["is_grayscale"],
            model_version="import-v1",
            extraction_timestamp=datetime.utcnow(),
        ))
        session.commit()
    return True


# ---------------------------------------------------------------------------
# Import modes
# ---------------------------------------------------------------------------

def _import_image_dir(
    image_dir: Path,
    SessionFactory,
    dry_run: bool,
) -> tuple[int, int, int]:
    """Import all image files from a directory. Returns (inserted, skipped, errors)."""
    files = [
        f for f in sorted(image_dir.iterdir())
        if f.is_file() and f.suffix.lower() in _IMAGE_EXTENSIONS
    ]
    if not files:
        logger.warning("No image files found in %s", image_dir)
        return 0, 0, 0

    logger.info("Found %d image file(s) in %s", len(files), image_dir)

    with SessionFactory() as session:
        known = _known_hashes(session)

    inserted = skipped = errors = 0

    for path in files:
        raw = path.read_bytes()
        result = _compute_hashes(raw)
        if result is None:
            logger.warning("Skipping unreadable file: %s", path.name)
            errors += 1
            continue

        sha256, phash, dhash, ahash = result

        if sha256 in known:
            logger.info("SKIP (already in DB): %s", path.name)
            skipped += 1
            continue

        meta = _image_meta(raw)
        title = path.stem  # UUID stem or whatever the filename is

        action = "DRY-RUN" if dry_run else "INSERT"
        logger.info("%s: %s  [%dx%d  phash=%s]", action, path.name,
                    meta["width_pixels"], meta["height_pixels"], phash)

        with SessionFactory() as session:
            _insert_artwork(
                session,
                title=title,
                artist_name=None,
                artist_birth_year=None,
                artist_death_year=None,
                artist_nationality=None,
                creation_year=None,
                description=None,
                image_url=None,
                image_path=str(path),
                last_known_location=None,
                raw=raw,
                sha256=sha256,
                phash=phash,
                dhash=dhash,
                ahash=ahash,
                meta=meta,
                dry_run=dry_run,
            )

        known.add(sha256)
        inserted += 1

    return inserted, skipped, errors


def _import_csv(
    csv_path: Path,
    SessionFactory,
    dry_run: bool,
) -> tuple[int, int, int]:
    """Import artworks from a CSV file. Returns (inserted, skipped, errors)."""
    with SessionFactory() as session:
        known = _known_hashes(session)

    inserted = skipped = errors = 0

    with csv_path.open(newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    logger.info("Read %d row(s) from %s", len(rows), csv_path)

    for i, row in enumerate(rows, start=2):  # row 1 is the header
        title = row.get("title", "").strip()
        artist_name = row.get("artist_name", "").strip() or None
        image_url = row.get("image_url", "").strip() or None
        image_path_str = row.get("image_path", "").strip() or None

        if not title and not artist_name:
            logger.warning("Row %d: skipping — no title or artist_name", i)
            errors += 1
            continue

        if not title:
            title = f"[Work by {artist_name}]"

        raw = _load_image_bytes(image_url, image_path_str)
        if raw is None:
            logger.warning("Row %d (%s): no image available — inserting without image", i, title)

        sha256 = phash = dhash = ahash = None
        meta = _image_meta(b"")

        if raw:
            result = _compute_hashes(raw)
            if result is None:
                logger.warning("Row %d (%s): image unreadable — skipping", i, title)
                errors += 1
                continue
            sha256, phash, dhash, ahash = result

            if sha256 in known:
                logger.info("SKIP (already in DB): row %d — %s", i, title)
                skipped += 1
                continue

            meta = _image_meta(raw)

        def _int(val: str) -> int | None:
            try:
                return int(val.strip()) if val and val.strip() else None
            except ValueError:
                return None

        action = "DRY-RUN" if dry_run else "INSERT"
        logger.info("%s: row %d — %s", action, i, title)

        with SessionFactory() as session:
            _insert_artwork(
                session,
                title=title,
                artist_name=artist_name,
                artist_birth_year=_int(row.get("artist_birth_year", "")),
                artist_death_year=_int(row.get("artist_death_year", "")),
                artist_nationality=row.get("artist_nationality", "").strip() or None,
                creation_year=_int(row.get("creation_year", "")),
                description=row.get("description", "").strip() or None,
                image_url=image_url,
                image_path=image_path_str,
                last_known_location=row.get("last_known_location", "").strip() or None,
                raw=raw,
                sha256=sha256,
                phash=phash or "",
                dhash=dhash or "",
                ahash=ahash or "",
                meta=meta,
                dry_run=dry_run,
            )

        if sha256:
            known.add(sha256)
        inserted += 1

    return inserted, skipped, errors


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import reference artworks (known-looted) into the master DB."
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--image-dir",
        metavar="PATH",
        help="Directory of image files to import (one artwork per file).",
    )
    group.add_argument(
        "--csv",
        metavar="PATH",
        help="CSV file with artwork metadata. See data/reference_import_template.csv.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        help="Print what would be inserted without writing to the DB.",
    )
    args = parser.parse_args()

    db_url = get_database_url()
    if "mode=ro" in db_url:
        logger.error("READ_ONLY is active — cannot write. Unset READ_ONLY before importing.")
        sys.exit(1)

    SessionFactory = _build_session_factory(db_url)

    if args.image_dir:
        image_dir = Path(args.image_dir)
        if not image_dir.is_dir():
            logger.error("Not a directory: %s", image_dir)
            sys.exit(1)
        inserted, skipped, errors = _import_image_dir(image_dir, SessionFactory, args.dry_run)
    else:
        csv_path = Path(args.csv)
        if not csv_path.exists():
            logger.error("CSV not found: %s", csv_path)
            sys.exit(1)
        inserted, skipped, errors = _import_csv(csv_path, SessionFactory, args.dry_run)

    suffix = " (dry run — nothing written)" if args.dry_run else ""
    print(f"\nDone{suffix}: {inserted} inserted, {skipped} skipped (duplicate), {errors} errors.")


if __name__ == "__main__":
    main()
