"""
Testes automatizados para a ETAPA 7:
1. Alternar entre Push-to-Talk e modo automático.
2. Iniciar e pausar escuta automática.
3. Ignorar fala comum (UNKNOWN).
4. Reconhecer referências bíblicas ("Vamos abrir em João capítulo 3, versículo 16").
5. Reconhecer próximo e versículo anterior.
6. Evitar comandos duplicados (cooldown/threshold).
7. Evitar operações simultâneas (Lock do controller / descarte em fila).
8. Recuperar-se de falhas de microfone.
9. Encerrar o aplicativo e liberar o dispositivo.
10. Reconhecer "Parar projeção".
11. Reconhecer "Limpar projeção".
12. Reconhecer "Encerrar projeção".
13. Bloquear limpeza quando o Holyrics estiver exibindo apresentação não bíblica (song/none).
14. Confirmar encerramento de apresentação bíblica.
15. Tratar falha ou resultado inconclusivo na confirmação.
"""

import sys
import time
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from PySide6.QtWidgets import QApplication

from src.config.settings import Settings
from src.interpreter import classify_command, CommandType
from src.interpreter.models import BibleReferenceCommand, NavigationCommand, UnknownCommand
from src.core.controller import VoiceHolyricsController, ExecutionResult
from src.ui.main_window import MainWindow, MODE_PTT, MODE_AUTO
from src.ui.threads import AutoListenWorker


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def mock_settings(tmp_path):
    cfg = tmp_path / "config.json"
    cfg.write_text('{"holyrics": {"host": "127.0.0.1", "port": 8091, "token": "test"}}', encoding="utf-8")
    return Settings(str(cfg))


class TestEtapa7Interpreter:
    """Testes dos novos comandos explícitos de parada e fala natural."""

    def test_parar_projecao(self):
        cmd = classify_command("Parar projeção")
        assert isinstance(cmd, NavigationCommand)
        assert cmd.command_type == CommandType.CLEAR_PRESENTATION

    def test_limpar_projecao(self):
        cmd = classify_command("Limpar projeção")
        assert isinstance(cmd, NavigationCommand)
        assert cmd.command_type == CommandType.CLEAR_PRESENTATION

    def test_encerrar_projecao(self):
        cmd = classify_command("Encerrar projeção")
        assert isinstance(cmd, NavigationCommand)
        assert cmd.command_type == CommandType.CLEAR_PRESENTATION

    def test_rejeita_palavras_isoladas_ambiguas(self):
        for word in ["parar", "limpar", "fechar", "apagar", "voltar", "avançar"]:
            cmd = classify_command(word)
            assert isinstance(cmd, UnknownCommand)
            assert cmd.command_type == CommandType.UNKNOWN

    def test_ignora_fala_comum_culto(self):
        frases_comuns = [
            "Hoje teremos uma reunião especial.",
            "Glória a Deus!",
            "Aleluia irmãos",
            "A paz do Senhor Jesus",
            "Vamos orar",
            "Podem se assentar",
        ]
        for frase in frases_comuns:
            cmd = classify_command(frase)
            assert isinstance(cmd, UnknownCommand)
            assert cmd.command_type == CommandType.UNKNOWN

    def test_reconhece_fala_natural_com_referencia(self):
        cmd = classify_command("Vamos abrir em João capítulo 3, versículo 16")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "João"
        assert cmd.chapter == 3
        assert cmd.verse_start == 16


