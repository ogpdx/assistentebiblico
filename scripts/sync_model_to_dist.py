"""
Copia os arquivos do modelo Whisper SMALL oficial para a pasta dist/AssistenteBiblico/models.
Inclui apenas o snapshot do SMALL para não inflar o instalador desnecessariamente.
"""

import shutil
from pathlib import Path

def sync_small_model():
    src_snapshot = Path(r"models\models--Systran--faster-whisper-small\snapshots\536b0662742c02347bc0e980a01041f333bce120")
    dest_dir = Path(r"dist\AssistenteBiblico\models\small")
    dest_dir.mkdir(parents=True, exist_ok=True)

    print(f"Copiando modelo SMALL de:\n  {src_snapshot.resolve()}\npara:\n  {dest_dir.resolve()}\n")

    files_to_copy = ["model.bin", "config.json", "tokenizer.json", "vocabulary.txt"]
    for f in files_to_copy:
        src_file = src_snapshot / f
        dest_file = dest_dir / f
        if src_file.exists():
            print(f"  Copiando {f} ({src_file.stat().st_size / (1024*1024):.2f} MB)...")
            shutil.copy2(src_file, dest_file)
        else:
            print(f"  [ALERTA] Arquivo não encontrado: {src_file}")

    print("\nModelo SMALL sincronizado com sucesso em dist/AssistenteBiblico/models/small!")

    # Copia também config.example.json para a pasta dist se ainda não existir
    example_src = Path("config.example.json")
    example_dest = Path(r"dist\AssistenteBiblico\config.example.json")
    if example_src.exists():
        shutil.copy2(example_src, example_dest)
        print("config.example.json copiado para dist/AssistenteBiblico!")

if __name__ == "__main__":
    sync_small_model()
