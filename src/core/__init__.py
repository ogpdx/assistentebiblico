"""
Módulo core - Controlador e constantes.
"""

from src.core.constants import (
    APP_NAME,
    APP_VERSION,
    APP_DESCRIPTION,
    DEFAULT_HOLYRICS_HOST,
    DEFAULT_HOLYRICS_PORT,
    DEFAULT_HOLYRICS_TIMEOUT,
    HolyricsActions,
    VERSE_ID_FORMAT,
)
from src.core.logging_config import setup_logging, get_logger
from src.core.controller import VoiceHolyricsController, ExecutionResult

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "APP_DESCRIPTION",
    "DEFAULT_HOLYRICS_HOST",
    "DEFAULT_HOLYRICS_PORT",
    "DEFAULT_HOLYRICS_TIMEOUT",
    "HolyricsActions",
    "VERSE_ID_FORMAT",
    "setup_logging",
    "get_logger",
    "VoiceHolyricsController",
    "ExecutionResult",
]
