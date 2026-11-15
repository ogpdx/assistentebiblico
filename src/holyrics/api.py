"""
API de alto nível para operações no Holyrics.

Este módulo oferece métodos tipados e documentados para cada
operação suportada pela API do Holyrics, abstraindo os detalhes
de construção do payload JSON.

Todos os métodos delegam ao HolyricsClient.request() para
comunicação de rede.

Referência dos endpoints:
    https://github.com/holyrics/API-Server
"""

from src.core.constants import HolyricsActions
from src.core.logging_config import get_logger
from src.holyrics.client import HolyricsClient
from src.holyrics.models import BibleVersion, HolyricsStatus

logger = get_logger(__name__)


class HolyricsAPI:
    """Interface de alto nível para a API do Holyrics.

    Encapsula as operações bíblicas e de apresentação em métodos
    Python simples e tipados.

    Args:
        client: Instância do HolyricsClient configurada.

    Example:
        >>> client = HolyricsClient("localhost", 8091, "token")
        >>> api = HolyricsAPI(client)
        >>> versions = api.get_bible_versions()
        >>> api.show_verse(reference="João 3:16")
    """

    def __init__(self, client: HolyricsClient) -> None:
        self._client = client

    @property
    def client(self) -> HolyricsClient:
        """Acesso ao cliente HTTP subjacente."""
        return self._client

    # ──────────────────────────────────────────────
    # Sistema
    # ──────────────────────────────────────────────

    def get_status(self) -> HolyricsStatus:
        """Obtém informações do sistema e verifica a conexão.

        Envia GetCPInfo para verificar se o Holyrics está acessível.

        Returns:
            HolyricsStatus com informações do sistema.
        """
        try:
            result = self._client.request(HolyricsActions.GET_CP_INFO)
            data = result.get("data", {})
            return HolyricsStatus(
                connected=True,
                version=str(data.get("version", "")),
                message="Conectado ao Holyrics.",
                raw_data=data,
            )
        except Exception as exc:
            return HolyricsStatus(
                connected=False,
                message=f"Falha na conexão: {exc}",
            )

    # ──────────────────────────────────────────────
    # Bíblia — Consultas
    # ──────────────────────────────────────────────

    def get_bible_versions(self) -> list[BibleVersion]:
        """Lista as traduções bíblicas instaladas no Holyrics.

        Usa o endpoint GetBibleVersionsV2 (recomendado sobre GetBibleVersions).

        Returns:
            Lista de BibleVersion com key e title de cada tradução.

        Raises:
            HolyricsError: Se houver erro na comunicação.
        """
        result = self._client.request(HolyricsActions.GET_BIBLE_VERSIONS_V2)
        data = result.get("data", [])

        if not isinstance(data, list):
            logger.warning(
                "GetBibleVersionsV2 retornou dados inesperados: %s",
                type(data).__name__,
            )
            return []

        versions = [BibleVersion.from_api(item) for item in data]
        logger.info("Traduções bíblicas encontradas: %d", len(versions))
        for v in versions:
            logger.debug("  - %s: %s", v.key, v.title)
        return versions

    def get_bible_books(self, language_id: str = "pt") -> list[dict]:
        """Lista os livros bíblicos por idioma.

        Args:
            language_id: Código do idioma (ex: "pt", "en").

        Returns:
            Lista de dicionários com informações dos livros.

        Raises:
            HolyricsError: Se houver erro na comunicação.
        """
        result = self._client.request(
            HolyricsActions.GET_BIBLE_BOOKS,
            {"language_id": language_id},
        )
        data = result.get("data", [])
        logger.info("Livros bíblicos (idioma=%s): %d encontrados", language_id, len(data))
        return data

    def get_bible_settings(self) -> dict:
        """Obtém as configurações bíblicas atuais do Holyrics.

        Returns:
            Dicionário com configurações de exibição bíblica.
        """
        result = self._client.request(HolyricsActions.GET_BIBLE_SETTINGS)
        return result.get("data", {})

    def identify_verse_references(
        self, text: str, language_id: str | None = None
    ) -> list[dict]:
        """Identifica referências bíblicas em um texto livre.

        Útil para validar se o Holyrics reconhece uma referência
        antes de enviá-la para projeção.

        Args:
            text: Texto a ser analisado (ex: "João 3:16").
            language_id: Idioma dos nomes de livros (padrão do Holyrics se None).

        Returns:
            Lista de referências identificadas.
        """
        payload: dict = {"value": text}
        if language_id is not None:
            payload["language_id"] = language_id

        result = self._client.request(
            HolyricsActions.IDENTIFY_VERSE_REFERENCES, payload
        )
        data = result.get("data", [])
        logger.info(
            "Referências identificadas em '%s': %d",
            text[:50], len(data) if isinstance(data, list) else 0,
        )
        return data

    # ──────────────────────────────────────────────
    # Bíblia — Projeção
    # ──────────────────────────────────────────────

    def show_verse(
        self,
        *,
        reference: str | None = None,
        verse_id: str | None = None,
        verse_ids: list[str] | None = None,
        version: str | None = None,
    ) -> dict:
        """Projeta versículo(s) na tela do Holyrics.

        Este é o método principal de integração. Aceita três formas
        de especificar os versículos (use apenas uma por chamada):

        1. reference: Referência textual (ex: "João 3:16", "Gn 1:1-3").
        2. verse_id: ID único no formato BBCCCVVV (ex: "43003016").
        3. verse_ids: Lista de IDs BBCCCVVV para múltiplos versículos.

        O Holyrics resolvea referência internamente, usando suas
        traduções instaladas e configurações de exibição.

        Args:
            reference: Referência textual (preferencial).
            verse_id: ID no formato BBCCCVVV.
            verse_ids: Lista de IDs BBCCCVVV (máximo 100).
            version: Versão/tradução (ex: "pt_arc"). Opcional.

        Returns:
            Resposta da API.

        Raises:
            ValueError: Se nenhum parâmetro de identificação for fornecido.
            HolyricsError: Se houver erro na comunicação.

        Example:
            >>> api.show_verse(reference="João 3:16")
            >>> api.show_verse(verse_id="43003016")
            >>> api.show_verse(verse_ids=["43003016", "43003017"])
            >>> api.show_verse(reference="Sl 23", version="pt_nvi")
        """
        if not any([reference, verse_id, verse_ids]):
            raise ValueError(
                "Forneça pelo menos um dos parâmetros: "
                "reference, verse_id ou verse_ids."
            )

        # Constrói o payload conforme documentação da API HTTP do Holyrics:
        # Na API HTTP os campos vão diretamente na raiz do payload.
        payload: dict = {}

        if reference is not None:
            payload["references"] = reference
        elif verse_id is not None:
            payload["id"] = verse_id
        elif verse_ids is not None:
            if len(verse_ids) > 100:
                raise ValueError(
                    f"Máximo de 100 versículos por requisição "
                    f"(recebidos: {len(verse_ids)})."
                )
            payload["ids"] = verse_ids

        if version is not None:
            payload["version"] = version

        display = reference or verse_id or f"{len(verse_ids or [])} versículos"
        logger.info("Projetando versículo: %s", display)

        result = self._client.request(HolyricsActions.SHOW_VERSE, payload)
        logger.info("Versículo projetado com sucesso: %s", display)
        return result

    def select_verse(
        self,
        *,
        verse_id: str | None = None,
        reference: str | None = None,
    ) -> dict:
        """Seleciona um versículo na janela bíblica do Holyrics.

        Diferente de show_verse, não projeta na tela — apenas
        seleciona o versículo no painel bíblico do Holyrics.

        Args:
            verse_id: ID no formato BBCCCVVV.
            reference: Referência textual.

        Returns:
            Resposta da API.
        """
        if not any([verse_id, reference]):
            raise ValueError("Forneça verse_id ou reference.")

        # SelectVerse usa parâmetros no nível raiz (sem wrapper "input")
        payload: dict = {}
        if verse_id is not None:
            payload["id"] = verse_id
        elif reference is not None:
            payload["reference"] = reference

        return self._client.request(HolyricsActions.SELECT_VERSE, payload)

    # ──────────────────────────────────────────────
    # Apresentação — Controle
    # ──────────────────────────────────────────────

    def close_current_presentation(self) -> dict:
        """Fecha a apresentação atual na tela do Holyrics.

        Returns:
            Resposta da API.
        """
        logger.info("Fechando apresentação atual.")
        return self._client.request(HolyricsActions.CLOSE_CURRENT_PRESENTATION)

    def close_quick_presentation(self) -> dict:
        """Fecha a apresentação rápida atual.

        Returns:
            Resposta da API.
        """
        logger.info("Fechando apresentação rápida.")
        return self._client.request(
            HolyricsActions.CLOSE_CURRENT_QUICK_PRESENTATION
        )

    def show_quick_presentation(
        self,
        text: str,
        *,
        theme: str | None = None,
    ) -> dict:
        """Exibe uma apresentação rápida com texto personalizado.

        Útil como fallback se ShowVerse não funcionar para
        determinado caso de uso.

        Args:
            text: Texto a ser exibido na tela.
            theme: Nome do tema a aplicar (opcional).

        Returns:
            Resposta da API.
        """
        payload: dict = {"text": text}
        if theme is not None:
            payload["theme"] = {"name": theme}

        logger.info("Exibindo apresentação rápida: '%s'", text[:80])
        return self._client.request(
            HolyricsActions.SHOW_QUICK_PRESENTATION, payload
        )

    def action_next(self) -> dict:
        """Avança para o próximo slide/versículo.

        Returns:
            Resposta da API.
        """
        return self._client.request(HolyricsActions.ACTION_NEXT)

    def action_previous(self) -> dict:
        """Volta para o slide/versículo anterior.

        Returns:
            Resposta da API.
        """
        return self._client.request(HolyricsActions.ACTION_PREVIOUS)

    def action_go_to_index(self, index: int) -> dict:
        """Vai para um slide/versículo específico por índice.

        Args:
            index: Índice do slide (baseado em zero).

        Returns:
            Resposta da API.
        """
        return self._client.request(
            HolyricsActions.ACTION_GO_TO_INDEX,
            {"index": index},
        )

    # ──────────────────────────────────────────────
    # Utilitários
    # ──────────────────────────────────────────────

    def get_current_presentation(self) -> dict | None:
        """Obtém detalhes da apresentação ativa na tela do Holyrics.

        Returns:
            Dicionário com 'type', 'id', 'name', 'slide_number', 'total_slides', etc.,
            ou None se não houver apresentação em andamento.
        """
        result = self._client.request(HolyricsActions.GET_CURRENT_PRESENTATION)
        return result.get("data")

    def parse_verse_id(self, verse_id: str) -> dict:
        """Converte um ID BBCCCVVV em referência legível.

        Args:
            verse_id: ID no formato BBCCCVVV (ex: "43003016").

        Returns:
            Dicionário com a referência textual.
        """
        return self._client.request(
            HolyricsActions.PARSE_VERSE_ID,
            {"id": verse_id},
        )

    def __repr__(self) -> str:
        return f"HolyricsAPI(client={self._client!r})"
