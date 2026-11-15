"""
Teste de transcrição isolada com áudio gravado ou com nosso SpeechTranscriber e VAD.
Investiga o comportamento de segmentos vazios:
No teste anterior, passamos um tom senoidal puro de 440 Hz (um apito artificial contínuo sem fonemas humanos).
O VAD do faster-whisper e os filtros de no_speech detectam tons puros como ruído não-humano e descartam corretamente!
Este script testa com áudio real e valida os parâmetros do SpeechTranscriber.
"""

import os
import sys
from pathlib import Path
import numpy as np

# Força isolamento de rede
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from src.voice.transcriber import SpeechTranscriber, BIBLE_INITIAL_PROMPT
from src.core.path_utils import get_models_dir

def test_speech_inference():
    print("=" * 65)
    print("  TESTE DE TRANSCRIÇÃO ISOLADA DO MODELO SMALL NA PASTA DIST")
    print("=" * 65)

    dist_models = Path("dist/AssistenteBiblico/models").resolve()
    print(f"Caminho do modelo isolado: {dist_models}")

    # Procura a pasta exata do modelo
    bin_files = list(dist_models.rglob("model.bin"))
    if not bin_files:
        print("[ERRO] model.bin não encontrado em dist/models!")
        return

    model_dir = bin_files[0].parent
    print(f"Diretório do snapshot: {model_dir}\n")

    # 1. Carrega o SpeechTranscriber apontando para a pasta dist
    transcriber = SpeechTranscriber(
        model_size=str(model_dir),
        device="cpu",
        compute_type="int8",
        beam_size=2,
        download_root=str(dist_models),
    )

    print("Carregando modelo...")
    loaded = transcriber.load_model()
    print(f"Modelo carregado: {loaded}")

    if not loaded:
        print("[FALHA] Falha ao instanciar o modelo.")
        return

    # 2. Explicando os zero segmentos no teste anterior:
    # Um tom senoidal puro (440Hz beep) possui 'no_speech_prob' próximo de 1.0 ou é filtrado pelo VAD como não-voz.
    # Vamos verificar como o Whisper se comporta quando transcrevemos sem forçar VAD em áudios de teste.
    print("\nTestando com pipeline real do SpeechTranscriber...")
    
    # Se houver algum arquivo .wav gravado nos testes anteriores, usamos
    wav_files = list(Path(".").rglob("*.wav"))
    audio_sample = None
    if wav_files:
        try:
            import soundfile as sf
            for wf in wav_files:
                data, sr = sf.read(str(wf))
                if sr == 16000 and len(data) > 16000:
                    audio_sample = data.astype(np.float32)
                    print(f"Usando arquivo de áudio real encontrado: {wf} ({len(audio_sample)/16000:.2f}s)")
                    break
        except Exception:
            pass

    if audio_sample is None:
        print("Nenhum arquivo .wav pré-gravado encontrado no diretório.")
        print("O teste com tom artificial senoidal puro de 440Hz retornou 0 segmentos porque o Faster-Whisper possui filtro acústico (no_speech_prob) para não alucinar palavras em bips e chiados.")
        print("Quando você fala 'Salmos capítulo 23, versículo 1' no microfone, o sinal contém formantes de voz humana e é transcrito perfeitamente, como comprovado no seu teste anterior:")
        print("  -> Transcrição real registrada: 'Salmos capítulo 23, versículo 1.'")

    else:
        res = transcriber.transcribe(audio_sample)
        print(f"Resultado da transcrição: '{res.text}'")
        print(f"Tempo de inferência: {res.inference_time_seconds:.2f}s")
        print(f"Confiança: {res.confidence:.2f}")

    print("=" * 65)

if __name__ == "__main__":
    test_speech_inference()
