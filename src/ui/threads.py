"""
Threads assíncronas (Workers) em PySide6 para tarefas de segundo plano.

Garante que nem a captura de áudio, nem a inferência do faster-whisper,
nem as chamadas de rede ao Holyrics travem a UI thread principal.
"""

from typing import Optional
import threading
import numpy as np
from PySide6.QtCore import QThread, Signal

from src.core.controller import VoiceHolyricsController, ExecutionResult
from src.core.logging_config import get_logger
from src.holyrics.api import HolyricsAPI
from src.voice.recorder import AudioRecorder
from src.voice.audio_utils import AudioMetrics

logger = get_logger(__name__)


class CommandProcessingWorker(QThread):
    """Thread dedicada ao processamento de áudio (Whisper) e envio à API do Holyrics."""

    # Sinais emitidos de volta para a UI Thread de forma thread-safe
    processing_started = Signal()
    finished = Signal(ExecutionResult)

    def __init__(
        self,
        controller: VoiceHolyricsController,
        audio_data: Optional[np.ndarray] = None,
        text_command: Optional[str] = None,
        parent=None,
    ):
        super().__init__(parent)
        self.controller = controller
        self.audio_data = audio_data
        self.text_command = text_command

    def run(self):
        """Executa a inferência e o controlador em background."""
        self.processing_started.emit()

        if self.audio_data is not None:
            result = self.controller.process_audio(self.audio_data)
        elif self.text_command is not None:
            result = self.controller.process_text(self.text_command)
        else:
            return

        self.finished.emit(result)


class HolyricsSyncWorker(QThread):
    """Thread contínua de baixa prioridade para sincronizar a TV caso o operador
    mude de versículo manualmente no Holyrics.
    """

    presentation_synced = Signal(object)  # dict ou None
    connection_status_changed = Signal(bool)

    def __init__(self, api: HolyricsAPI, interval_seconds: float = 2.0, parent=None):
        super().__init__(parent)
        self.api = api
        self.interval_seconds = interval_seconds
        self._running = True

    def stop(self):
        """Para a thread de sincronização com segurança."""
        self._running = False
        self.wait(1000)

    def run(self):
        while self._running:
            try:
                # Verifica status de conexão
                status = self.api.get_status()
                self.connection_status_changed.emit(status.connected)

                if status.connected:
                    pres = self.api.get_current_presentation()
                    self.presentation_synced.emit(pres)
                else:
                    self.presentation_synced.emit(None)

            except Exception as exc:
                logger.debug("Falha na sincronização periódica: %s", exc)
                self.connection_status_changed.emit(False)
                self.presentation_synced.emit(None)

            # Aguarda intervalo em fatias curtas para encerramento responsivo
            elapsed = 0.0
            while self._running and elapsed < self.interval_seconds:
                self.msleep(200)
                elapsed += 0.2


