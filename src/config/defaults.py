"""
Valores padrão para configurações do Assistente Bíblico.

Este módulo define a estrutura completa de configuração com valores
iniciais seguros. O arquivo config.json do usuário sobrescreve
apenas os valores alterados.
"""

from src.core.constants import (
    DEFAULT_HOLYRICS_HOST,
    DEFAULT_HOLYRICS_PORT,
    DEFAULT_HOLYRICS_TIMEOUT,
)

DEFAULT_CONFIG: dict = {
    "holyrics": {
        "host": DEFAULT_HOLYRICS_HOST,
        "port": DEFAULT_HOLYRICS_PORT,
        "token": "",
        "timeout": DEFAULT_HOLYRICS_TIMEOUT,
    },
    "voice": {
        "model": "small",
        "language": "pt",
        "device_index": None,
        "sample_rate": 16000,
        "vad_threshold": 0.5,
    },
    "app": {
        "send_mode": "manual",  # "manual" ou "automatic"
        "default_bible_version": "",
        "log_level": "INFO",
        "history_max_items": 100,
    },
}
