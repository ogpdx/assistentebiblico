"""
Testes do gerenciador de configurações (Settings).
"""

import json
import pytest

from src.config.settings import Settings
from src.config.defaults import DEFAULT_CONFIG


class TestSettingsLoad:
    """Testes de carregamento de configurações."""

    def test_carrega_valores_padrao_sem_arquivo(self, tmp_path):
        """Sem config.json, usa valores padrão."""
        config_path = tmp_path / "inexistente.json"
        settings = Settings(str(config_path))

        assert settings.holyrics_host == "localhost"
        assert settings.holyrics_port == 8091
        assert settings.holyrics_token == ""
        assert settings.holyrics_timeout == 10.0

    def test_carrega_arquivo_valido(self, tmp_path):
        """Carrega valores do config.json."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "holyrics": {
                "host": "192.168.1.100",
                "port": 9000,
                "token": "abc123",
            }
        }), encoding="utf-8")

        settings = Settings(str(config_file))

        assert settings.holyrics_host == "192.168.1.100"
        assert settings.holyrics_port == 9000
        assert settings.holyrics_token == "abc123"
        # Valores não definidos pelo usuário vêm do padrão
        assert settings.holyrics_timeout == 10.0

    def test_carrega_json_invalido_usa_padroes(self, tmp_path):
        """JSON corrompido não quebra — usa padrões."""
        config_file = tmp_path / "config.json"
        config_file.write_text("{invalid json", encoding="utf-8")

        settings = Settings(str(config_file))

        assert settings.holyrics_host == "localhost"
        assert settings.holyrics_port == 8091

    def test_merge_profundo(self, tmp_path):
        """Valores parciais se mesclam com padrões."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "holyrics": {
                "token": "meu_token",
            }
        }), encoding="utf-8")

        settings = Settings(str(config_file))

        # Token veio do arquivo
        assert settings.holyrics_token == "meu_token"
        # O resto veio dos padrões
        assert settings.holyrics_host == "localhost"
        assert settings.holyrics_port == 8091


class TestSettingsGetSet:
    """Testes de acesso e modificação de valores."""

    def test_get_chave_existente(self, mock_settings):
        assert mock_settings.get("holyrics", "host") == "localhost"

    def test_get_chave_inexistente_retorna_default(self, mock_settings):
        assert mock_settings.get("foo", "bar", default="fallback") == "fallback"

    def test_set_valor(self, mock_settings):
        mock_settings.set("holyrics", "port", 9999)
        assert mock_settings.get("holyrics", "port") == 9999

    def test_set_sem_argumentos_suficientes(self, mock_settings):
        with pytest.raises(ValueError):
            mock_settings.set("apenas_chave")


class TestSettingsSave:
    """Testes de persistência."""

    def test_salva_e_recarrega(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "holyrics": {"token": "original"}
        }), encoding="utf-8")

        settings = Settings(str(config_file))
        settings.set("holyrics", "token", "modificado")
        settings.save()

        # Recarrega e verifica
        settings2 = Settings(str(config_file))
        assert settings2.holyrics_token == "modificado"


class TestSettingsValidation:
    """Testes de validação de configurações."""

    def test_valida_configuracao_completa(self, mock_settings):
        issues = mock_settings.validate()
        assert issues == []

    def test_valida_token_ausente(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "holyrics": {"host": "localhost", "port": 8091, "token": ""}
        }), encoding="utf-8")

        settings = Settings(str(config_file))
        issues = settings.validate()

        assert any("token" in i.lower() or "Token" in i for i in issues)

    def test_valida_porta_invalida(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "holyrics": {"port": -1, "token": "abc"}
        }), encoding="utf-8")

        settings = Settings(str(config_file))
        issues = settings.validate()

        assert any("porta" in i.lower() or "Porta" in i for i in issues)


class TestSettingsSecurity:
    """Testes de proteção do token."""

    def test_to_safe_dict_mascara_token(self, mock_settings):
        safe = mock_settings.to_safe_dict()
        token = safe["holyrics"]["token"]
        assert "test_token_123" not in token
        assert "***" in token

    def test_to_safe_dict_token_vazio(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text('{"holyrics": {"token": ""}}', encoding="utf-8")

        settings = Settings(str(config_file))
        safe = settings.to_safe_dict()

        assert safe["holyrics"]["token"] == "(não configurado)"


class TestSettingsProperties:
    """Testes das propriedades de conveniência."""

    def test_holyrics_base_url(self, mock_settings):
        url = mock_settings.holyrics_base_url
        assert url == "http://localhost:8091"

    def test_holyrics_base_url_custom(self, tmp_path):
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({
            "holyrics": {"host": "192.168.1.50", "port": 3500}
        }), encoding="utf-8")

        settings = Settings(str(config_file))
        assert settings.holyrics_base_url == "http://192.168.1.50:3500"
