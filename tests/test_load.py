"""Tests for the load module — uses mocking to avoid a real database."""

from unittest.mock import MagicMock, patch

from src.config import DBConfig
from src.load import load_chapters
from src.transform import Chapter

SAMPLE_CHAPTERS = [
    Chapter("CA-0101", "UC Davis", "Davis", "CA", -121.74, 38.54),
    Chapter("CA-0102", "UCLA", "Los Angeles", "CA", -118.44, 34.07),
]

DB_CONFIG = DBConfig(
    host="localhost", port=5432, name="test", user="test", password="test"
)


@patch("src.load.execute_values")
@patch("src.load.psycopg2.connect")
def test_load_chapters_executes_upsert(mock_connect, mock_exec):
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_connect.return_value.__enter__ = MagicMock(return_value=mock_conn)
    mock_connect.return_value.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cur)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    rows = load_chapters(DB_CONFIG, SAMPLE_CHAPTERS)
    assert rows == 2
    mock_exec.assert_called_once()


def test_load_chapters_empty_list_returns_zero():
    rows = load_chapters(DB_CONFIG, [])
    assert rows == 0
