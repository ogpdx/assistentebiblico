"""
Ponto de entrada do módulo voice.
"""

from src.voice.vad import EnergyVAD
from src.voice.audio_utils import calculate_audio_metrics, normalize_audio, render_vu_meter, AudioMetrics
from src.voice.recorder import AudioRecorder, list_audio_devices
from src.voice.transcriber import SpeechTranscriber, TranscriptionResult

__all__ = [
    "EnergyVAD",
    "AudioMetrics",
    "calculate_audio_metrics",
    "normalize_audio",
    "render_vu_meter",
    "AudioRecorder",
    "list_audio_devices",
    "SpeechTranscriber",
    "TranscriptionResult",
]
