"""
Testes da API de alto nível do Holyrics (HolyricsAPI).

Usa mocks no HolyricsClient.request() para simular
respostas da API sem necessidade do Holyrics real.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.holyrics.api import HolyricsAPI
from src.holyrics.client import HolyricsClient
from src.holyrics.models import BibleVersion, HolyricsStatus
from src.holyrics.exceptions import HolyricsConnectionError, HolyricsAPIError


@pytest.fixture
def mock_client():
    """HolyricsClient com request() mockado."""
    client = HolyricsClient(token="test_token")
    client.request = MagicMock()
    return client


@pytest.fixture
def api(mock_client):
    """HolyricsAPI com cliente mockado."""
    return HolyricsAPI(mock_client)


class TestGetStatus:
    """Testes de verificação de status."""

    def test_status_conectado(self, api, mock_client):
        mock_client.request.return_value = {
            "status": "ok",
            "data": {"version": "2.25.0"},
        }

        status = api.get_status()

        assert status.connected is True
        assert status.version == "2.25.0"
        assert "Conectado" in status.message

    def test_status_desconectado(self, api, mock_client):
        mock_client.request.side_effect = HolyricsConnectionError("Sem conexão")

        status = api.get_status()

        assert status.connected is False
        assert "Falha" in status.message or "conexão" in status.message.lower()


class TestGetBibleVersions:
    """Testes de listagem de traduções bíblicas."""

    def test_lista_versoes(self, api, mock_client):
        mock_client.request.return_value = {
            "status": "ok",
            "data": [
                {"key": "pt_arc", "title": "Almeida Revista e Corrigida"},
                {"key": "pt_nvi", "title": "Nova Versão Internacional"},
                {"key": "pt_acf", "title": "Almeida Corrigida Fiel"},
            ],
        }

        versions = api.get_bible_versions()

        assert len(versions) == 3
        assert isinstance(versions[0], BibleVersion)
        assert versions[0].key == "pt_arc"
        assert versions[1].title == "Nova Versão Internacional"
        mock_client.request.assert_called_once_with("GetBibleVersionsV2")

    def test_sem_versoes(self, api, mock_client):
        mock_client.request.return_value = {
            "status": "ok",
            "data": [],
        }

        versions = api.get_bible_versions()
        assert versions == []

    def test_dados_inesperados(self, api, mock_client):
        mock_client.request.return_value = {
            "status": "ok",
            "data": "formato_inesperado",
        }

        versions = api.get_bible_versions()
        assert versions == []


class TestShowVerse:
    """Testes de projeção de versículos."""

    def test_show_verse_por_referencia(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok"}

        result = api.show_verse(reference="João 3:16")

        assert result["status"] == "ok"
        mock_client.request.assert_called_once_with(
            "ShowVerse",
            {"references": "João 3:16"},
        )

    def test_show_verse_por_id(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok"}

        api.show_verse(verse_id="43003016")

        mock_client.request.assert_called_once_with(
            "ShowVerse",
            {"id": "43003016"},
        )

    def test_show_verse_por_ids(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok"}

        ids = ["43003016", "43003017", "43003018"]
        api.show_verse(verse_ids=ids)

        mock_client.request.assert_called_once_with(
            "ShowVerse",
            {"ids": ids},
        )

    def test_show_verse_com_versao(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok"}

        api.show_verse(reference="Gn 1:1-3", version="pt_arc")

        mock_client.request.assert_called_once_with(
            "ShowVerse",
            {"references": "Gn 1:1-3", "version": "pt_arc"},
        )

    def test_show_verse_sem_parametros_erro(self, api):
        with pytest.raises(ValueError, match="Forneça pelo menos"):
            api.show_verse()

    def test_show_verse_mais_de_100_ids_erro(self, api):
        ids = [f"010010{i:02d}" for i in range(101)]
        with pytest.raises(ValueError, match="100"):
            api.show_verse(verse_ids=ids)

    def test_show_verse_referencia_prioritaria(self, api, mock_client):
        """Quando reference é fornecido, é usado preferencialmente."""
        mock_client.request.return_value = {"status": "ok"}

        api.show_verse(reference="Sl 23", verse_id="19023001")

        call_payload = mock_client.request.call_args[0][1]
        assert "references" in call_payload
        assert "id" not in call_payload


class TestSelectVerse:
    """Testes de seleção de versículo."""

    def test_select_por_id(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok"}

        api.select_verse(verse_id="43003016")

        mock_client.request.assert_called_once_with(
            "SelectVerse",
            {"id": "43003016"},
        )

    def test_select_por_referencia(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok"}

        api.select_verse(reference="João 3:16")

        mock_client.request.assert_called_once_with(
            "SelectVerse",
            {"reference": "João 3:16"},
        )

    def test_select_sem_parametros_erro(self, api):
        with pytest.raises(ValueError):
            api.select_verse()


class TestClosePresentation:
    """Testes de fechamento de apresentação."""

    def test_close_current(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok"}

        result = api.close_current_presentation()

        assert result["status"] == "ok"
        mock_client.request.assert_called_once_with("CloseCurrentPresentation")

    def test_close_quick(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok"}

        result = api.close_quick_presentation()

        assert result["status"] == "ok"
        mock_client.request.assert_called_once_with("CloseCurrentQuickPresentation")


class TestShowQuickPresentation:
    """Testes de apresentação rápida."""

    def test_show_text(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok"}

        api.show_quick_presentation("Texto de teste")

        mock_client.request.assert_called_once_with(
            "ShowQuickPresentation",
            {"text": "Texto de teste"},
        )

    def test_show_text_com_tema(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok"}

        api.show_quick_presentation("Texto", theme="MeuTema")

        mock_client.request.assert_called_once_with(
            "ShowQuickPresentation",
            {"text": "Texto", "theme": {"name": "MeuTema"}},
        )


class TestNavigationActions:
    """Testes de navegação."""

    def test_action_next(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok"}
        api.action_next()
        mock_client.request.assert_called_once_with("ActionNext")

    def test_action_previous(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok"}
        api.action_previous()
        mock_client.request.assert_called_once_with("ActionPrevious")

    def test_action_go_to_index(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok"}
        api.action_go_to_index(5)
        mock_client.request.assert_called_once_with(
            "ActionGoToIndex",
            {"index": 5},
        )


class TestIdentifyVerseReferences:
    """Testes de identificação de referências."""

    def test_identifica_referencia(self, api, mock_client):
        mock_client.request.return_value = {
            "status": "ok",
            "data": [{"reference": "João 3:16"}],
        }

        refs = api.identify_verse_references("João 3:16")

        assert len(refs) == 1
        mock_client.request.assert_called_once_with(
            "IdentifyVerseReferences",
            {"value": "João 3:16"},
        )

    def test_identifica_com_idioma(self, api, mock_client):
        mock_client.request.return_value = {"status": "ok", "data": []}

        api.identify_verse_references("Genesis 1:1", language_id="en")

        mock_client.request.assert_called_once_with(
            "IdentifyVerseReferences",
            {"value": "Genesis 1:1", "language_id": "en"},
        )


class TestBibleVersionModel:
    """Testes do modelo BibleVersion."""

    def test_from_api(self):
        data = {"key": "pt_arc", "title": "Almeida Revista e Corrigida"}
        version = BibleVersion.from_api(data)

        assert version.key == "pt_arc"
        assert version.title == "Almeida Revista e Corrigida"

    def test_from_api_dados_parciais(self):
        version = BibleVersion.from_api({})
        assert version.key == ""
        assert version.title == ""


class TestHolyricsStatusModel:
    """Testes do modelo HolyricsStatus."""

    def test_status_conectado(self):
        status = HolyricsStatus(connected=True, version="2.25.0", message="OK")
        assert status.connected
        assert status.version == "2.25.0"

    def test_status_desconectado(self):
        status = HolyricsStatus(connected=False, message="Falha")
        assert not status.connected
        assert status.raw_data == {}
