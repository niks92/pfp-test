"""Tests for the extract module."""

import pytest
import responses

from src.config import APIConfig
from src.extract import fetch_chapters

SAMPLE_RESPONSE = {
    "features": [
        {
            "attributes": {
                "OBJECTID": 1,
                "University_Chapter": "UC Davis",
                "City": "Davis",
                "State": "CA",
                "ChapterID": "CA-0101",
                "MEVR_RD": "Test Director",
            },
            "geometry": {"x": -121.7405, "y": 38.5449},
        }
    ]
}


@responses.activate
def test_fetch_chapters_returns_features():
    config = APIConfig()
    responses.add(
        responses.GET,
        config.base_url,
        json=SAMPLE_RESPONSE,
        status=200,
    )

    features = fetch_chapters(config)
    assert len(features) == 1
    assert features[0]["attributes"]["State"] == "CA"


@responses.activate
def test_fetch_chapters_raises_on_api_error():
    config = APIConfig()
    responses.add(
        responses.GET,
        config.base_url,
        json={"error": {"code": 400, "message": "Bad request"}},
        status=200,
    )

    with pytest.raises(ValueError, match="API returned error"):
        fetch_chapters(config)


@responses.activate
def test_fetch_chapters_raises_on_http_error():
    config = APIConfig()
    responses.add(
        responses.GET,
        config.base_url,
        json={"error": "server error"},
        status=500,
    )

    with pytest.raises(Exception):
        fetch_chapters(config)


@responses.activate
def test_fetch_chapters_empty_response():
    config = APIConfig()
    responses.add(
        responses.GET,
        config.base_url,
        json={"features": []},
        status=200,
    )

    features = fetch_chapters(config)
    assert features == []
