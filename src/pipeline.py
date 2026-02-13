"""Orchestrates the ETL pipeline: Extract -> Transform -> Load."""

import logging
import sys

from src.config import load_api_config, load_db_config
from src.extract import fetch_chapters
from src.load import ensure_table, load_chapters
from src.transform import transform_features

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


def run() -> None:
    """Execute the full ETL pipeline."""
    logger.info("Starting DU University Chapters ETL pipeline")

    api_config = load_api_config()
    db_config = load_db_config()

    # Extract
    raw_features = fetch_chapters(api_config)

    # Transform
    chapters = transform_features(raw_features)

    # Load
    ensure_table(db_config)
    rows_loaded = load_chapters(db_config, chapters)

    logger.info("Pipeline complete — %d rows loaded", rows_loaded)


def main() -> None:
    try:
        run()
    except Exception:
        logger.exception("Pipeline failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
