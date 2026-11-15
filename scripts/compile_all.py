"""
Script completo de compilação em 1 clique:
1. Atualiza o executável PyInstaller com as alterações recentes (campo de token na UI).
2. Sincroniza o modelo SMALL e config.example.json para dist/AssistenteBiblico.
3. Compila o instalador final Inno Setup.
"""

import sys
import subprocess
from pathlib import Path

# Adiciona raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.sync_model_to_dist import sync_small_model
from scripts.build_installer import build_installer

def full_build():
    print("=" * 65)
    print("  COMPILAÇÃO COMPLETA: PYINSTALLER + INNO SETUP")
    print("=" * 65)

    # 1. Compila o PyInstaller
    print("\n[Passo 1/3] Atualizando executável com PyInstaller...")
    res = subprocess.run(["python", "-m", "PyInstaller", "--noconfirm", "assistente_biblico.spec"])
    if res.returncode != 0:
        print("[ERRO] Falha ao compilar com o PyInstaller.")
        return False

    # 2. Sincroniza modelo SMALL e config.example.json
    print("\n[Passo 2/3] Sincronizando modelo SMALL e recursos...")
    sync_small_model()

    # 3. Compila o Instalador Inno Setup
    print("\n[Passo 3/3] Compilando instalador Inno Setup...")
    success = build_installer()
    return success

if __name__ == "__main__":
    full_build()
