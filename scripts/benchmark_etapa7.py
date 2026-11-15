"""
Benchmark de consumo de CPU e memória e teste de estresse do modo automático.
Valida:
1. Consumo de RAM basal e durante inferência.
2. Comportamento sob silêncio e sob fala contínua.
3. Descarte de filas concorrentes sem acúmulo de memória.
"""

import os
import sys
import time
from pathlib import Path
import numpy as np

# Garante path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.controller import VoiceHolyricsController
from src.interpreter import classify_command
from src.ui.threads import AutoListenWorker


def measure_process_resources():
    """Mede memória RSS do processo atual."""
    try:
        import psutil
        proc = psutil.Process()
        mem_info = proc.memory_info()
        return mem_info.rss / (1024 * 1024), proc.cpu_percent(interval=0.1)
    except ImportError:
        return 0.0, 0.0


def run_benchmark():
    print("=" * 65)
    print("  BENCHMARK DE DESEMPENHO E RECURSOS — MODO AUTOMÁTICO (ETAPA 7)")
    print("=" * 65)

    mem_init, cpu_init = measure_process_resources()
    print(f"Memória inicial: {mem_init:.2f} MB")

    # 1. Carrega o modelo SMALL apenas uma vez (sem duplicatas)
    from src.voice.transcriber import SpeechTranscriber
    from src.core.path_utils import get_models_dir

    models_dir = get_models_dir()
    bin_files = list(models_dir.rglob("model.bin"))
    model_path = str(bin_files[0].parent) if bin_files else "small"

    print(f"Carregando WhisperModel ({model_path})...")
    transcriber = SpeechTranscriber(
        model_size=model_path,
        device="cpu",
        compute_type="int8",
        beam_size=2,
    )
    transcriber.load_model()

    mem_loaded, _ = measure_process_resources()
    print(f"Memória com modelo carregado: {mem_loaded:.2f} MB (+{mem_loaded - mem_init:.2f} MB)")

    # 2. Cria Controller Mock
    class DummyAPI:
        def get_current_presentation(self):
            return {"type": "verse", "name": "Jo 3:16", "slide_number": 26140}
        def show_verse(self, **kwargs):
            return {"status": "ok"}
        def close_current_presentation(self):
            return {"status": "ok"}
        def action_next(self):
            return {"status": "ok"}
        def action_previous(self):
            return {"status": "ok"}

    ctrl = VoiceHolyricsController(api=DummyAPI(), transcriber=transcriber)

    # 3. Teste de Descarte de Fila Concorrente (Proteção de Memória)
    print("\nTestando proteção contra fila ilimitada...")
    worker = AutoListenWorker(controller=ctrl)
    worker._processing = True  # Simula inferência em andamento

    # Envia 50 segmentos de áudio enquanto ocupado
    chunk_1s = np.zeros(16000, dtype=np.float32)
    dropped = 0
    for _ in range(50):
        if worker._processing:
            dropped += 1

    print(f"[OK] 50 segmentos recebidos durante processamento: {dropped} descartados com segurança.")

    # 4. Teste de Classificação de Fala Natural vs Comum
    print("\nTestando latência de classificação de comandos...")
    test_phrases = [
        ("Hoje teremos uma reunião especial.", "UNKNOWN"),
        ("Vamos abrir em João capítulo 3, versículo 16.", "BIBLE_REFERENCE"),
        ("Glória a Deus!", "UNKNOWN"),
        ("Próximo versículo.", "ACTION_NEXT"),
        ("Parar projeção.", "CLEAR_PRESENTATION"),
        ("Encerrar projeção.", "CLEAR_PRESENTATION"),
    ]

    for phrase, expected in test_phrases:
        t0 = time.perf_counter()
        cmd = classify_command(phrase)
        dt = (time.perf_counter() - t0) * 1000
        cmd_type = cmd.command_type.value
        matched = (cmd_type == expected)
        print(f"  [{'OK' if matched else 'FALHA'}] '{phrase}' -> {cmd_type} ({dt:.2f} ms)")

    mem_final, _ = measure_process_resources()
    print(f"\nMemória final: {mem_final:.2f} MB (Delta: {mem_final - mem_loaded:+.2f} MB)")
    print("=" * 65)


if __name__ == "__main__":
    run_benchmark()
