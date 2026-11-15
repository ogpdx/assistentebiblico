"""
Módulo de transcrição local usando faster-whisper.

Configurações otimizadas para precisão em culto:
- Prompt contextual com sentenças eclesiásticas e bíblicas reais em português brasileiro.
- Normalização dinâmica de amplitude (Peak Normalization) pré-inferência.
- Parâmetros anti-alucinação: condition_on_previous_text=False para não forçar referências do prompt em silêncio.
- Beam search configurável (padrão beam_size=2) para evitar erros fonéticos em palavras como 'Salmos'.
"""

from dataclasses import dataclass
import os
import time
from pathlib import Path
from typing import Optional
import numpy as np

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None

from src.core.logging_config import get_logger
from src.core.path_utils import get_models_dir
from src.voice.audio_utils import calculate_audio_metrics, normalize_audio, AudioMetrics

logger = get_logger(__name__)

# Prompt bíblico estruturado em frases naturais para orientar a probabilidade das palavras
# sem forçar alucinações
BIBLE_INITIAL_PROMPT = (
    "Leitura da Bíblia Sagrada na igreja: "
    "Salmos capítulo 23, versículo 1. "
    "Salmo 91. Salmo 119, versículo 105. "
    "Gênesis capítulo 1, versículo 1 ao 3. "
    "Êxodo capítulo 20, versículo 1. "
    "Deuteronômio capítulo 6, versículo 4. "
    "Primeiro Reis capítulo 1, versículo 2. "
    "Romanos capítulo 8, versículo 1 ao 4. "
    "Primeiro Coríntios capítulo 13, versículo 4. "
    "Primeiro Tessalonicenses capítulo 5, versículo 16. "
    "Apocalipse capítulo 22, versículo 20. "
    "Próximo versículo. Versículo anterior. Limpar projeção."
)


@dataclass
class TranscriptionResult:
    """Resultado estruturado e detalhado da transcrição."""
    text: str
    duration_seconds: float
    inference_time_seconds: float
    confidence: float
    no_speech_prob: float
    is_uncertain: bool
    metrics: AudioMetrics


