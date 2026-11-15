"""
Fixtures compartilhadas para testes automatizados.
"""

import pytest

from src.config.settings import Settings
from src.holyrics.client import HolyricsClient
from src.holyrics.api import HolyricsAPI


@pytest.fixture
def mock_settings(tmp_path):
    """Settings com arquivo temporário para testes."""
    config_file = tmp_path / "config.json"
    config_file.write_text(
        '{"holyrics": {"host": "localhost", "port": 8091, "token": "test_token_123"}}',
        encoding="utf-8",
    )
    return Settings(str(config_file))


@pytest.fixture
def holyrics_client():
    """HolyricsClient configurado para testes (não conecta de fato)."""
    return HolyricsClient(
        host="localhost",
        port=8091,
        token="test_token_123",
        timeout=5.0,
    )


@pytest.fixture
def holyrics_api(holyrics_client):
    """HolyricsAPI com cliente mockável."""
    return HolyricsAPI(holyrics_client)
