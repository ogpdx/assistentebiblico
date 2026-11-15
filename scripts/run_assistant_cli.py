"""
Aplicação de terminal do Assistente Bíblico Integrado com Holyrics (Etapa 4).

Fluxo operacional em culto (Modo Push-to-Talk):
1. Pressione [ENTER] para iniciar a escuta no microfone (VU Meter em tempo real).
2. Fale naturalmente a passagem bíblica ou comando (ex: "João 3:16", "Próximo versículo").
3. Pressione [ENTER] para parar.
4. O sistema transcreve via faster-whisper, valida os limites bíblicos canônicos,
   consulta o Holyrics via API e projeta na TV se for válido.
5. Exibe confirmação visual com o estado real da TV.

Uso:
    python -m scripts.run_assistant_cli
    python -m scripts.run_assistant_cli --model small
"""

import argparse
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import Settings
from src.core.logging_config import setup_logging
from src.core.controller import VoiceHolyricsController, ExecutionResult
from src.holyrics.client import HolyricsClient
from src.holyrics.api import HolyricsAPI
from src.voice.recorder import AudioRecorder, list_audio_devices
from src.voice.transcriber import SpeechTranscriber
from src.voice.audio_utils import render_vu_meter, AudioMetrics

import logging
setup_logging(level=logging.WARNING)


def print_banner(host: str, port: int, model_name: str, device_name: str):
    print("=" * 72)
    print("        ASSISTENTE BÍBLICO — CONTROLE REMOTO POR VOZ (HOLYRICS)")
    print("=" * 72)
    print(f"  Holyrics API Server : http://{host}:{port}")
    print(f"  Modelo Transcrição  : faster-whisper '{model_name.upper()}' (CPU / int8)")
    print(f"  Dispositivo de Áudio: {device_name}")
    print(f"  Modo de Operação    : PUSH-TO-TALK seguro (ENTER para falar)")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="Assistente Bíblico integrado ao Holyrics.")
    parser.add_argument("--model", default="small", choices=["base", "small"], help="Modelo Whisper (padrão: small)")
    parser.add_argument("--device", type=int, default=None, help="Índice do microfone")
    parser.add_argument("--config", default="config.json", help="Arquivo de configuração")
    args = parser.parse_args()

    # 1. Carrega configurações do Holyrics
    settings = Settings(args.config)
    host = settings.holyrics_host
    port = settings.holyrics_port
    token = settings.holyrics_token

    if not token:
        print("\n❌ ERRO: Token do Holyrics não configurado no config.json!")
        print("   Gere um token no Holyrics em: Arquivo > Configurações > API Server > Gerenciar Permissões.")
        sys.exit(1)

    # 2. Conecta à API do Holyrics
    print(f"\n[1/3] Conectando ao Holyrics em {host}:{port}...")
    client = HolyricsClient(host=host, port=port, token=token, timeout=settings.holyrics_timeout)
    api = HolyricsAPI(client)

    status = api.get_status()
    if not status.connected:
        print(f"  ❌ FALHA: Não foi possível conectar ao Holyrics ({status.message}).")
        print("     Verifique se o Holyrics está aberto e o 'API Server - Local' está ativado.")
        sys.exit(1)
    print(f"  ✅ Conectado com sucesso ao Holyrics!")

    # 3. Dispositivos de microfone
    devices = list_audio_devices()
    if not devices:
        print("  ❌ Nenhum microfone detectado no sistema!")
        sys.exit(1)

    selected_dev = None
    for d in devices:
        if (args.device == d["index"]) or (args.device is None and d["is_default"]):
            selected_dev = d
            break
    dev_name = selected_dev["name"] if selected_dev else "Microfone Padrão"

    # 4. Carrega modelo Whisper
    print(f"\n[2/3] Carregando modelo faster-whisper '{args.model}' (int8)...")
    t0 = time.perf_counter()
    transcriber = SpeechTranscriber(
        model_size=args.model,
        device="cpu",
        compute_type="int8",
        beam_size=2,
    )
    if not transcriber.load_model():
        print("  ❌ Erro ao inicializar o modelo de transcrição.")
        sys.exit(1)
    print(f"  ✅ Modelo pronto em {time.perf_counter() - t0:.2f}s!")

    # 5. Inicializa o controlador central
    print("\n[3/3] Inicializando controlador de orquestração...")
    controller = VoiceHolyricsController(
        api=api,
        transcriber=transcriber,
        duplicate_threshold_seconds=2.0,
    )
    recorder = AudioRecorder(device_index=args.device, mode="push_to_talk")

    def on_level(m: AudioMetrics):
        bar = render_vu_meter(m.rms, m.peak, width=20)
        sys.stdout.write(f"\r  🎙️  Gravando... {bar}   ")
        sys.stdout.flush()

    recorder.on_level_meter = on_level

    print_banner(host, port, args.model, dev_name)
    print("\nInstruções de Uso:")
    print("  • Pressione [ENTER] para COMEÇAR a falar.")
    print("  • Fale a passagem (ex: 'João três dezesseis' ou 'Próximo versículo').")
    print("  • Pressione [ENTER] para PARAR e projetar na TV.")
    print("  • Digite 'sair' para encerrar o assistente.\n")

    # Loop de escuta Push-to-Talk
    while True:
        try:
            prompt_input = input("👉 Pressione [ENTER] para falar (ou 'sair'): ").strip()
            if prompt_input.lower() in ("sair", "exit", "quit"):
                break

            print("-" * 72)
            recorder.start_recording()

            input()  # Aguarda o segundo enter do operador

            audio = recorder.stop_recording()
            sys.stdout.write("\n")
            sys.stdout.flush()

            if audio is None or len(audio) < 1600:
                print("  ⚠️ Áudio muito curto ou vazio. Pressione ENTER e fale enquanto o microfone grava.\n")
                continue

            print("⏳ [PROCESSANDO] Transcrevendo voz e consultando Holyrics...")
            t_start = time.perf_counter()
            exec_res: ExecutionResult = controller.process_audio(audio)
            t_total = time.perf_counter() - t_start

            print("\n  RELATÓRIO DE EXECUÇÃO:")
            print(f"  • Texto Reconhecido : \"{exec_res.raw_text}\"")
            print(f"  • Comando / Tipo    : {exec_res.command.command_type.value}")
            print(f"  • Ação no Holyrics  : {exec_res.action_executed}")
            print(f"  • Tempo Total       : {t_total:.2f}s")

            if exec_res.success:
                print(f"  ✅ STATUS: {exec_res.message}")
                if exec_res.current_presentation:
                    active_name = exec_res.current_presentation.get("name", "Bíblia")
                    slide_num = exec_res.current_presentation.get("slide_number", "")
                    print(f"  📺 NA TELA DA TV    : {active_name} (Slide {slide_num})")
            else:
                print(f"  ⚠️  BLOQUEADO: {exec_res.message}")

            print("-" * 72 + "\n")

        except (KeyboardInterrupt, EOFError):
            break

    print("\nAssistente Bíblico encerrado com segurança.")
    client.close()


if __name__ == "__main__":
    main()