class SpeechTranscriber:
    """Transcritor de voz offline baseado em faster-whisper."""

    def __init__(
        self,
        model_size: str = "base",
        device: str = "cpu",
        compute_type: str = "int8",
        beam_size: int = 2,
        download_root: Optional[str] = "models",
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.beam_size = beam_size
        self.download_root = download_root

        self._model: Optional[WhisperModel] = None

    def is_loaded(self) -> bool:
        return self._model is not None

    def load_model(self) -> bool:
        """Carrega o modelo Whisper em memória."""
        if WhisperModel is None:
            logger.error("faster-whisper não está instalado.")
            return False

        if self._model is not None:
            return True

        logger.info(
            "Carregando modelo faster-whisper '%s' (device=%s, compute_type=%s, beam_size=%d)...",
            self.model_size, self.device, self.compute_type, self.beam_size
        )
        try:
            target_download_root = self.download_root or str(get_models_dir())
            os.makedirs(target_download_root, exist_ok=True)

            # Prioriza carregar diretamente da pasta local se o snapshot/model.bin existir
            # Isso evita que o faster-whisper/huggingface_hub tente consultar a API do Hugging Face online!
            model_to_load = self.model_size
            local_bin_files = list(Path(target_download_root).rglob("model.bin"))
            if local_bin_files:
                # Usa o diretório exato onde estão model.bin, config.json, tokenizer.json
                model_to_load = str(local_bin_files[0].parent)
                logger.info("Snapshot local de modelo encontrado: '%s'. Carregando 100%% offline.", model_to_load)

            # Garante flags de ambiente offline caso o modelo já exista localmente
            if local_bin_files or os.path.exists(model_to_load):
                os.environ["HF_HUB_OFFLINE"] = "1"
                os.environ["TRANSFORMERS_OFFLINE"] = "1"

            self._model = WhisperModel(
                model_to_load,
                device=self.device,
                compute_type=self.compute_type,
                download_root=target_download_root,
                cpu_threads=4,
                local_files_only=True if (local_bin_files or os.path.exists(model_to_load)) else False,
            )
            logger.info("Modelo faster-whisper carregado com sucesso de '%s'.", model_to_load)
            return True
        except Exception as exc:
            logger.error("Erro ao carregar modelo faster-whisper: %s", exc)
            return False

    def transcribe(self, audio: np.ndarray, apply_normalization: bool = True) -> TranscriptionResult:
        """Transcreve um array de áudio (16kHz mono, float32).

        Args:
            audio: Array 1D numpy (float32).
            apply_normalization: Se True, aplica ganho de pico proporcional antes da inferência.

        Returns:
            TranscriptionResult com texto, métricas acústicas e confiança.
        """
        # Calcula métricas acústicas do áudio original
        metrics = calculate_audio_metrics(audio, sample_rate=16000)

        # Se o áudio for silêncio absoluto ou inaudível (RMS < 0.001), não gera alucinação
        if metrics.is_silent or metrics.duration_seconds < 0.2:
            return TranscriptionResult(
                text="",
                duration_seconds=metrics.duration_seconds,
                inference_time_seconds=0.0,
                confidence=0.0,
                no_speech_prob=1.0,
                is_uncertain=True,
                metrics=metrics,
            )

        if not self.is_loaded():
            if not self.load_model():
                return TranscriptionResult(
                    text="",
                    duration_seconds=metrics.duration_seconds,
                    inference_time_seconds=0.0,
                    confidence=0.0,
                    no_speech_prob=1.0,
                    is_uncertain=True,
                    metrics=metrics,
                )

        # Normaliza ganho se necessário para que o Whisper receba sinal na amplitude correta
        processed_audio = normalize_audio(audio, target_peak=0.85) if apply_normalization else audio

        start_time = time.perf_counter()

        try:
            # Em gravações push-to-talk já delimitadas, o VAD interno com parâmetros relaxados
            # evita o descarte indevido de áudios de 3.5 segundos
            segments, info = self._model.transcribe(
                processed_audio,
                language="pt",
                beam_size=self.beam_size,
                initial_prompt=BIBLE_INITIAL_PROMPT,
                condition_on_previous_text=False,  # Não alucina baseado no histórico anterior
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=1000,
                    speech_pad_ms=300,
                ),
                without_timestamps=True,
            )

            texts = []
            avg_logprobs = []
            no_speech_probs = []

            for seg in segments:
                t = seg.text.strip()
                if t:
                    texts.append(t)
                    avg_logprobs.append(seg.avg_logprob)
                    no_speech_probs.append(seg.no_speech_prob)

            inference_time = time.perf_counter() - start_time
            full_text = " ".join(texts).strip()

            mean_logprob = float(np.mean(avg_logprobs)) if avg_logprobs else -1.0
            mean_no_speech = float(np.mean(no_speech_probs)) if no_speech_probs else 0.0

            # Normalização simples do logprob para score 0.0 - 1.0
            confidence = float(np.clip(np.exp(mean_logprob), 0.0, 1.0)) if avg_logprobs else 0.0

            # Regras de incerteza operacional
            is_uncertain = (
                confidence < 0.40
                or mean_no_speech > 0.65
                or len(full_text) < 2
            )

            return TranscriptionResult(
                text=full_text,
                duration_seconds=metrics.duration_seconds,
                inference_time_seconds=inference_time,
                confidence=confidence,
                no_speech_prob=mean_no_speech,
                is_uncertain=is_uncertain,
                metrics=metrics,
            )

        except Exception as exc:
            logger.error("Erro durante a transcrição: %s", exc)
            return TranscriptionResult(
                text="",
                duration_seconds=metrics.duration_seconds,
                inference_time_seconds=time.perf_counter() - start_time,
                confidence=0.0,
                no_speech_prob=1.0,
                is_uncertain=True,
                metrics=metrics,
            )
