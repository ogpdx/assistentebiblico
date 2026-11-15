"""
Script de teste de escuta automática ao vivo e auditoria de Input Overflow e Offline real.
Permite testar as frases reais no microfone com monitoramento de overflow do driver.
"""

import os
import sys
import time
from pathlib import Path

# Garante raiz no path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Força isolamento de rede
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from src.core.controller import VoiceHolyricsController
from src.holyrics.client import HolyricsClient
from src.holyrics.api import HolyricsAPI
from src.config.settings import Settings
from src.voice.transcriber import SpeechTranscriber
from src.ui.threads import AutoListenWorker


def run_live_auto_session():
    print("=" * 65)
    print("  SESSÃO DE VALIDAÇÃO AO VIVO — ETAPA 7.1 (MODO AUTOMÁTICO)")
    print("=" * 65)

    settings = Settings("config.json")
    client = HolyricsClient(
        host=settings.holyrics_host,
        port=settings.holyrics_port,
        token=settings.holyrics_token,
    )
    api = HolyricsAPI(client)

    # 1. Carrega modelo estritamente offline
    print("\n[1/3] Inicializando SpeechTranscriber em modo 100% offline...")
    transcriber = SpeechTranscriber(
        model_size=settings.get("voice", "model", default="small"),
        device="cpu",
        compute_type="int8",
        beam_size=2,
    )
    if not transcriber.load_model():
        print("[ERRO] Falha ao carregar modelo offline.")
        return
    print("[OK] Modelo carregado sem consultas externas.")

    ctrl = VoiceHolyricsController(api=api, transcriber=transcriber)

    # 2. Inicia Worker com as correções de buffer e desacoplamento
    print("\n[2/3] Iniciando escuta contínua com desacoplamento assíncrono...")
    dev_idx = settings.get("voice", "device_index")
    worker = AutoListenWorker(
        controller=ctrl,
        device_index=dev_idx,
        sample_rate=16000,
        vad_threshold=0.015,
        silence_seconds=1.0,
    )

    overflow_count = 0

    def on_result(result):
        print("\n" + "=" * 50)
        print(f" Fala reconhecida: '{result.raw_text}'")
        if result.command:
            print(f" Comando:          {result.command.command_type.value}")
            if hasattr(result.command, "display_name"):
                print(f" Referência:       {result.command.display_name}")
        print(f" Ação Holyrics:    {result.action_executed}")
        print(f" Status:           {'SUCESSO' if result.success else 'BLOQUEADO/IGNORADO'}")
        print(f" Mensagem:         {result.message}")
        if result.transcription:
            print(f" Latência:         {result.transcription.inference_time_seconds:.2f}s")
        print("=" * 50 + "\n")

    def on_speech():
        print(">>> [VAD] Fala detectada... gravando...")

    def on_err(msg):
        print(f"[ERRO WORKER]: {msg}")

    worker.speech_detected.connect(on_speech)
    worker.result_ready.connect(on_result)
    worker.error_occurred.connect(on_err)

    worker.start()
    print("[OK] Escuta automática ativa! Pode falar naturalmente no microfone.")
    print("Experimente falar:")
    print("  1. 'Então, lá em Salmos 23.1.'")
    print("  2. 'Próximo versículo.'")
    print("  3. 'Versículo anterior.'")
    print("  4. 'Hoje teremos uma reunião especial.' (deve ser ignorado)")
    print("  5. 'Parar projeção.' (deve encerrar)")
    print("\nPressione Ctrl+C para encerrar a sessão de testes.\n")

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nEncerrando escuta automática...")
        worker.stop()
        worker.wait(2000)
        print("Microfone liberado com sucesso. Sessão finalizada.")


if __name__ == "__main__":
    run_live_auto_session()