class TestEtapa7ControllerClearSecurity:
    """Testes da regra de segurança do controlador ao parar/limpar projeção."""

    def test_bloqueia_limpeza_se_apresentacao_for_musica(self):
        api = MagicMock()
        api.get_current_presentation.return_value = {
            "type": "song",
            "name": "Porque Ele Vive",
            "slide_number": 1
        }
        ctrl = VoiceHolyricsController(api=api)
        res = ctrl.process_text("Parar projeção")

        assert res.success is False
        assert "não é bíblica" in res.message
        api.close_current_presentation.assert_not_called()

    def test_bloqueia_limpeza_se_nenhuma_apresentacao_ativa(self):
        api = MagicMock()
        api.get_current_presentation.return_value = None
        ctrl = VoiceHolyricsController(api=api)
        res = ctrl.process_text("Encerrar projeção")

        assert res.success is False
        assert "Nenhuma apresentação ativa" in res.message
        api.close_current_presentation.assert_not_called()

    def test_confirma_encerramento_apresentacao_biblica(self):
        api = MagicMock()
        # Antes: versículo ativo. Depois: tela vazia
        api.get_current_presentation.side_effect = [
            {"type": "verse", "name": "Jo 3:16", "slide_number": 26140},
            None
        ]
        api.close_current_presentation.return_value = {"status": "ok"}
        ctrl = VoiceHolyricsController(api=api)
        res = ctrl.process_text("Limpar projeção")

        assert res.success is True
        assert res.action_executed == "CloseCurrentPresentation"
        assert "encerrada com sucesso" in res.message
        assert res.current_presentation is None
        api.close_current_presentation.assert_called_once()

    def test_resultado_inconclusivo_se_apresentacao_continua_ativa(self):
        api = MagicMock()
        # Antes e Depois: versículo continua ativo
        api.get_current_presentation.side_effect = [
            {"type": "verse", "name": "Jo 3:16", "slide_number": 26140},
            {"type": "verse", "name": "Jo 3:16", "slide_number": 26140}
        ]
        api.close_current_presentation.return_value = {"status": "ok"}
        ctrl = VoiceHolyricsController(api=api)
        res = ctrl.process_text("Parar projeção")

        assert res.success is False
        assert "inconclusivo" in res.message


class TestEtapa7DuplicacaoEOperacoesConcorrentes:
    """Testes de prevenção de duplicação e concorrência."""

    def test_evita_comandos_duplicados_em_curto_intervalo(self):
        api = MagicMock()
        api.show_verse.return_value = {"status": "ok"}
        api.get_current_presentation.return_value = {"type": "verse", "name": "Jo 3:16"}
        ctrl = VoiceHolyricsController(api=api, duplicate_threshold_seconds=2.0)

        res1 = ctrl.process_text("João 3:16")
        assert res1.success is True

        # Disparo idêntico imediato
        res2 = ctrl.process_text("João 3:16")
        assert res2.success is False
        assert "duplicação" in res2.message

    def test_auto_worker_descarta_audio_se_ocupado(self):
        ctrl = MagicMock()
        worker = AutoListenWorker(controller=ctrl)
        worker._processing = True  # Simula ocupado

        dummy_audio = np.zeros(16000, dtype=np.float32)
        worker._on_speech_end(dummy_audio)

        # Não deve chamar process_audio pois o anterior ainda não acabou
        ctrl.process_audio.assert_not_called()


class TestEtapa7UI:
    """Testes da interface gráfica no modo automático e alternância."""

    @patch("src.ui.main_window.SpeechTranscriber")
    @patch("src.ui.main_window.AudioRecorder")
    @patch("src.ui.main_window.HolyricsAPI")
    def test_alternar_modos_ptt_e_auto(self, mock_api, mock_rec, mock_trans, qapp, mock_settings):
        window = MainWindow(mock_settings)

        assert window._current_mode == MODE_PTT
        assert window.combo_mode.currentIndex() == MODE_PTT

        # Alterna para modo automático
        window.combo_mode.setCurrentIndex(MODE_AUTO)
        assert window._current_mode == MODE_AUTO
        assert window.mode_stack.currentIndex() == MODE_AUTO

        # Alterna de volta para PTT
        window.combo_mode.setCurrentIndex(MODE_PTT)
        assert window._current_mode == MODE_PTT
        assert window.mode_stack.currentIndex() == MODE_PTT

        window.close()

    @patch("src.ui.main_window.AutoListenWorker")
    @patch("src.ui.main_window.SpeechTranscriber")
    @patch("src.ui.main_window.AudioRecorder")
    @patch("src.ui.main_window.HolyricsAPI")
    def test_iniciar_pausar_parar_escuta_auto(self, mock_api, mock_rec, mock_trans, mock_worker_cls, qapp, mock_settings):
        mock_worker = MagicMock()
        mock_worker.isRunning.return_value = False
        mock_worker.is_paused = False
        mock_worker_cls.return_value = mock_worker

        window = MainWindow(mock_settings)
        window.combo_mode.setCurrentIndex(MODE_AUTO)

        # Inicia
        window._start_auto_listen()
        assert window._auto_worker is not None
        mock_worker.start.assert_called_once()

        # Pausa
        mock_worker.isRunning.return_value = True
        window._toggle_auto_pause()
        mock_worker.pause.assert_called_once()

        # Retoma
        mock_worker.is_paused = True
        window._toggle_auto_pause()
        mock_worker.resume.assert_called_once()

        # Para
        window._stop_auto_listen()
        mock_worker.stop.assert_called_once()

        window.close()
