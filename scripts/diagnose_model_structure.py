"""
Script de diagnóstico minucioso da estrutura do modelo em dist/AssistenteBiblico/models.
Investiga:
1. Arquivos reais existentes no snapshot do modelo na distribuição.
2. Arquivos reais no cache original do usuário (~/.cache/huggingface/hub/...).
3. Quais arquivos o faster-whisper e o CTranslate2 realmente exigem (tokenizer.json vs vocabulary.json).
4. Teste real de instanciar WhisperModel apontando EXCLUSIVAMENTE para a pasta dist, sem rede.
5. Transcrição de áudio sintético/real isolado.
"""

import os
import sys
from pathlib import Path

def inspect_models():
    print("=" * 70)
    print("  INVESTIGAÇÃO DA ESTRUTURA DO MODELO FASTER-WHISPER")
    print("=" * 70)

    dist_models = Path("dist/AssistenteBiblico/models").resolve()
    print(f"\n1. Arquivos encontrados em: {dist_models}")
    if dist_models.exists():
        for root, dirs, files in os.walk(dist_models):
            rel = Path(root).relative_to(dist_models)
            print(f"  Pasta: {rel}")
            for f in files:
                f_path = Path(root) / f
                size_kb = f_path.stat().st_size / 1024
                print(f"    - {f} ({size_kb:.2f} KB)")
    else:
        print("  Pasta não existe!")

    # 2. Inspecionar cache original do huggingface
    hf_cache = Path.home() / ".cache" / "huggingface" / "hub"
    print(f"\n2. Inspecionando cache do Hugging Face em: {hf_cache}")
    if hf_cache.exists():
        small_folders = list(hf_cache.glob("*whisper-small*"))
        for sf in small_folders:
            print(f"  Repositório encontrado: {sf.name}")
            snapshots = list((sf / "snapshots").glob("*"))
            for snap in snapshots:
                print(f"    Snapshot: {snap.name}")
                for item in snap.iterdir():
                    print(f"      * {item.name} ({item.stat().st_size / 1024:.2f} KB)")

    # 3. Teste de isolamento com faster-whisper
    print("\n3. Teste de carregamento isolado do WhisperModel:")
    try:
        import faster_whisper
        import ctranslate2
        print(f"  faster-whisper versão: {faster_whisper.__version__}")
        print(f"  ctranslate2 versão:    {ctranslate2.__version__}")
    except Exception as e:
        print(f"  Erro ao importar: {e}")
        return

    # Procura onde está o model.bin em dist_models
    bin_files = list(dist_models.rglob("model.bin"))
    if not bin_files:
        print("  [ERRO] model.bin não encontrado em dist/models!")
        return

    model_dir = bin_files[0].parent
    print(f"\n4. Testando WhisperModel apontando DIRETAMENTE para a pasta:")
    print(f"   model_dir = {model_dir}")

    # Desativa qualquer conexão ou download forçando HF_HUB_OFFLINE
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"

    try:
        # Quando passamos o diretório direto contendo model.bin, o faster-whisper trata como modelo CTranslate2 local
        model = faster_whisper.WhisperModel(
            str(model_dir),
            device="cpu",
            compute_type="int8",
            cpu_threads=4,
            local_files_only=True
        )
        print("  [SUCESSO] WhisperModel carregado perfeitamente em modo 100% OFFLINE!")

        # 5. Teste de transcrição real de áudio sintético
        import numpy as np
        # 2 segundos de tom senoidal simulando silêncio/áudio
        sr = 16000
        t = np.linspace(0, 2, sr * 2, endpoint=False, dtype=np.float32)
        test_audio = 0.05 * np.sin(2 * np.pi * 440 * t)

        segments, info = model.transcribe(test_audio, language="pt", beam_size=1)
        seg_list = list(segments)
        print(f"  [SUCESSO] Transcrição isolada executada com sucesso!")
        print(f"  Idioma detectado: {info.language} (prob={info.language_probability:.2f})")
        print(f"  Segmentos retornados: {len(seg_list)}")

    except Exception as e:
        print(f"  [FALHA] Erro durante o carregamento/transcrição: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    inspect_models()
