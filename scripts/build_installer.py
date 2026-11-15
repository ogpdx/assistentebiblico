"""
Script em Python para localizar o ISCC.exe e compilar o script Inno Setup.
Evita problemas de sintaxe de batch (.bat) no Windows.
"""

import os
import sys
import subprocess
from pathlib import Path

# Adiciona a raiz do projeto no sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def build_installer():
    print("=" * 65)
    print("  COMPILAÇÃO DO INSTALADOR INNO SETUP (PYTHON BUILDER)")
    print("=" * 65)

    # 1. Procura ISCC.exe
    possible_paths = [
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    ]

    # Também checa no PATH do sistema
    import shutil
    path_iscc = shutil.which("ISCC.exe") or shutil.which("iscc")
    if path_iscc:
        possible_paths.insert(0, Path(path_iscc))

    iscc_exe = None
    for p in possible_paths:
        if p and p.exists():
            iscc_exe = p
            break

    if not iscc_exe:
        print("\n[AVISO CRÍTICO]: O compilador do Inno Setup 6 (ISCC.exe) não foi detectado no sistema.")
        print("Para compilar o instalador Windows (.exe), você precisará instalar o Inno Setup 6:")
        print("  Download oficial gratuito: https://jrsoftware.org/isdl.php")
        print("\nApós instalar o Inno Setup, rode este comando novamente:")
        print("  python scripts/build_installer.py")
        return False

    print(f"\n[OK] Compilador Inno Setup encontrado em:\n     {iscc_exe}")

    # Garante sincronização do modelo SMALL limpo na pasta dist antes de compilar
    from scripts.sync_model_to_dist import sync_small_model
    sync_small_model()

    iss_script = Path("scripts/installer/AssistenteBiblico.iss").resolve()
    if not iss_script.exists():
        print(f"[ERRO] Arquivo de script não encontrado: {iss_script}")
        return False

    out_dir = Path("dist/installer").resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nCompilando script: {iss_script}...")
    cmd = [str(iscc_exe), str(iss_script)]

    try:
        res = subprocess.run(cmd, check=True)
        print("\n" + "=" * 65)
        print("  INSTALADOR GERADO COM SUCESSO!")
        print(f"  Pasta de saída: {out_dir}")
        for item in out_dir.glob("*.exe"):
            print(f"  -> {item.name} ({item.stat().st_size / (1024*1024):.2f} MB)")
        print("=" * 65)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n[ERRO] Falha ao compilar com o Inno Setup (código {e.returncode})")
        return False

if __name__ == "__main__":
    build_installer()
