"""Tests for the transform module."""

from src.transform import Chapter, transform_features


def _make_feature(chapter_id="CA-0101", name="UC Davis", city="Davis",
                  state="CA", x=-121.74, y=38.54):
    return {
        "attributes": {
            "ChapterID": chapter_id,
            "University_Chapter": name,
            "City": city,
            "State": state,
        },
        "geometry": {"x": x, "y": y},
    }


def test_transform_valid_feature():
    features = [_make_feature()]
    result = transform_features(features)

    assert len(result) == 1
    assert isinstance(result[0], Chapter)
    assert result[0].chapter_id == "CA-0101"
    assert result[0].chapter_name == "UC Davis"
    assert result[0].city == "Davis"
    assert result[0].state == "CA"
    assert result[0].longitude == -121.74
    assert result[0].latitude == 38.54


def test_transform_skips_missing_attributes():
    features = [
        _make_feature(),
        {"attributes": {"ChapterID": None, "University_Chapter": "Bad"},
         "geometry": {"x": 0, "y": 0}},
    ]
    result = transform_features(features)
    assert len(result) == 1


def test_transform_skips_missing_geometry():
    features = [
        {"attributes": {
            "ChapterID": "CA-0102",
            "University_Chapter": "UCLA",
            "City": "Los Angeles",
            "State": "CA",
        }, "geometry": {}},
    ]
    result = transform_features(features)
    assert len(result) == 0


def test_transform_multiple_features():
    features = [
        _make_feature("CA-0101", "UC Davis", "Davis", "CA", -121.74, 38.54),
        _make_feature("CA-0102", "UCLA", "Los Angeles", "CA", -118.44, 34.07),
    ]
    result = transform_features(features)
    assert len(result) == 2
    assert {r.chapter_id for r in result} == {"CA-0101", "CA-0102"}


def test_transform_empty_list():
    assert transform_features([]) == []
