"""
Testes automatizados da ETAPA 3 — Reconhecimento de Voz e VAD.
"""

import numpy as np
import pytest
from src.voice.vad import EnergyVAD
from src.voice.transcriber import SpeechTranscriber, TranscriptionResult
from src.voice.recorder import AudioRecorder


class TestEnergyVAD:
    """Testa a separação de fala e silêncio do detector de atividade de voz."""

    def test_silencio_puro(self):
        vad = EnergyVAD(energy_threshold=0.015, sample_rate=16000)
        silent_chunk = np.zeros(800, dtype=np.float32)

        is_voice, speech_ended = vad.process_chunk(silent_chunk)
        assert is_voice is False
        assert speech_ended is False
        assert vad.is_speech_active is False

    def test_deteccao_voz_e_termino_por_silencio(self):
        vad = EnergyVAD(
            energy_threshold=0.015,
            silence_duration_seconds=0.2,  # 3200 amostras
            sample_rate=16000,
        )

        # 1. Envia 0.5s de áudio ruidoso/voz (onda senoidal com amplitude 0.2)
        sr = 16000
        t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
        voice_chunk = (0.2 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)

        is_voice, speech_ended = vad.process_chunk(voice_chunk)
        assert is_voice is True
        assert speech_ended is False
        assert vad.is_speech_active is True

        # 2. Envia blocos de silêncio para acionar speech_ended
        silent_chunk = np.zeros(1600, dtype=np.float32)  # 0.1s cada
        _, ended1 = vad.process_chunk(silent_chunk)
        assert ended1 is False  # 0.1s de silêncio ainda não atingiu o limite de 0.2s

        _, ended2 = vad.process_chunk(silent_chunk)
        assert ended2 is True  # Agora atingiu 0.2s de silêncio pós-voz!
        assert vad.is_speech_active is False


class TestTranscriberStructure:
    """Testa o comportamento e regras de incerteza do transcritor."""

    def test_transcricao_vazia_quando_nao_inicializado(self):
        transcriber = SpeechTranscriber()
        # Se faster-whisper não estiver instalado ou falhar, deve retornar objeto seguro
        res = transcriber.transcribe(np.zeros(16000, dtype=np.float32))
        assert isinstance(res, TranscriptionResult)
        assert res.is_uncertain is True
