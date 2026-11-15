"""
Módulo robusto de captura de áudio com sounddevice.

Oferece:
- Listagem e seleção de microfones com verificação de canais e taxas.
- Captura de áudio a 16kHz mono (formato nativo esperado pelo Whisper).
- Modo Push-to-Talk seguro: o buffer NUNCA é descartado automaticamente no meio da gravação.
- Medição contínua de volume (RMS, Pico, dBFS) via callback.
- Tratamento robusto de desconexão e falhas de hardware.
"""

import threading
from typing import Callable, Optional
import numpy as np

try:
    import sounddevice as sd
except ImportError:
    sd = None

from src.core.logging_config import get_logger
from src.voice.vad import EnergyVAD
from src.voice.audio_utils import calculate_audio_metrics, AudioMetrics

logger = get_logger(__name__)


def list_audio_devices() -> list[dict]:
    """Lista todos os dispositivos de entrada de áudio disponíveis no sistema.

    Returns:
        Lista de dicionários com 'index', 'name', 'channels', 'default'.
    """
    if sd is None:
        logger.error("sounddevice não está instalado.")
        return []

    try:
        devices = sd.query_devices()
        default_in = sd.default.device[0]
        input_devices = []

        for idx, dev in enumerate(devices):
            if dev.get("max_input_channels", 0) > 0:
                input_devices.append({
                    "index": idx,
                    "name": dev.get("name", f"Microfone {idx}"),
                    "channels": dev.get("max_input_channels", 1),
                    "default_samplerate": dev.get("default_samplerate", 16000),
                    "is_default": (idx == default_in),
                })
        return input_devices
    except Exception as exc:
        logger.error("Erro ao listar dispositivos de áudio: %s", exc)
        return []


class AudioRecorder:
    """Gerenciador de captura de áudio via microfone."""

    def __init__(
        self,
        device_index: Optional[int] = None,
        sample_rate: int = 16000,
        vad_threshold: float = 0.015,
        silence_seconds: float = 0.8,
        mode: str = "push_to_talk",  # "push_to_talk" ou "auto_vad"
    ):
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.mode = mode
        self.vad = EnergyVAD(
            energy_threshold=vad_threshold,
            silence_duration_seconds=silence_seconds,
            sample_rate=sample_rate,
        )

        self._is_recording = False
        self._stream: Optional[sd.InputStream] = None
        self._audio_buffer: list[np.ndarray] = []
        self._lock = threading.Lock()

        # Métricas da última gravação
        self.last_metrics: Optional[AudioMetrics] = None

        # Callbacks
        self.on_speech_start: Optional[Callable[[], None]] = None
        self.on_speech_end: Optional[Callable[[np.ndarray], None]] = None
        self.on_level_meter: Optional[Callable[[AudioMetrics], None]] = None
        self.on_error: Optional[Callable[[str], None]] = None

    @property
    def is_recording(self) -> bool:
        return self._is_recording

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info, status):
        """Callback executado pela thread de áudio do sounddevice."""
        if status:
            logger.warning("Alerta de hardware de áudio: %s", status)

        # indata shape: (frames, 1), converte para float32 1D
        chunk = indata[:, 0].astype(np.float32)

        # Calcula métricas instantâneas do bloco atual para medidor de volume
        if self.on_level_meter:
            chunk_metrics = calculate_audio_metrics(chunk, sample_rate=self.sample_rate)
            self.on_level_meter(chunk_metrics)

        with self._lock:
            if not self._is_recording:
                return

            self._audio_buffer.append(chunk.copy())

            # No modo auto_vad, monitora término automático da fala
            if self.mode == "auto_vad":
                is_voice, speech_ended = self.vad.process_chunk(chunk)

                if is_voice and self.vad.speech_samples_count == len(chunk):
                    if self.on_speech_start:
                        self.on_speech_start()

                if speech_ended:
                    complete_audio = np.concatenate(self._audio_buffer)
                    self._audio_buffer.clear()
                    self.vad.reset()

                    if self.on_speech_end:
                        # Executa em thread separada para o callback não atrasar o retorno do buffer de áudio do driver
                        threading.Thread(target=self.on_speech_end, args=(complete_audio,), daemon=True).start()

    def start_recording(self) -> bool:
        """Inicia a gravação no microfone selecionado."""
        if sd is None:
            if self.on_error:
                self.on_error("sounddevice não está instalado.")
            return False

        with self._lock:
            if self._is_recording:
                return True

            self._audio_buffer.clear()
            self.vad.reset()

            try:
                self._stream = sd.InputStream(
                    device=self.device_index,
                    channels=1,
                    samplerate=self.sample_rate,
                    dtype="float32",
                    blocksize=int(self.sample_rate * 0.1),  # Blocos de 100ms (1600 amostras) para estabilidade
                    callback=self._audio_callback,
                )
                self._stream.start()
                self._is_recording = True
                logger.info("Captura de áudio iniciada no dispositivo %s", self.device_index)
                return True
            except Exception as exc:
                err_msg = f"Falha ao abrir microfone: {exc}"
                logger.error(err_msg)
                if self.on_error:
                    self.on_error(err_msg)
                return False

    def stop_recording(self) -> Optional[np.ndarray]:
        """Interrompe a gravação e retorna o áudio acumulado integralmente."""
        with self._lock:
            if not self._is_recording:
                return None

            self._is_recording = False
            try:
                if self._stream:
                    self._stream.stop()
                    self._stream.close()
                    self._stream = None
            except Exception as exc:
                logger.warning("Erro ao encerrar stream de áudio: %s", exc)

            if not self._audio_buffer:
                self.last_metrics = None
                return None

            # Concatena o áudio gravado
            audio_data = np.concatenate(self._audio_buffer)
            self._audio_buffer.clear()
            self.vad.reset()

            # Calcula e armazena métricas finais
            self.last_metrics = calculate_audio_metrics(audio_data, sample_rate=self.sample_rate)
            return audio_data
