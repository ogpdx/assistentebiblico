"""
Script auxiliar para verificar a integridade da pasta de distribuição (dist/AssistenteBiblico).
Executa testes de fumaça sem GUI antes do teste visual final.
"""

import os
import sys
from pathlib import Path


def verify_distribution(dist_folder: str = "dist/AssistenteBiblico"):
    dist_path = Path(dist_folder)
    print(f"Verificando pasta de distribuição: {dist_path.resolve()}")

    if not dist_path.exists():
        print(f"[FALHA] Pasta de distribuição não encontrada: {dist_path}")
        return False

    exe_file = dist_path / "AssistenteBiblico.exe"
    if not exe_file.exists():
        print(f"[FALHA] Executável principal não encontrado: {exe_file}")
        return False
    print(f"[OK] Executável encontrado: {exe_file} ({exe_file.stat().st_size / (1024*1024):.2f} MB)")

    # Calcula tamanho total da pasta
    total_size = sum(f.stat().st_size for f in dist_path.rglob('*') if f.is_file())
    print(f"[OK] Tamanho total da pasta de distribuição: {total_size / (1024*1024):.2f} MB")

    # Verifica arquivos críticos
    internal_dir = dist_path / "_internal"
    if not internal_dir.exists():
        # Em versões antigas do PyInstaller todos os arquivos ficam na raiz de dist_path
        internal_dir = dist_path

    ct2_found = any(dist_path.rglob("*ctranslate2*"))
    portaudio_found = any(dist_path.rglob("*portaudio*"))
    pyside_found = any(dist_path.rglob("*PySide6*"))

    print(f"[{'OK' if ct2_found else 'ALERTA'}] CTranslate2 nativo presente: {ct2_found}")
    print(f"[{'OK' if portaudio_found else 'ALERTA'}] PortAudio / SoundDevice presente: {portaudio_found}")
    print(f"[{'OK' if pyside_found else 'ALERTA'}] PySide6 runtime presente: {pyside_found}")

    return True


if __name__ == "__main__":
    verify_distribution()
