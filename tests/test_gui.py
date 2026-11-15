"""
Testes automatizados da Interface Gráfica (PySide6) - Etapa 5.
Testa instanciação, componentes visuais, diálogos e transições de estado com mocks.
"""

import sys
import pytest
from unittest.mock import MagicMock, patch
import numpy as np

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.config.settings import Settings
from src.ui.widgets.status_badge import StatusBadge
from src.ui.widgets.vu_meter import VUMeterWidget
from src.ui.dialogs.settings_dialog import SettingsDialog
from src.ui.main_window import MainWindow
from src.core.controller import ExecutionResult
from src.interpreter import BibleReferenceCommand


@pytest.fixture(scope="session")
def qapp():
    """Garante uma instância única de QApplication para a suíte de testes."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    yield app


@pytest.fixture
def mock_settings(tmp_path):
    """Cria uma instância de Settings em diretório temporário."""
    cfg = tmp_path / "config.json"
    cfg.write_text('{"holyrics": {"host": "127.0.0.1", "port": 8091, "token": "test"}}', encoding="utf-8")
    return Settings(str(cfg))


class TestStatusBadge:
    """Testes do widget StatusBadge."""

    def test_status_badge_states(self, qapp):
        badge = StatusBadge()
        assert badge._label.text() == "Aguardando"

        badge.set_state("listening")
        assert badge._label.text() == "Ouvindo..."

        badge.set_state("processing")
        assert badge._label.text() == "Processando..."

        badge.set_state("success", "Versículo Exibido")
        assert badge._label.text() == "Versículo Exibido"

        badge.set_state("error")
        assert badge._label.text() == "Não Reconhecido"


class TestVUMeterWidget:
    """Testes do widget VUMeterWidget."""

    def test_vu_meter_levels(self, qapp):
        vu = VUMeterWidget()
        assert vu.bar.value() == 0

        # Nível moderado
        vu.set_level(rms=0.1, peak=0.5, dbfs=-20.0)
        assert vu.bar.value() > 0
        assert "-20.0 dB" in vu.lbl_db.text()

        # Nível com pico / sobrecarga
        vu.set_level(rms=0.5, peak=1.0, dbfs=-0.1)
        assert vu.bar.value() == 100
        assert "-0.1 dB" in vu.lbl_db.text()

        # Silêncio / reset
        vu.reset()
        assert vu.bar.value() == 0
        assert "-inf dB" in vu.lbl_db.text()


class TestSettingsDialog:
    """Testes do diálogo de configurações."""

    @patch("src.ui.dialogs.settings_dialog.list_audio_devices")
    def test_settings_dialog_load_and_cancel(self, mock_devices, qapp, mock_settings):
        mock_devices.return_value = [
            {"index": 0, "name": "Microfone Padrão", "max_input_channels": 2, "default_samplerate": 16000.0}
        ]
        dialog = SettingsDialog(mock_settings)
        assert dialog.txt_host.text() == "127.0.0.1"
        assert dialog.spin_port.value() == 8091
        assert dialog.txt_token.text() == "test"
        dialog.reject()


class TestMainWindow:
    """Testes da janela principal MainWindow."""

    @patch("src.ui.main_window.SpeechTranscriber")
    @patch("src.ui.main_window.AudioRecorder")
    @patch("src.ui.main_window.HolyricsAPI")
    def test_main_window_init(self, mock_api_cls, mock_rec_cls, mock_trans_cls, qapp, mock_settings):
        # Mocks para não tentar inicializar hardware real ou rede
        mock_api = mock_api_cls.return_value
        mock_api.test_connection.return_value = (True, "Conectado")
        mock_api.get_current_presentation.return_value = {
            "type": "verse",
            "name": "Jo 3:16",
            "slide_number": 26140,
            "total_slides": 31106
        }

        window = MainWindow(mock_settings)
        assert "Assistente Bíblico" in window.windowTitle()
        assert window.btn_ptt is not None
        assert window.lbl_active_verse is not None
        assert window.vu_meter is not None

        # Testa atualização de VU Meter via callback
        from src.voice.audio_utils import AudioMetrics
        window._is_holding_talk = True
        window._on_audio_level_meter(
            AudioMetrics(
                rms=0.1,
                peak=0.5,
                dbfs=-20.0,
                duration_seconds=0.1,
                is_silent=False,
                is_clipping=False,
            )
        )

        # Testa resultado de comando simulado
        from src.interpreter.models import CommandType
        cmd = BibleReferenceCommand(
            command_type=CommandType.BIBLE_REFERENCE,
            raw_text="João 3:16",
            book_name="João",
            book_abbreviation="Jo",
            book_number=43,
            chapter=3,
            verse_start=16,
        )
        sample_res = ExecutionResult(
            success=True,
            raw_text="João 3:16",
            command=cmd,
            action_executed="ShowVerse",
            message="Versículo 'João 3:16' projetado com sucesso na TV!",
            current_presentation={"type": "verse", "name": "Jo 3:16", "slide_number": 26140}
        )
        window._on_processing_finished(sample_res)

        assert "João 3:16" in window.lbl_transcribed_text.text()
        assert "João 3:16" in window.lbl_interpreted_ref.text()
        assert "Jo 3:16" in window.lbl_active_verse.text()

        window.close()
