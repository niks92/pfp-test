"""Transform stage — normalise raw API features into clean records."""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class Chapter:
    """A single university chapter record ready for loading."""

    chapter_id: str
    chapter_name: str
    city: str
    state: str
    longitude: float
    latitude: float


def transform_features(raw_features: list[dict[str, Any]]) -> list[Chapter]:
    """Convert raw ArcGIS feature dicts into Chapter objects.

    Records with missing mandatory fields are logged and skipped.
    """
    chapters: list[Chapter] = []

    for feature in raw_features:
        attrs = feature.get("attributes", {})
        geometry = feature.get("geometry", {})

        chapter_id = attrs.get("ChapterID")
        chapter_name = attrs.get("University_Chapter")
        city = attrs.get("City")
        state = attrs.get("State")
        longitude = geometry.get("x")
        latitude = geometry.get("y")

        if not all([chapter_id, chapter_name, city, state]):
            logger.warning("Skipping feature with missing attributes: %s", attrs)
            continue

        if longitude is None or latitude is None:
            logger.warning(
                "Skipping feature with missing coordinates: %s", chapter_id
            )
            continue

        chapters.append(
            Chapter(
                chapter_id=chapter_id,
                chapter_name=chapter_name,
                city=city,
                state=state,
                longitude=float(longitude),
                latitude=float(latitude),
            )
        )

    logger.info("Transformed %d / %d features", len(chapters), len(raw_features))
    return chapters
