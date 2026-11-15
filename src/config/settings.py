"""
Gerenciador de configurações do Assistente Bíblico.

Responsabilidades:
- Carregar configurações de config.json.
- Mesclar com valores padrão (defaults).
- Salvar alterações de volta ao arquivo.
- Proteger o token contra exposição.
- Validar valores críticos.
"""

import copy
import json
import os
from pathlib import Path
from typing import Any

from src.config.defaults import DEFAULT_CONFIG
from src.core.logging_config import get_logger
from src.core.path_utils import get_app_dir, get_user_config_dir, is_frozen

logger = get_logger(__name__)

# Caminho padrão do arquivo de configuração
_CONFIG_FILE = "config.json"
_CONFIG_EXAMPLE_FILE = "config.example.json"


def _deep_merge(base: dict, override: dict) -> dict:
    """Mescla dois dicionários recursivamente.

    Valores em 'override' sobrescrevem os de 'base'.
    Chaves presentes apenas em 'base' são preservadas.

    Args:
        base: Dicionário com valores padrão.
        override: Dicionário com valores do usuário.

    Returns:
        Dicionário mesclado.
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class Settings:
    """Gerenciador de configurações do aplicativo.

    Carrega configurações de um arquivo JSON, mescla com valores padrão
    e oferece acesso seguro aos valores.

    Attributes:
        config_path: Caminho absoluto do arquivo de configuração.
    """

    def __init__(self, config_path: str | None = None) -> None:
        """Inicializa o gerenciador de configurações.

        Estratégia de resolução:
        1. Se config_path for explicitamente informado, usa-o.
        2. Procura config.json na pasta do app/executável (prioridade para portabilidade).
        3. Procura config.json em %APPDATA%/AssistenteBiblico/config.json (usuário).
        4. Se não existir em nenhum, define como alvo o %APPDATA%/AssistenteBiblico/config.json.
        """
        if config_path:
            self.config_path = Path(config_path)
        else:
            # 1. Checa pasta do app / executável
            app_cfg = get_app_dir() / _CONFIG_FILE
            user_cfg = get_user_config_dir() / _CONFIG_FILE

            if app_cfg.exists():
                self.config_path = app_cfg
            elif user_cfg.exists():
                self.config_path = user_cfg
            else:
                # Se não existir em nenhum, o arquivo preferencial para gravação será o do usuário (ou do app se não-congelado)
                self.config_path = user_cfg if is_frozen() else app_cfg

        self._data: dict = copy.deepcopy(DEFAULT_CONFIG)
        self._load()

    def _load(self) -> None:
        """Carrega o arquivo de configuração e mescla com os padrões."""
        if not self.config_path.exists():
            logger.warning(
                "Arquivo de configuração '%s' não encontrado. "
                "Usando valores padrão. Crie o arquivo a partir de '%s'.",
                self.config_path,
                _CONFIG_EXAMPLE_FILE,
            )
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)

            self._data = _deep_merge(DEFAULT_CONFIG, user_config)
            logger.info(
                "Configurações carregadas de '%s'.", self.config_path
            )
        except json.JSONDecodeError as e:
            logger.error(
                "Erro ao ler '%s': JSON inválido (%s). Usando valores padrão.",
                self.config_path,
                e,
            )
        except OSError as e:
            logger.error(
                "Erro ao abrir '%s': %s. Usando valores padrão.",
                self.config_path,
                e,
            )

    def save(self) -> None:
        """Salva as configurações atuais no arquivo JSON.

        Raises:
            OSError: Se não for possível escrever o arquivo.
        """
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            logger.info("Configurações salvas em '%s'.", self.config_path)
        except OSError as e:
            logger.error("Erro ao salvar configurações: %s", e)
            raise

    def get(self, *keys: str, default: Any = None) -> Any:
        """Obtém um valor de configuração por caminho de chaves.

        Args:
            *keys: Sequência de chaves (ex: "holyrics", "host").
            default: Valor padrão se a chave não existir.

        Returns:
            Valor da configuração ou o default.

        Examples:
            >>> settings.get("holyrics", "host")
            'localhost'
            >>> settings.get("holyrics", "port")
            8091
        """
        current = self._data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def set(self, *keys_and_value: Any) -> None:
        """Define um valor de configuração por caminho de chaves.

        O último argumento é o valor; os anteriores são as chaves.

        Args:
            *keys_and_value: Chaves seguidas do valor
                             (ex: "holyrics", "port", 9000).

        Raises:
            ValueError: Se menos de 2 argumentos forem fornecidos.
        """
        if len(keys_and_value) < 2:
            raise ValueError("Forneça pelo menos uma chave e um valor.")

        keys = keys_and_value[:-1]
        value = keys_and_value[-1]

        current = self._data
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

    @property
    def holyrics_host(self) -> str:
        """Endereço do Holyrics API Server."""
        return self.get("holyrics", "host", default="localhost")

    @property
    def holyrics_port(self) -> int:
        """Porta do Holyrics API Server."""
        return self.get("holyrics", "port", default=8091)

    @property
    def holyrics_token(self) -> str:
        """Token de autenticação do Holyrics (sensível)."""
        return self.get("holyrics", "token", default="")

    @property
    def holyrics_timeout(self) -> float:
        """Timeout de conexão em segundos."""
        return self.get("holyrics", "timeout", default=10.0)

    @property
    def holyrics_base_url(self) -> str:
        """URL base do Holyrics API Server."""
        return f"http://{self.holyrics_host}:{self.holyrics_port}"

    def validate(self) -> list[str]:
        """Valida as configurações críticas.

        Returns:
            Lista de problemas encontrados (vazia se tudo estiver OK).
        """
        issues = []

        if not self.holyrics_host:
            issues.append("Endereço do Holyrics (holyrics.host) não configurado.")

        port = self.holyrics_port
        if not isinstance(port, int) or port < 1 or port > 65535:
            issues.append(
                f"Porta do Holyrics (holyrics.port) inválida: {port}. "
                "Deve ser um número entre 1 e 65535."
            )

        if not self.holyrics_token:
            issues.append(
                "Token do Holyrics (holyrics.token) não configurado. "
                "Gere um token em: Holyrics > Arquivo > Configurações > "
                "API Server > Gerenciar Permissões."
            )

        timeout = self.holyrics_timeout
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            issues.append(
                f"Timeout (holyrics.timeout) inválido: {timeout}. "
                "Deve ser um número positivo."
            )

        return issues

    def to_safe_dict(self) -> dict:
        """Retorna as configurações com o token mascarado.

        Seguro para logging e exibição.
        """
        safe = copy.deepcopy(self._data)
        if "holyrics" in safe and "token" in safe["holyrics"]:
            token = safe["holyrics"]["token"]
            if token:
                safe["holyrics"]["token"] = token[:3] + "***" if len(token) > 3 else "***"
            else:
                safe["holyrics"]["token"] = "(não configurado)"
        return safe

    def __repr__(self) -> str:
        return f"Settings(config_path='{self.config_path}')"
