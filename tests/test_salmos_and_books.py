"""
Testes automatizados específicos para Salmos e livros bíblicos de fonética sensível.
Garante que melhorias não prejudiquem o reconhecimento dos livros já funcionais.
"""

import numpy as np
import pytest
from src.interpreter import classify_command, BibleReferenceCommand, CommandType
from src.voice.audio_utils import calculate_audio_metrics, normalize_audio


class TestSalmosPatterns:
    """Testes obrigatórios para diferentes formas de falar Salmos."""

    def test_salmos_vinte_e_tres(self):
        cmd = classify_command("Salmos vinte e três")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "Salmos"
        assert cmd.chapter == 23
        assert cmd.verse_start is None
        assert cmd.holyrics_reference == "Sl 23"

    def test_salmo_vinte_e_tres(self):
        cmd = classify_command("Salmo vinte e três")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "Salmos"
        assert cmd.chapter == 23
        assert cmd.holyrics_reference == "Sl 23"

    def test_salmos_capitulo_vinte_e_tres(self):
        cmd = classify_command("Salmos capítulo vinte e três")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "Salmos"
        assert cmd.chapter == 23
        assert cmd.holyrics_reference == "Sl 23"

    def test_salmos_vinte_e_tres_versiculo_um(self):
        cmd = classify_command("Salmos vinte e três versículo um")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "Salmos"
        assert cmd.chapter == 23
        assert cmd.verse_start == 1
        assert cmd.holyrics_reference == "Sl 23:1"

    def test_salmos_noventa_e_um(self):
        cmd = classify_command("Salmos noventa e um")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "Salmos"
        assert cmd.chapter == 91
        assert cmd.holyrics_reference == "Sl 91"

    def test_salmos_cento_e_dezenove(self):
        cmd = classify_command("Salmos cento e dezenove")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "Salmos"
        assert cmd.chapter == 119
        assert cmd.holyrics_reference == "Sl 119"


class TestOtherBooksRegressions:
    """Garante que os livros já funcionais continuem 100% íntegros."""

    def test_genesis_1_1(self):
        cmd = classify_command("Gênesis 1 versículo 1")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "Gênesis"
        assert cmd.chapter == 1
        assert cmd.verse_start == 1
        assert cmd.holyrics_reference == "Gn 1:1"

    def test_mateus_6_12(self):
        cmd = classify_command("Mateus seis doze")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "Mateus"
        assert cmd.chapter == 6
        assert cmd.verse_start == 12
        assert cmd.holyrics_reference == "Mt 6:12"

    def test_apocalipse_1_1(self):
        cmd = classify_command("Apocalipse um um")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "Apocalipse"
        assert cmd.chapter == 1
        assert cmd.verse_start == 1
        assert cmd.holyrics_reference == "Ap 1:1"

    def test_exodo_20_1(self):
        cmd = classify_command("Êxodo vinte versículo um")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "Êxodo"
        assert cmd.chapter == 20
        assert cmd.verse_start == 1
        assert cmd.holyrics_reference == "Êx 20:1"

    def test_deuteronomio_6_4(self):
        cmd = classify_command("Deuteronômio seis versículo quatro")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "Deuteronômio"
        assert cmd.chapter == 6
        assert cmd.verse_start == 4
        assert cmd.holyrics_reference == "Dt 6:4"

    def test_primeiro_tessalonicenses_5_16(self):
        cmd = classify_command("Primeiro Tessalonicenses cinco dezesseis")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "1 Tessalonicenses"
        assert cmd.chapter == 5
        assert cmd.verse_start == 16
        assert cmd.holyrics_reference == "1Ts 5:16"


class TestAudioUtils:
    """Testes de processamento e normalização de áudio."""

    def test_metricas_silencio(self):
        silent_audio = np.zeros(16000, dtype=np.float32)
        metrics = calculate_audio_metrics(silent_audio)
        assert metrics.is_silent is True
        assert metrics.rms == 0.0
        assert metrics.peak == 0.0

    def test_normalizacao_de_sinal_baixo(self):
        # Sinal fraco com pico 0.1
        t = np.linspace(0, 1.0, 16000, endpoint=False)
        low_audio = (0.1 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

        metrics_before = calculate_audio_metrics(low_audio)
        assert metrics_before.peak == pytest.approx(0.1, abs=0.01)

        normalized = normalize_audio(low_audio, target_peak=0.85)
        metrics_after = calculate_audio_metrics(normalized)
        assert metrics_after.peak == pytest.approx(0.85, abs=0.02)

    def test_nao_amplifica_silencio_puro(self):
        silent = np.zeros(16000, dtype=np.float32)
        normalized = normalize_audio(silent, target_peak=0.85)
        assert np.max(np.abs(normalized)) == 0.0
