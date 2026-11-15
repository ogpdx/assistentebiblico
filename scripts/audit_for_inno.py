"""
Script de auditoria completa da distribuição dist/AssistenteBiblico para preparação do instalador Inno Setup.
"""

import os
import sys
from pathlib import Path

def audit_dist():
    print("=" * 70)
    print("  AUDITORIA DE DISTRIBUIÇÃO PARA INNO SETUP (ETAPA 8)")
    print("=" * 70)

    dist_dir = Path("dist/AssistenteBiblico").resolve()
    print(f"Diretório dist: {dist_dir}\n")

    if not dist_dir.exists():
        print(f"[ERRO] Pasta {dist_dir} não existe!")
        return

    # 1. Executável principal
    exe = dist_dir / "AssistenteBiblico.exe"
    print(f"Executável: {'[OK]' if exe.exists() else '[FALTA]'} {exe.name} ({exe.stat().st_size / (1024*1024):.2f} MB)")

    # 2. Pasta models
    models_dir = dist_dir / "models"
    print(f"\nPasta models: {'[OK]' if models_dir.exists() else '[FALTA]'}")
    if models_dir.exists():
        for f in models_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(models_dir)
                print(f"  - models/{rel} ({f.stat().st_size / (1024*1024):.2f} MB)")

    # 3. Dependências nativas críticas
    print("\nDependências nativas:")
    ct2 = list(dist_dir.rglob("*ctranslate2*"))
    print(f"  CTranslate2: {'[OK]' if ct2 else '[FALTA]'} ({len(ct2)} arquivos)")

    pa = list(dist_dir.rglob("*portaudio*"))
    print(f"  PortAudio:   {'[OK]' if pa else '[FALTA]'} ({len(pa)} arquivos)")

    qw = list(dist_dir.rglob("qwindows.dll"))
    print(f"  qwindows.dll:{'[OK]' if qw else '[FALTA]'}")

    # 4. Inno Setup Compiler
    print("\nVerificação do Inno Setup:")
    inno_paths = [
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Users\pedro\AppData\Local\Programs\Inno Setup 6\ISCC.exe"),
    ]
    iscc_found = None
    for p in inno_paths:
        if p.exists():
            iscc_found = p
            break

    if iscc_found:
        print(f"  [OK] Compilador Inno Setup encontrado em: {iscc_found}")
    else:
        print("  [AVISO] ISCC.exe não encontrado nos caminhos padrão (Program Files / AppData).")

    # 5. Tamanho total
    total_size = sum(f.stat().st_size for f in dist_dir.rglob('*') if f.is_file())
    print(f"\nTamanho total de dist/AssistenteBiblico: {total_size / (1024*1024):.2f} MB")
    print("=" * 70)

if __name__ == "__main__":
    audit_dist()
