"""
Módulo de detecção de atividade de voz (VAD) e cálculo de energia.

Usa RMS de energia e detecção de silêncio para identificar quando o usuário
iniciou e terminou de falar, separando a fala do ruído de fundo antes
de enviar o buffer de áudio ao Whisper.
"""

import numpy as np


class EnergyVAD:
    """Detector de atividade vocal baseado em energia sonora (RMS) e limiar adaptativo."""

    def __init__(
        self,
        energy_threshold: float = 0.015,
        silence_duration_seconds: float = 0.8,
        sample_rate: int = 16000,
    ):
        self.energy_threshold = energy_threshold
        self.silence_duration_seconds = silence_duration_seconds
        self.sample_rate = sample_rate

        self.silence_limit_chunks = int(silence_duration_seconds * sample_rate)
        self.reset()

    def reset(self) -> None:
        """Reinicia o estado da detecção."""
        self.is_speech_active = False
        self.silent_samples_count = 0
        self.speech_samples_count = 0

    def calculate_rms(self, audio_chunk: np.ndarray) -> float:
        """Calcula o valor RMS (Root Mean Square) do bloco de áudio."""
        if len(audio_chunk) == 0:
            return 0.0
        return float(np.sqrt(np.mean(np.square(audio_chunk, dtype=np.float32))))

    def process_chunk(self, audio_chunk: np.ndarray) -> tuple[bool, bool]:
        """Processa um pedaço de áudio e atualiza o estado de fala.

        Args:
            audio_chunk: Array numpy 1D float32.

        Returns:
            Tupla (is_speech_detected, speech_ended):
            - is_speech_detected: True se o bloco atual tem energia de fala.
            - speech_ended: True se houve fala prévia e o silêncio atingiu o limite configurado.
        """
        rms = self.calculate_rms(audio_chunk)
        chunk_len = len(audio_chunk)

        is_voice = rms >= self.energy_threshold
        speech_ended = False

        if is_voice:
            self.is_speech_active = True
            self.silent_samples_count = 0
            self.speech_samples_count += chunk_len
        else:
            if self.is_speech_active:
                self.silent_samples_count += chunk_len
                # Se acumulou silêncio suficiente após um período mínimo de fala (pelo menos 0.3s)
                if (
                    self.silent_samples_count >= self.silence_limit_chunks
                    and self.speech_samples_count >= int(0.3 * self.sample_rate)
                ):
                    speech_ended = True
                    self.is_speech_active = False

        return is_voice, speech_ended
