# Módulo holyrics - Integração com Holyrics API Server
from src.holyrics.client import HolyricsClient
from src.holyrics.api import HolyricsAPI
from src.holyrics.exceptions import (
    HolyricsError,
    HolyricsConnectionError,
    HolyricsTimeoutError,
    HolyricsAuthError,
    HolyricsPermissionError,
    HolyricsAPIError,
)

__all__ = [
    "HolyricsClient",
    "HolyricsAPI",
    "HolyricsError",
    "HolyricsConnectionError",
    "HolyricsTimeoutError",
    "HolyricsAuthError",
    "HolyricsPermissionError",
    "HolyricsAPIError",
]
