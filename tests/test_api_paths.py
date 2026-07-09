"""Tests for API path helpers."""

from src.core.config import Settings
from src.utils.api_paths import build_api_path


def test_build_api_path():
    settings = Settings(API_V1_STR="/mock/api")
    assert build_api_path("notes", settings) == "/mock/api/notes"


def test_build_api_path_strips_slashes():
    settings = Settings(API_V1_STR="/api/v1/")
    assert build_api_path("/ping", settings) == "/api/v1/ping"
