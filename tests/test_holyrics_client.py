"""
Testes do cliente HTTP do Holyrics (HolyricsClient).

Todos os testes usam mocks para simular respostas HTTP,
permitindo testes sem o Holyrics real.
"""

import pytest
from unittest.mock import patch, MagicMock
import requests

from src.holyrics.client import HolyricsClient
from src.holyrics.exceptions import (
    HolyricsConnectionError,
    HolyricsTimeoutError,
    HolyricsAuthError,
    HolyricsPermissionError,
    HolyricsAPIError,
)


class TestHolyricsClientInit:
    """Testes de inicialização do cliente."""

    def test_inicializa_com_valores_padrao(self):
        client = HolyricsClient()
        assert client.base_url == "http://localhost:8091"
        assert not client.is_configured

    def test_inicializa_com_parametros(self):
        client = HolyricsClient(
            host="192.168.1.100",
            port=3500,
            token="abc123",
            timeout=30.0,
        )
        assert client.base_url == "http://192.168.1.100:3500"
        assert client.is_configured

    def test_is_configured_com_token(self):
        client = HolyricsClient(token="abc")
        assert client.is_configured

    def test_is_configured_sem_token(self):
        client = HolyricsClient(token="")
        assert not client.is_configured


class TestHolyricsClientRequest:
    """Testes de envio de requisições."""

    def _mock_response(self, status_code=200, json_data=None):
        """Cria um Response mockado."""
        response = MagicMock(spec=requests.Response)
        response.status_code = status_code
        response.json.return_value = json_data or {"status": "ok"}
        response.text = str(json_data or {"status": "ok"})
        return response

    @patch.object(requests.Session, "post")
    def test_requisicao_bem_sucedida(self, mock_post):
        """Requisição com resposta OK."""
        mock_post.return_value = self._mock_response(
            json_data={"status": "ok", "data": {"version": "2.25.0"}}
        )

        client = HolyricsClient(token="test_token")
        result = client.request("GetCPInfo")

        assert result["status"] == "ok"
        assert result["data"]["version"] == "2.25.0"

        # Verifica que o POST foi chamado corretamente
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "GetCPInfo" in call_args.args[0] or "GetCPInfo" in str(call_args)

    @patch.object(requests.Session, "post")
    def test_requisicao_com_payload(self, mock_post):
        """Requisição com body JSON."""
        mock_post.return_value = self._mock_response(
            json_data={"status": "ok"}
        )

        client = HolyricsClient(token="test_token")
        payload = {"references": "João 3:16"}
        client.request("ShowVerse", payload)

        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["json"] == payload

    @patch.object(requests.Session, "post")
    def test_token_enviado_como_query_param(self, mock_post):
        """Token é enviado como parâmetro da URL."""
        mock_post.return_value = self._mock_response()

        client = HolyricsClient(token="meu_token_secreto")
        client.request("GetCPInfo")

        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["params"] == {"token": "meu_token_secreto"}

    @patch.object(requests.Session, "post")
    def test_payload_vazio_quando_none(self, mock_post):
        """Sem payload, envia {} (corpo vazio)."""
        mock_post.return_value = self._mock_response()

        client = HolyricsClient(token="test")
        client.request("GetCPInfo")

        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["json"] == {}

    @patch.object(requests.Session, "post")
    def test_timeout_configurado(self, mock_post):
        """Timeout é repassado ao requests."""
        mock_post.return_value = self._mock_response()

        client = HolyricsClient(token="test", timeout=25.0)
        client.request("GetCPInfo")

        call_kwargs = mock_post.call_args.kwargs
        assert call_kwargs["timeout"] == 25.0


