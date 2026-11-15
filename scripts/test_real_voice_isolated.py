"""
Script para gravar um pequeno áudio real de 3 segundos com fala do usuário
e imediatamente testar a transcrição isolada com o modelo da pasta dist/.
"""

import os
import sys
import time
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from src.voice.recorder import AudioRecorder
from src.voice.transcriber import SpeechTranscriber
from src.interpreter import classify_command

def test_real_voice_isolated():
    print("=" * 65)
    print("  TESTE DE FALA REAL ISOLADA COM O MODELO DA PASTA DIST")
    print("=" * 65)

    dist_models = Path("dist/AssistenteBiblico/models").resolve()
    bin_files = list(dist_models.rglob("model.bin"))
    if not bin_files:
        print("[ERRO] model.bin não encontrado em dist/models!")
        return

    model_dir = bin_files[0].parent

    print(f"1. Carregando modelo Whisper da pasta de distribuição: {model_dir.name}")
    transcriber = SpeechTranscriber(
        model_size=str(model_dir),
        device="cpu",
        compute_type="int8",
        beam_size=2,
    )
    if not transcriber.load_model():
        print("[FALHA] Não foi possível carregar o modelo.")
        return
    print("[OK] Modelo carregado em memória com sucesso.\n")

    print("2. Teste de gravação de voz:")
    print("   Prepare-se para falar uma referência bíblica (ex: 'João 3:16' ou 'Salmos 23:1')")
    print("   Iniciando gravação de 4 segundos em 2 segundos...")
    time.sleep(2)

    recorder = AudioRecorder(sample_rate=16000, mode="manual")
    recorder.start_recording()
    print(">>> GRAVANDO AGORA... FALE SUA REFERÊNCIA BÍBLICA! <<<")
    time.sleep(4.0)
    audio = recorder.stop_recording()
    print(">>> GRAVAÇÃO FINALIZADA! <<<\n")

    if audio is None or len(audio) < 1600:
        print("[ERRO] Áudio capturado vazio ou muito curto.")
        return

    print("3. Executando transcrição offline com o modelo isolado da distribuição...")
    res = transcriber.transcribe(audio)

    print(f"\n" + "-" * 50)
    print(f"  TEXTO RECONHECIDO: '{res.text}'")
    print(f"  TEMPO DE INFERÊNCIA: {res.inference_time_seconds:.2f}s")
    print(f"  PROBABILIDADE DE NÃO-VOZ: {res.no_speech_prob:.4f}")
    print(f"-" * 50)

    # 4. Envia ao interpretador
    cmd = classify_command(res.text)
    print(f"  TIPO DE COMANDO: {cmd.command_type.value}")
    if hasattr(cmd, "holyrics_reference"):
        print(f"  REFERÊNCIA HOLYRICS: {cmd.holyrics_reference}")
        print(f"  NOME AMIGÁVEL:       {cmd.display_name}")

    print("=" * 65)

if __name__ == "__main__":
    test_real_voice_isolated()
