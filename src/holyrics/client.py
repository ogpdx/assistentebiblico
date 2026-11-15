"""
Cliente HTTP de baixo nível para o Holyrics API Server.

Este módulo é responsável exclusivamente pela comunicação HTTP:
- Construção de URLs.
- Envio de requisições POST com JSON.
- Autenticação via token.
- Tratamento de erros de rede e protocolo.
- Proteção do token nos logs.

Referência: https://github.com/holyrics/API-Server

Protocolo:
    - Método: POST
    - Content-Type: application/json
    - URL: http://[HOST]:[PORT]/api/{action}?token=TOKEN
    - Body: JSON (pode ser {} para ações sem parâmetros)
    - Resposta: {"status": "ok", "data": ...} ou {"status": "error", ...}
"""

import requests

from src.core.logging_config import get_logger
from src.holyrics.exceptions import (
    HolyricsAPIError,
    HolyricsAuthError,
    HolyricsConnectionError,
    HolyricsPermissionError,
    HolyricsTimeoutError,
)

logger = get_logger(__name__)


class HolyricsClient:
    """Cliente HTTP para o Holyrics API Server.

    Encapsula toda a comunicação de rede com o Holyrics,
    oferecendo um método genérico `request()` que qualquer
    camada superior pode usar para enviar ações.

    Args:
        host: Endereço IP ou hostname do Holyrics.
        port: Porta do API Server.
        token: Token de autenticação.
        timeout: Timeout em segundos para cada requisição.

    Example:
        >>> client = HolyricsClient("localhost", 8091, "meu_token")
        >>> result = client.request("GetCPInfo")
        >>> print(result["status"])
        'ok'
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 8091,
        token: str = "",
        timeout: float = 10.0,
    ) -> None:
        self._host = host
        self._port = port
        self._token = token
        self._timeout = timeout

        self._base_url = f"http://{host}:{port}"
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

        logger.info(
            "Cliente Holyrics inicializado: %s:%d (timeout=%.1fs)",
            host, port, timeout,
        )

    @property
    def base_url(self) -> str:
        """URL base do API Server (sem token)."""
        return self._base_url

    @property
    def is_configured(self) -> bool:
        """Verifica se o cliente possui um token configurado."""
        return bool(self._token)

    def _build_url(self, action: str) -> str:
        """Constrói a URL completa para uma ação (sem token).

        Args:
            action: Nome da ação da API (ex: "ShowVerse").

        Returns:
            URL no formato http://host:port/api/{action}
        """
        return f"{self._base_url}/api/{action}"

    def _safe_url(self, action: str) -> str:
        """URL para logging (sem expor o token)."""
        return f"{self._base_url}/api/{action}?token=***"

    def request(self, action: str, payload: dict | None = None) -> dict:
        """Envia uma requisição POST ao Holyrics API Server.

        Args:
            action: Nome da ação (endpoint) da API.
                    Ex: "ShowVerse", "GetBibleVersionsV2".
            payload: Corpo JSON da requisição. Se None, envia {}.

        Returns:
            Dicionário com a resposta completa da API.

        Raises:
            HolyricsConnectionError: Servidor inacessível.
            HolyricsTimeoutError: Tempo de resposta excedido.
            HolyricsAuthError: Token inválido (HTTP 401).
            HolyricsPermissionError: Permissão insuficiente (HTTP 403).
            HolyricsAPIError: A API retornou um erro.
        """
        url = self._build_url(action)
        body = payload if payload is not None else {}

        logger.debug(
            "Enviando requisição: POST %s | body=%s",
            self._safe_url(action),
            body,
        )

        try:
            response = self._session.post(
                url,
                params={"token": self._token},
                json=body,
                timeout=self._timeout,
            )
        except requests.exceptions.ConnectionError as exc:
            msg = (
                f"Não foi possível conectar ao Holyrics em {self._base_url}. "
                "Verifique se o Holyrics está aberto e o API Server habilitado."
            )
            logger.error(msg)
            raise HolyricsConnectionError(msg) from exc
        except requests.exceptions.Timeout as exc:
            msg = (
                f"Timeout ao conectar ao Holyrics ({self._timeout}s). "
                "O servidor pode estar sobrecarregado."
            )
            logger.error(msg)
            raise HolyricsTimeoutError(msg) from exc
        except requests.exceptions.RequestException as exc:
            msg = f"Erro inesperado na requisição ao Holyrics: {exc}"
            logger.error(msg)
            raise HolyricsConnectionError(msg) from exc

        # Trata erros HTTP
        return self._handle_response(response, action)

    def _handle_response(self, response: requests.Response, action: str) -> dict:
        """Processa a resposta HTTP e trata erros.

        Args:
            response: Objeto Response do requests.
            action: Nome da ação (para mensagens de erro).

        Returns:
            Dicionário com a resposta da API.

        Raises:
            HolyricsAuthError: HTTP 401.
            HolyricsPermissionError: HTTP 403.
            HolyricsAPIError: Erro da API ou HTTP inesperado.
        """
        # Erros HTTP
        if response.status_code == 401:
            msg = (
                "Token de autenticação inválido ou ausente. "
                "Verifique o token em config.json e nas permissões do Holyrics."
            )
            logger.error(msg)
            raise HolyricsAuthError(msg)

        if response.status_code == 403:
            msg = (
                f"Permissão insuficiente para a ação '{action}'. "
                "Configure as permissões do token no Holyrics: "
                "Arquivo > Configurações > API Server > Gerenciar Permissões."
            )
            logger.error(msg)
            raise HolyricsPermissionError(msg)

        if response.status_code >= 400:
            msg = f"Erro HTTP {response.status_code} ao executar '{action}'."
            logger.error("%s | Resposta: %s", msg, response.text[:500])
            raise HolyricsAPIError(
                msg,
                details={"status_code": response.status_code, "body": response.text[:500]},
            )

        # Parse do JSON
        try:
            result = response.json()
        except ValueError as exc:
            msg = f"Resposta do Holyrics não é JSON válido para '{action}'."
            logger.error("%s | Resposta bruta: %s", msg, response.text[:500])
            raise HolyricsAPIError(msg) from exc

        # Verifica status da API
        status = result.get("status", "")
        if status == "error":
            error_msg = result.get("error", result.get("message", "Erro desconhecido"))
            msg = f"Erro da API Holyrics em '{action}': {error_msg}"
            logger.error(msg)
            raise HolyricsAPIError(msg, details=result)

        logger.debug("Resposta de '%s': status=%s", action, status)
        return result

    def test_connection(self) -> bool:
        """Testa se a conexão com o Holyrics está funcionando.

        Envia uma requisição simples (GetCPInfo) para verificar
        se o servidor está acessível e o token é válido.

        Returns:
            True se a conexão foi bem-sucedida.
        """
        try:
            result = self.request("GetCPInfo")
            return result.get("status") == "ok"
        except HolyricsError:
            return False

    def close(self) -> None:
        """Fecha a sessão HTTP."""
        self._session.close()
        logger.debug("Sessão HTTP do Holyrics encerrada.")

    def __enter__(self) -> "HolyricsClient":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def __repr__(self) -> str:
        return (
            f"HolyricsClient(host='{self._host}', port={self._port}, "
            f"configured={self.is_configured})"
        )
