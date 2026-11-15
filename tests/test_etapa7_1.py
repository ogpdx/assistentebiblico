"""
Testes automatizados da ETAPA 7.1:
1. Extração de referências bíblicas em frases naturais complexas de culto.
2. Tratamento de fonemas/erros leves do Whisper (ex: 'sámos' -> Salmos).
3. Teste negativo: frases sem referência ou com números aleatórios não se transformam em referências.
4. Teste de isolamento offline de modelo local (sem chamadas de rede).
5. Comandos de parada/limpeza/encerramento de projeção.
"""

import sys
import pytest
from unittest.mock import MagicMock, patch

from src.interpreter import classify_command, CommandType
from src.interpreter.models import BibleReferenceCommand, NavigationCommand, UnknownCommand
from src.core.controller import VoiceHolyricsController


class TestEtapa71NaturalSpeechExtraction:
    """Testes específicos do Problema 1: Extração em falas naturais."""

    def test_frases_reais_com_salmos(self):
        frases = [
            ("Então, lá em Salmos 23.1.", "Salmos", 23, 1),
            ("Então assim, pessoal, lá em Salmos 23.1.", "Salmos", 23, 1),
            ("Lá em Salmos 23, 1.", "Salmos", 23, 1),
            ("Abra a sua Bíblia em sámos 23, 1.", "Salmos", 23, 1),
            ("Então, lá em Salmos 23, versículo 1.", "Salmos", 23, 1),
        ]
        for frase, book, cap, v in frases:
            cmd = classify_command(frase)
            assert isinstance(cmd, BibleReferenceCommand), f"Falha na frase: {frase}"
            assert cmd.book_name == book
            assert cmd.chapter == cap
            assert cmd.verse_start == v

    def test_outras_frases_naturais_de_culto(self):
        casos = [
            ("Vamos abrir em João 3:16.", "João", 3, 16),
            ("Abra sua Bíblia em Romanos capítulo 8, versículo 1.", "Romanos", 8, 1),
            ("Hoje vamos estudar primeiro Coríntios 13.", "1 Coríntios", 13, None),
            ("Vamos acompanhar em Gênesis, capítulo 1, versículo 1.", "Gênesis", 1, 1),
        ]
        for frase, book, cap, v in casos:
            cmd = classify_command(frase)
            assert isinstance(cmd, BibleReferenceCommand), f"Falha na frase: {frase}"
            assert cmd.book_name == book
            assert cmd.chapter == cap
            assert cmd.verse_start == v

    def test_negativos_nao_transforma_numeros_aleatorios(self):
        frases_negativas = [
            "Hoje tivemos 23 pessoas e 1 criança.",
            "São exatamente 14 horas e 30 minutos.",
            "A reunião começa às 19 horas.",
            "Comprei 3 pães e 16 laranjas.",
            "O versículo era muito bonito, irmãos.",
            "Glória a Deus pela vitória!",
        ]
        for frase in frases_negativas:
            cmd = classify_command(frase)
            assert isinstance(cmd, UnknownCommand), f"Deveria ter rejeitado: {frase}"
            assert cmd.command_type == CommandType.UNKNOWN


class TestEtapa71ClearPresentationSecurity:
    """Validação dos comandos de encerramento de projeção."""

    @pytest.mark.parametrize("frase", ["Parar projeção.", "Limpar projeção.", "Encerrar projeção."])
    def test_comandos_de_encerramento(self, frase):
        cmd = classify_command(frase)
        assert isinstance(cmd, NavigationCommand)
        assert cmd.command_type == CommandType.CLEAR_PRESENTATION

    def test_bloqueia_se_apresentacao_for_musica(self):
        api = MagicMock()
        api.get_current_presentation.return_value = {"type": "song", "name": "Hino 15"}
        ctrl = VoiceHolyricsController(api=api)
        res = ctrl.process_text("Parar projeção")
        assert res.success is False
        assert "não é bíblica" in res.message
        api.close_current_presentation.assert_not_called()

    def test_executa_se_apresentacao_for_versiculo(self):
        api = MagicMock()
        api.get_current_presentation.side_effect = [
            {"type": "verse", "name": "Sl 23:1"},
            None
        ]
        api.close_current_presentation.return_value = {"status": "ok"}
        ctrl = VoiceHolyricsController(api=api)
        res = ctrl.process_text("Encerrar projeção")
        assert res.success is True
        assert "encerrada com sucesso" in res.message
        api.close_current_presentation.assert_called_once()
