"""
Utilitários de processamento e métricas de sinal de áudio.

Fornece:
- Cálculo de métricas acústicas: RMS, Pico absoluto, dBFS.
- Detecção de silêncio/microfone mudo e clipping/saturação.
- Normalização de pico (Peak Normalization) para sinal ótimo ao Whisper.
- Renderizador de VU Meter em ASCII para visualização em tempo real no console.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class AudioMetrics:
    """Métricas acústicas calculadas para um segmento de áudio."""
    rms: float
    peak: float
    dbfs: float
    duration_seconds: float
    is_silent: bool
    is_clipping: bool


def calculate_audio_metrics(audio: np.ndarray, sample_rate: int = 16000) -> AudioMetrics:
    """Calcula métricas de volume e integridade do sinal de áudio."""
    if len(audio) == 0:
        return AudioMetrics(
            rms=0.0,
            peak=0.0,
            dbfs=-99.0,
            duration_seconds=0.0,
            is_silent=True,
            is_clipping=False,
        )

    # Garante float32
    audio_f = audio.astype(np.float32)

    peak = float(np.max(np.abs(audio_f)))
    rms = float(np.sqrt(np.mean(np.square(audio_f))))

    # Cálculo de dBFS (referência 1.0)
    if rms > 1e-6:
        dbfs = float(20.0 * np.log10(rms))
    else:
        dbfs = -99.0

    duration = len(audio) / float(sample_rate)

    # Limiares de alerta
    # Silêncio: RMS abaixo de 0.002 (-54 dBFS) é considerado quase inaudível
    is_silent = rms < 0.002
    # Clipping: amplitude máxima atingindo ou ultrapassando 0.98
    is_clipping = peak >= 0.98

    return AudioMetrics(
        rms=rms,
        peak=peak,
        dbfs=dbfs,
        duration_seconds=duration,
        is_silent=is_silent,
        is_clipping=is_clipping,
    )


def normalize_audio(audio: np.ndarray, target_peak: float = 0.85) -> np.ndarray:
    """Normaliza o áudio elevando seu ganho para o pico desejado.

    Evita amplificar silêncio absoluto (ruído de fundo puro).
    """
    if len(audio) == 0:
        return audio

    peak = float(np.max(np.abs(audio)))

    # Se o pico for muito baixo (< 0.002), o áudio é puro silêncio ou ruído, não amplifica
    # Se já tiver um bom nível (>= target_peak), não precisa mexer
    if peak < 0.002 or peak >= target_peak:
        return audio

    # Aplica ganho proporcional para atingir target_peak
    gain = target_peak / peak
    # Limita o ganho máximo a 10x (+20 dB) para evitar saturar estática
    gain = min(gain, 10.0)

    normalized = audio * gain
    return np.clip(normalized, -1.0, 1.0).astype(np.float32)


def render_vu_meter(rms: float, peak: float, width: int = 24) -> str:
    """Renderiza uma barra gráfica de VU Meter em texto ASCII para o terminal.

    Exemplo: [████████░░░░░░░░░░] -18.4 dB (Pico: 0.35)
    """
    # Mapeia RMS (0.0 a ~0.4) para a largura da barra
    level = min(max(rms * 3.5, 0.0), 1.0)
    filled = int(round(level * width))
    empty = width - filled

    bar = "█" * filled + "░" * empty

    if rms > 1e-5:
        db = 20.0 * np.log10(rms)
        db_str = f"{db:5.1f} dB"
    else:
        db_str = "-inf dB"

    clip_alert = " ⚠️ CLIP!" if peak >= 0.98 else ""
    return f"[{bar}] {db_str} (Pico: {peak:.2f}){clip_alert}"