class TestHolyricsClientErrors:
    """Testes de tratamento de erros."""

    @patch.object(requests.Session, "post")
    def test_erro_conexao(self, mock_post):
        """ConnectionError → HolyricsConnectionError."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Recusado")

        client = HolyricsClient(token="test")
        with pytest.raises(HolyricsConnectionError) as exc_info:
            client.request("GetCPInfo")

        assert "conectar" in str(exc_info.value).lower() or "Holyrics" in str(exc_info.value)

    @patch.object(requests.Session, "post")
    def test_erro_timeout(self, mock_post):
        """Timeout → HolyricsTimeoutError."""
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")

        client = HolyricsClient(token="test")
        with pytest.raises(HolyricsTimeoutError) as exc_info:
            client.request("GetCPInfo")

        assert "timeout" in str(exc_info.value).lower() or "Timeout" in str(exc_info.value)

    @patch.object(requests.Session, "post")
    def test_erro_401_auth(self, mock_post):
        """HTTP 401 → HolyricsAuthError."""
        response = MagicMock(spec=requests.Response)
        response.status_code = 401
        response.text = "Unauthorized"
        mock_post.return_value = response

        client = HolyricsClient(token="token_invalido")
        with pytest.raises(HolyricsAuthError):
            client.request("GetCPInfo")

    @patch.object(requests.Session, "post")
    def test_erro_403_permissao(self, mock_post):
        """HTTP 403 → HolyricsPermissionError."""
        response = MagicMock(spec=requests.Response)
        response.status_code = 403
        response.text = "Forbidden"
        mock_post.return_value = response

        client = HolyricsClient(token="test")
        with pytest.raises(HolyricsPermissionError) as exc_info:
            client.request("ShowVerse")

        assert "permissão" in str(exc_info.value).lower() or "Permissão" in str(exc_info.value)

    @patch.object(requests.Session, "post")
    def test_erro_api_status_error(self, mock_post):
        """API retorna status: "error" → HolyricsAPIError."""
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        response.json.return_value = {
            "status": "error",
            "error": "Referência não encontrada",
        }
        response.text = '{"status": "error"}'
        mock_post.return_value = response

        client = HolyricsClient(token="test")
        with pytest.raises(HolyricsAPIError) as exc_info:
            client.request("ShowVerse", {"input": {"references": "Livro Inexistente 1:1"}})

        assert "Referência não encontrada" in str(exc_info.value)

    @patch.object(requests.Session, "post")
    def test_erro_http_500(self, mock_post):
        """HTTP 500+ → HolyricsAPIError."""
        response = MagicMock(spec=requests.Response)
        response.status_code = 500
        response.text = "Internal Server Error"
        mock_post.return_value = response

        client = HolyricsClient(token="test")
        with pytest.raises(HolyricsAPIError):
            client.request("GetCPInfo")

    @patch.object(requests.Session, "post")
    def test_resposta_nao_json(self, mock_post):
        """Resposta não-JSON → HolyricsAPIError."""
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        response.json.side_effect = ValueError("No JSON")
        response.text = "<html>Not JSON</html>"
        mock_post.return_value = response

        client = HolyricsClient(token="test")
        with pytest.raises(HolyricsAPIError) as exc_info:
            client.request("GetCPInfo")

        assert "JSON" in str(exc_info.value)

    @patch.object(requests.Session, "post")
    def test_erro_request_generico(self, mock_post):
        """RequestException genérica → HolyricsConnectionError."""
        mock_post.side_effect = requests.exceptions.RequestException("Erro genérico")

        client = HolyricsClient(token="test")
        with pytest.raises(HolyricsConnectionError):
            client.request("GetCPInfo")


class TestHolyricsClientTestConnection:
    """Testes do método test_connection."""

    @patch.object(requests.Session, "post")
    def test_conexao_ok(self, mock_post):
        response = MagicMock(spec=requests.Response)
        response.status_code = 200
        response.json.return_value = {"status": "ok", "data": {}}
        mock_post.return_value = response

        client = HolyricsClient(token="test")
        assert client.test_connection() is True

    @patch.object(requests.Session, "post")
    def test_conexao_falha(self, mock_post):
        mock_post.side_effect = requests.exceptions.ConnectionError()

        client = HolyricsClient(token="test")
        assert client.test_connection() is False


class TestHolyricsClientContextManager:
    """Testes do context manager."""

    def test_context_manager_fecha_sessao(self):
        with HolyricsClient(token="test") as client:
            assert client.is_configured
        # Após sair do with, a sessão é fechada (sem exceção)

    def test_repr(self):
        client = HolyricsClient(host="192.168.1.1", port=3500, token="abc")
        repr_str = repr(client)
        assert "192.168.1.1" in repr_str
        assert "3500" in repr_str
        assert "configured=True" in repr_str
        # Token NÃO aparece no repr
        assert "abc" not in repr_str
