"""
Exceções personalizadas para integração com o Holyrics.

Hierarquia:
    HolyricsError
    ├── HolyricsConnectionError   → Servidor inacessível
    ├── HolyricsTimeoutError      → Tempo de resposta excedido
    ├── HolyricsAuthError         → Token inválido (HTTP 401)
    ├── HolyricsPermissionError   → Permissão insuficiente (HTTP 403)
    └── HolyricsAPIError          → Erro retornado pela API (status: "error")
"""


class HolyricsError(Exception):
    """Erro base para todas as exceções do Holyrics."""

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.details = details or {}


class HolyricsConnectionError(HolyricsError):
    """O Holyrics API Server não está acessível.

    Causas prováveis:
    - Holyrics não está aberto.
    - API Server não está habilitado.
    - Endereço ou porta incorretos.
    - Firewall bloqueando a conexão.
    """

    pass


class HolyricsTimeoutError(HolyricsError):
    """A requisição ao Holyrics excedeu o tempo limite.

    Causas prováveis:
    - Holyrics travado ou sobrecarregado.
    - Timeout configurado muito baixo.
    """

    pass


class HolyricsAuthError(HolyricsError):
    """Token de autenticação inválido ou ausente (HTTP 401).

    Causas prováveis:
    - Token incorreto no config.json.
    - Token foi revogado no Holyrics.
    """

    pass


class HolyricsPermissionError(HolyricsError):
    """O token não possui permissão para a ação solicitada (HTTP 403).

    Causas prováveis:
    - Token não tem permissão para o endpoint usado.
    - Configurar permissões em:
      Holyrics > Arquivo > Configurações > API Server > Gerenciar Permissões.
    """

    pass


class HolyricsAPIError(HolyricsError):
    """A API do Holyrics retornou um erro (status: "error").

    Causas prováveis:
    - Parâmetros inválidos.
    - Referência bíblica não encontrada.
    - Estado interno do Holyrics incompatível com a operação.
    """

    pass
