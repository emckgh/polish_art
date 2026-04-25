"""Export evaluator feedback as JSONL for LLM fine-tuning.

Usage:
    python -m src.scripts.export_feedback_for_llm
    python -m src.scripts.export_feedback_for_llm --output data/feedback_export.jsonl
    python -m src.scripts.export_feedback_for_llm --not-a-match-only --output data/negatives.jsonl

Each output line is a JSON object:
    {
        "feedback_id": "...",
        "artwork_id": "...",
        "artwork_title": "...",
        "artwork_status": "suspected",
        "image_url": "...",           # original or scraper-found URL
        "scraped_url": "...",         # URL where the image was found (if from crawler)
        "image_phash": "...",
        "not_a_match": true,
        "comment": "Clearly a different style; 18th century not mid-20th",
        "created_by": null,
        "created_at": "2026-04-13T12:00:00"
    }

These rows can be used directly as negative-example training data for an
LLM classifier or ranker:  feed the comment as the label rationale, and
the artwork metadata + image URL as the context.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.constants import get_database_url
from src.repositories.models import (
    ArtworkModel,
    Base,
    EvaluatorFeedbackModel,
    ScrapedURLModel,
)


def export(
    output_path: Path,
    not_a_match_only: bool = False,
    db_url: str | None = None,
) -> int:
    """Write feedback rows to JSONL. Returns the number of rows written."""
    url = db_url or get_database_url()
    engine = create_engine(url)
    Base.metadata.create_all(engine, checkfirst=True)

    written = 0
    with Session(engine) as session, open(output_path, "w", encoding="utf-8") as fh:
        q = session.query(EvaluatorFeedbackModel)
        if not_a_match_only:
            q = q.filter(EvaluatorFeedbackModel.not_a_match == True)

        for fb in q.all():
            artwork = session.get(ArtworkModel, fb.artwork_id)
            scraped = (
                session.get(ScrapedURLModel, fb.scraped_url_id)
                if fb.scraped_url_id
                else None
            )

            record = {
                "feedback_id": str(fb.id),
                "artwork_id": str(fb.artwork_id),
                "artwork_title": artwork.title if artwork else None,
                "artwork_status": artwork.status.value if artwork else None,
                "image_url": artwork.image_url if artwork else None,
                "scraped_url": scraped.url if scraped else None,
                "image_phash": scraped.image_phash if scraped else (
                    artwork.image_hash if artwork else None
                ),
                "not_a_match": fb.not_a_match,
                "comment": fb.comment,
                "created_by": fb.created_by,
                "created_at": (
                    fb.created_at.isoformat()
                    if isinstance(fb.created_at, datetime)
                    else str(fb.created_at)
                ),
            }
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1

    return written


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export evaluator feedback to JSONL for LLM training."
    )
    parser.add_argument(
        "--output",
        default="data/feedback_export.jsonl",
        help="Output file path (default: data/feedback_export.jsonl)",
    )
    parser.add_argument(
        "--not-a-match-only",
        action="store_true",
        default=False,
        help="Only export rows where not_a_match=True",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    count = export(output_path, not_a_match_only=args.not_a_match_only)
    print(f"Exported {count} feedback record(s) to {output_path}")


if __name__ == "__main__":
    main()
