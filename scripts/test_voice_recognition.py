"""
Painel aprimorado de diagnóstico e testes ao vivo de captura de áudio,
reconhecimento de voz (faster-whisper) e interpretação bíblica.

Novidades da auditoria:
- Medidor visual de volume (VU Meter em tempo real) com barra ASCII, RMS e Pico.
- Detecção imediata de microfone mudo / silêncio ou clipping / saturação.
- Normalização de ganho automático pré-inferência.
- Separação transparente das etapas: [CAPTURA] -> [TRANSCRIÇÃO] -> [INTERPRETAÇÃO].
- Suporte para alternar entre modelos 'base' e 'small' e testar 'beam_size'.

Uso:
    python -m scripts.test_voice_recognition
    python -m scripts.test_voice_recognition --model small
    python -m scripts.test_voice_recognition --model small --beam 2
"""

import argparse
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.logging_config import setup_logging
from src.voice.recorder import AudioRecorder, list_audio_devices
from src.voice.transcriber import SpeechTranscriber
from src.voice.audio_utils import render_vu_meter, AudioMetrics
from src.interpreter import (
    classify_command,
    CommandType,
    BibleReferenceCommand,
    NavigationCommand,
    UnknownCommand,
)

import logging
setup_logging(level=logging.WARNING)


def print_banner(model_name: str, beam_size: int, device_name: str):
    print("=" * 72)
    print("    ASSISTENTE BÍBLICO — AUDITORIA DE VOZ E DIAGNÓSTICO ACÚSTICO")
    print("=" * 72)
    print(f"  Microfone Ativo : {device_name}")
    print(f"  Modelo Whisper  : {model_name.upper()} (CPU, int8, beam_size={beam_size})")
    print(f"  Modo de Captura : PUSH-TO-TALK (Pressione ENTER para falar)")
    print("=" * 72)