class AutoListenWorker(QThread):
    """Thread de escuta automática contínua com VAD.

    Mantém o AudioRecorder em modo auto_vad. Quando o VAD detecta o fim
    de uma fala, o segmento de áudio é despachado para o controller.
    Se o controller já estiver processando um segmento anterior,
    o novo segmento é descartado (proteção contra fila ilimitada).

    Sinais:
        speech_detected: Emitido quando o VAD identifica início de fala.
        result_ready: Emitido quando o processamento termina (ExecutionResult).
        listening_status: Emitido com True/False quando a escuta inicia/para.
        error_occurred: Emitido com mensagem de erro.
        level_meter: Emitido com AudioMetrics a cada bloco de áudio capturado.
    """

    speech_detected = Signal()
    result_ready = Signal(ExecutionResult)
    listening_status = Signal(bool)
    error_occurred = Signal(str)
    level_meter = Signal(AudioMetrics)

    def __init__(
        self,
        controller: VoiceHolyricsController,
        device_index: Optional[int] = None,
        sample_rate: int = 16000,
        vad_threshold: float = 0.015,
        silence_seconds: float = 1.0,
        parent=None,
    ):
        super().__init__(parent)
        self.controller = controller
        self.device_index = device_index
        self.sample_rate = sample_rate
        self.vad_threshold = vad_threshold
        self.silence_seconds = silence_seconds

        self._running = False
        self._paused = False
        self._processing = False
        self._processing_lock = threading.Lock()
        self._recorder: Optional[AudioRecorder] = None

    @property
    def is_paused(self) -> bool:
        return self._paused

    def pause(self):
        """Pausa a escuta automática sem destruir a thread."""
        self._paused = True
        logger.info("Escuta automática pausada.")

    def resume(self):
        """Retoma a escuta automática."""
        self._paused = False
        logger.info("Escuta automática retomada.")

    def stop(self):
        """Solicita parada segura da escuta automática."""
        self._running = False

    def run(self):
        """Loop principal da escuta automática."""
        logger.info("Escuta automática iniciada.")
        self._running = True
        self._paused = False

        self._recorder = AudioRecorder(
            device_index=self.device_index,
            sample_rate=self.sample_rate,
            vad_threshold=self.vad_threshold,
            silence_seconds=self.silence_seconds,
            mode="auto_vad",
        )

        # Registra callbacks do AudioRecorder
        self._recorder.on_speech_start = self._on_speech_start
        self._recorder.on_speech_end = self._on_speech_end
        self._recorder.on_level_meter = self._on_level_meter
        self._recorder.on_error = self._on_recorder_error

        if not self._recorder.start_recording():
            self.error_occurred.emit("Falha ao abrir o microfone para escuta automática.")
            self.listening_status.emit(False)
            return

        self.listening_status.emit(True)

        # Mantém a thread viva enquanto a escuta estiver ativa
        while self._running:
            self.msleep(100)

        # Encerra limpa o stream
        try:
            if self._recorder.is_recording:
                self._recorder.stop_recording()
        except Exception as exc:
            logger.warning("Erro ao parar recorder na finalização: %s", exc)

        self._recorder = None
        self.listening_status.emit(False)
        logger.info("Escuta automática encerrada.")

    def _on_speech_start(self):
        """Callback: VAD detectou início de fala."""
        if self._paused:
            return
        self.speech_detected.emit()

    def _on_speech_end(self, audio: np.ndarray):
        """Callback: VAD detectou fim de fala — despacha para processamento.

        PROTEÇÃO CONTRA FILA ILIMITADA:
        Se o controller já estiver processando um segmento anterior,
        este segmento é descartado com log.
        """
        if self._paused:
            logger.debug("Segmento de fala descartado: escuta pausada.")
            return

        if audio is None or len(audio) < 3200:  # < 0.2s
            logger.debug("Segmento de fala muito curto, descartado.")
            return

        with self._processing_lock:
            if self._processing:
                logger.info("Segmento descartado: processamento anterior ainda ativo.")
                return
            self._processing = True

        # Despacha a inferência para uma thread separada (worker independente)
        # para NÃO BLOQUEAR o loop run() da thread AutoListenWorker!
        # Isso garante que o sounddevice continue alimentando blocos sem gerar input overflow!
        threading.Thread(
            target=self._run_inference_async,
            args=(audio,),
            daemon=True
        ).start()

    def _run_inference_async(self, audio: np.ndarray):
        """Executa a inferência em background assíncrono isolado."""
        try:
            result = self.controller.process_audio(audio)
            self.result_ready.emit(result)
        except Exception as exc:
            logger.error("Erro durante processamento automático: %s", exc)
            self.error_occurred.emit(f"Erro de processamento: {exc}")
        finally:
            with self._processing_lock:
                self._processing = False

    def _on_level_meter(self, metrics: AudioMetrics):
        """Callback: repassa métricas de volume para a UI."""
        if not self._paused:
            self.level_meter.emit(metrics)

    def _on_recorder_error(self, msg: str):
        """Callback: erro no hardware de áudio."""
        logger.error("Erro no microfone (modo automático): %s", msg)
        self.error_occurred.emit(msg)
