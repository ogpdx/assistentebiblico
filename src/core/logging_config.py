"""
Configuração centralizada de logging para o Assistente Bíblico.

Garante que:
- Logs são escritos em arquivo rotativo e no console.
- Tokens e dados sensíveis NUNCA aparecem nos logs.
- O formato é consistente em todos os módulos.
"""

import logging
import os
import re
from logging.handlers import RotatingFileHandler

from src.core.constants import LOG_FORMAT, LOG_DATE_FORMAT, LOG_MAX_BYTES, LOG_BACKUP_COUNT
from src.core.path_utils import get_user_logs_dir


class TokenFilter(logging.Filter):
    """Filtro que mascara tokens e dados sensíveis nos logs.

    Substitui padrões como 'token=abc123' por 'token=***' em todas
    as mensagens de log, evitando vazamento acidental de credenciais.
    """

    # Padrões que podem conter tokens
    _PATTERNS = [
        (re.compile(r"(token=)[^\s&\"']+", re.IGNORECASE), r"\1***"),
        (re.compile(r"(dtoken=)[^\s&\"']+", re.IGNORECASE), r"\1***"),
        (re.compile(r"(\"token\"\s*:\s*\")[^\"]+\"", re.IGNORECASE), r'\1***"'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in self._PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        if record.args:
            new_args = []
            for arg in (record.args if isinstance(record.args, tuple) else (record.args,)):
                if isinstance(arg, str):
                    for pattern, replacement in self._PATTERNS:
                        arg = pattern.sub(replacement, arg)
                new_args.append(arg)
            record.args = tuple(new_args) if isinstance(record.args, tuple) else new_args[0]
        return True


def setup_logging(level: int = logging.INFO) -> None:
    """Configura o sistema de logging do aplicativo.

    Args:
        level: Nível mínimo de log (padrão: INFO).
    """
    # Usa diretório de logs de usuário (%LOCALAPPDATA%/AssistenteBiblico/logs/)
    logs_dir = get_user_logs_dir()
    log_file = logs_dir / "assistente_biblico.log"

    # Formatter compartilhado
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

    # Filtro de segurança
    token_filter = TokenFilter()

    # Handler de arquivo rotativo
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(token_filter)

    # Handler de console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.addFilter(token_filter)

    # Configura root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove handlers existentes para evitar duplicação
    root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def get_logger(name: str) -> logging.Logger:
    """Obtém um logger nomeado com o filtro de segurança aplicado.

    Args:
        name: Nome do módulo (geralmente __name__).

    Returns:
        Logger configurado.
    """
    logger = logging.getLogger(name)
    # Garante que o filtro de token está aplicado
    if not any(isinstance(f, TokenFilter) for f in logger.filters):
        logger.addFilter(TokenFilter())
    return logger