def main():
    parser = argparse.ArgumentParser(description="Auditoria de reconhecimento de voz do Assistente Bíblico.")
    parser.add_argument("--model", default="base", choices=["base", "small"], help="Modelo Whisper (padrão: base)")
    parser.add_argument("--beam", type=int, default=2, help="Beam size para decodificação (padrão: 2)")
    parser.add_argument("--device", type=int, default=None, help="Índice do microfone (opcional)")
    args = parser.parse_args()

    print("\n[1/3] Verificando microfones do sistema...")
    devices = list_audio_devices()
    if not devices:
        print("  ❌ Nenhum microfone encontrado ou sounddevice não instalado!")
        sys.exit(1)

    selected_dev = None
    for d in devices:
        is_sel = (args.device == d["index"]) or (args.device is None and d["is_default"])
        if is_sel:
            selected_dev = d
        prefix = "👉" if is_sel else "  "
        print(f"  {prefix} [{d['index']}] {d['name']} ({'Padrão' if d['is_default'] else 'Secundário'})")

    dev_name = selected_dev["name"] if selected_dev else "Microfone Padrão"

    print(f"\n[2/3] Carregando modelo faster-whisper '{args.model}' (int8, beam={args.beam})...")
    transcriber = SpeechTranscriber(
        model_size=args.model,
        device="cpu",
        compute_type="int8",
        beam_size=args.beam,
    )
    t0 = time.perf_counter()
    if not transcriber.load_model():
        print("  ❌ Erro ao carregar o modelo. Verifique a instalação do faster-whisper.")
        sys.exit(1)
    print(f"  ✅ Modelo pronto em {time.perf_counter() - t0:.2f}s!")

    recorder = AudioRecorder(device_index=args.device, mode="push_to_talk")

    # Callback para atualizar VU Meter na tela durante a fala
    def on_level(metrics: AudioMetrics):
        bar = render_vu_meter(metrics.rms, metrics.peak, width=22)
        # Imprime na mesma linha usando retorno de carro
        sys.stdout.write(f"\r  🎙️  Gravando... {bar}   ")
        sys.stdout.flush()

    recorder.on_level_meter = on_level

    print_banner(args.model, args.beam, dev_name)
    print("\nInstruções de Teste:")
    print("  1. Pressione [ENTER] para INICIAR a captura.")
    print("  2. Observe a barra de volume se mover enquanto você fala.")
    print("  3. Fale a referência (ex: 'Salmos vinte e três' ou 'Gênesis um versículo um').")
    print("  4. Pressione [ENTER] novamente para FINALIZAR e processar.")
    print("  5. Digite 'sair' para encerrar.\n")

    while True:
        try:
            cmd_in = input("\n👉 Pressione [ENTER] para falar (ou 'sair'): ").strip()
            if cmd_in.lower() in ("sair", "exit", "quit"):
                break

            print("\n" + "-" * 72)
            recorder.start_recording()

            input()  # Aguarda o segundo enter do usuário

            audio = recorder.stop_recording()
            sys.stdout.write("\n")
            sys.stdout.flush()

            metrics = recorder.last_metrics
            print("⏳ [PROCESSANDO] Analisando áudio com faster-whisper...")

            # --- ETAPA 1: DIAGNÓSTICO DA CAPTURA DE ÁUDIO ---
            print("\n  [FASE 1: CAPTURA DE ÁUDIO]")
            if metrics is None or audio is None or len(audio) < 1600:
                print("  ❌ ALERTA: Áudio vazio ou gravação excessivamente curta (< 100ms).")
                print("     Verifique se o microfone está conectado e se houve fala.")
                continue

            print(f"  • Duração Total   : {metrics.duration_seconds:.2f}s ({len(audio)} amostras)")
            print(f"  • RMS Médio       : {metrics.rms:.4f} ({metrics.dbfs:.1f} dBFS)")
            print(f"  • Pico Máximo     : {metrics.peak:.4f}")

            if metrics.is_silent:
                print("  ⚠️  ALERTA CRÍTICO: Áudio quase inaudível ou silencioso!")
                print("      O microfone pode estar mudo no Windows ou com ganho muito baixo.")
            elif metrics.is_clipping:
                print("  ⚠️  ALERTA: Sinal saturado (clipping). Reduza o volume do microfone.")
            else:
                print("  • Qualidade Sinal : Nível adequado para transcrição.")

            # --- ETAPA 2: TRANSCRIÇÃO FASTER-WHISPER ---
            t_infer_start = time.perf_counter()
            result = transcriber.transcribe(audio, apply_normalization=True)
            t_infer = time.perf_counter() - t_infer_start

            print("\n  [FASE 2: TRANSCRIÇÃO FASTER-WHISPER]")
            print(f"  • Texto Bruto     : \"{result.text}\"")
            print(f"  • Tempo Inferência: {t_infer:.2f}s (Latência real)")
            print(f"  • Score Confiança : {result.confidence * 100:.1f}%")
            if result.is_uncertain:
                print("  ⚠️  ALERTA: Whisper indicou incerteza acústica / baixa confiança.")

            # --- ETAPA 3: INTERPRETAÇÃO E SEGURANÇA ---
            print("\n  [FASE 3: INTERPRETAÇÃO BÍBLICA / COMANDOS]")
            interpreted = classify_command(result.text)
            print(f"  • Classificação   : {interpreted.command_type.value}")

            if isinstance(interpreted, BibleReferenceCommand):
                print(f"  • Livro Identificado: {interpreted.book_name} (Abrev: '{interpreted.book_abbreviation}')")
                print(f"  • Capítulo / Vers.  : Cap {interpreted.chapter}" + (f", Versículo {interpreted.verse_start}" if interpreted.verse_start else ""))
                print(f"  • Payload Holyrics  : ShowVerse(reference='{interpreted.holyrics_reference}')")
                print(f"  • Exibição Interface: \"{interpreted.display_name}\"")
                print("  ✅ SUCESSO: Referência bíblica válida e pronta para envio!")
            elif isinstance(interpreted, NavigationCommand):
                print(f"  • Ação Mapeada    : Holyrics.{interpreted.command_type.value}")
                print("  ✅ SUCESSO: Comando de navegação explícito aprovado!")
            elif isinstance(interpreted, UnknownCommand):
                print(f"  • Status Segurança : REJEITADO (Não enviado à TV)")
                print(f"  • Motivo Recusa    : {interpreted.reason}")

            print("-" * 72)

        except (KeyboardInterrupt, EOFError):
            break

    print("\nAuditoria de voz encerrada com sucesso.")


if __name__ == "__main__":
    main()
