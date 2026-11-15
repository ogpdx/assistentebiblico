"""
Testes automatizados da ETAPA 4 — Integração do Reconhecimento de Voz com o Holyrics.
Utiliza mocks completos da API do Holyrics para validação determinística e independente.
"""

from unittest.mock import MagicMock
import pytest

from src.core.controller import VoiceHolyricsController, ExecutionResult
from src.holyrics.api import HolyricsAPI
from src.holyrics.client import HolyricsClient
from src.holyrics.exceptions import HolyricsConnectionError, HolyricsAuthError
from src.interpreter.models import CommandType, BibleReferenceCommand, NavigationCommand, UnknownCommand


@pytest.fixture
def mock_api():
    """Cria uma instância mockada de HolyricsAPI."""
    client = MagicMock(spec=HolyricsClient)
    api = HolyricsAPI(client)
    api.show_verse = MagicMock(return_value={"status": "ok"})
    api.action_next = MagicMock(return_value={"status": "ok"})
    api.action_previous = MagicMock(return_value={"status": "ok"})
    api.close_current_presentation = MagicMock(return_value={"status": "ok"})
    api.get_current_presentation = MagicMock(return_value={
        "id": "43003016",
        "type": "verse",
        "name": "Jo 3:16",
        "slide_number": 26140,
        "total_slides": 31106,
    })
    return api


@pytest.fixture
def controller(mock_api):
    """Cria o controlador usando a API mockada."""
    return VoiceHolyricsController(api=mock_api, transcriber=None, duplicate_threshold_seconds=1.5)


class TestBibleVerseProjections:
    """Testes obrigatórios de projeção bíblica."""

    def test_projetar_joao_3_16(self, controller, mock_api):
        res = controller.process_text("João, capítulo 3, versículo 16")
        assert res.success is True
        assert res.action_executed == "ShowVerse"
        assert isinstance(res.command, BibleReferenceCommand)
        assert res.command.holyrics_reference == "Jo 3:16"
        mock_api.show_verse.assert_called_once_with(reference="Jo 3:16")

    def test_projetar_salmos_23_1(self, controller, mock_api):
        res = controller.process_text("Salmos vinte e três versículo um")
        assert res.success is True
        assert res.action_executed == "ShowVerse"
        assert res.command.holyrics_reference == "Sl 23:1"
        mock_api.show_verse.assert_called_once_with(reference="Sl 23:1")

    def test_projetar_apocalipse_1_1(self, controller, mock_api):
        res = controller.process_text("Apocalipse um um")
        assert res.success is True
        assert res.action_executed == "ShowVerse"
        assert res.command.holyrics_reference == "Ap 1:1"
        mock_api.show_verse.assert_called_once_with(reference="Ap 1:1")


class TestSafeNavigation:
    """Testes de navegação com consulta ao estado real do Holyrics."""

    def test_avancar_um_versiculo_com_apresentacao_biblica_ativa(self, controller, mock_api):
        # Holyrics está com type == "verse"
        mock_api.get_current_presentation.return_value = {
            "type": "verse",
            "name": "Jo 3:16",
            "slide_number": 26140,
        }
        res = controller.process_text("Próximo versículo")
        assert res.success is True
        assert res.action_executed == "ActionNext"
        mock_api.action_next.assert_called_once()

    def test_retornar_um_versiculo_com_apresentacao_biblica_ativa(self, controller, mock_api):
        # Holyrics está com type == "verse"
        mock_api.get_current_presentation.return_value = {
            "type": "verse",
            "name": "Jo 3:17",
            "slide_number": 26141,
        }
        res = controller.process_text("Versículo anterior")
        assert res.success is True
        assert res.action_executed == "ActionPrevious"
        mock_api.action_previous.assert_called_once()

    def test_impedir_navegacao_quando_apresentacao_for_musica(self, controller, mock_api):
        # Holyrics está exibindo uma música (type == "song")
        mock_api.get_current_presentation.return_value = {
            "type": "song",
            "name": "Porque Ele Vive",
            "slide_number": 1,
        }
        res = controller.process_text("Próximo versículo")
        assert res.success is False
        assert res.action_executed == "None"
        assert "não é bíblica" in res.message
        mock_api.action_next.assert_not_called()

    def test_impedir_navegacao_quando_nao_houver_apresentacao_ativa(self, controller, mock_api):
        # Holyrics sem nada na tela (None)
        mock_api.get_current_presentation.return_value = None
        res = controller.process_text("Versículo anterior")
        assert res.success is False
        assert res.action_executed == "None"
        assert "nenhuma apresentação ativa" in res.message
        mock_api.action_previous.assert_not_called()


class TestSecurityAndErrorHandling:
    """Testes de segurança: referências inválidas, duplicação e falhas de conexão."""

    def test_impedir_execucao_referencias_invalidas(self, controller, mock_api):
        # João 1316 não existe
        res = controller.process_text("João 1316")
        assert res.success is False
        assert res.action_executed == "None"
        assert isinstance(res.command, UnknownCommand)
        mock_api.show_verse.assert_not_called()

        # Salmos 151 não existe
        res2 = controller.process_text("Salmos 151")
        assert res2.success is False
        assert res2.action_executed == "None"
        mock_api.show_verse.assert_not_called()

    def test_impedir_comandos_duplicados_imediatos(self, controller, mock_api):
        # Envia João 3:16 uma vez
        res1 = controller.process_text("João 3 16")
        assert res1.success is True
        assert mock_api.show_verse.call_count == 1

        # Envia a mesma referência imediatamente em seguida (< 1.5s)
        res2 = controller.process_text("João 3 16")
        assert res2.success is False
        assert "duplicação rápida" in res2.message
        # A API NÃO deve ter sido chamada uma segunda vez
        assert mock_api.show_verse.call_count == 1

    def test_tratar_holyrics_desconectado(self, controller, mock_api):
        # Simula Holyrics desligado / ConnectionError
        mock_api.show_verse.side_effect = HolyricsConnectionError("Conexão recusada em localhost:8091")

        res = controller.process_text("João 3:16")
        assert res.success is False
        assert res.action_executed == "Error"
        assert "offline ou inacessível" in res.message.lower() or "conectar" in res.message.lower()
        # Garante que não levantou exceção descontrolada
        assert isinstance(res, ExecutionResult)
