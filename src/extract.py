"""Extract stage — fetch university chapter data from the Ducks Unlimited API."""

import logging
from typing import Any

import requests

from src.config import APIConfig

logger = logging.getLogger(__name__)


def fetch_chapters(config: APIConfig) -> list[dict[str, Any]]:
    """Query the ArcGIS Feature Service and return raw feature dicts.

    Raises:
        requests.HTTPError: On non-2xx responses.
        ValueError: If the API returns an error payload or no features.
    """
    params = {
        "where": f"State='{config.state_filter}'",
        "outFields": config.out_fields,
        "outSR": config.spatial_ref,
        "f": "json",
        "returnGeometry": "true",
    }

    logger.info(
        "Requesting chapters from API (state=%s)", config.state_filter
    )
    response = requests.get(
        config.base_url, params=params, timeout=config.timeout_seconds
    )
    response.raise_for_status()

    payload = response.json()

    if "error" in payload:
        raise ValueError(f"API returned error: {payload['error']}")

    features = payload.get("features", [])
    logger.info("Extracted %d features from API", len(features))

    if not features:
        logger.warning("No features returned for state=%s", config.state_filter)

    return features
