import os
from pathlib import Path

def list_files(p):
    path = Path(p)
    if not path.exists():
        print(f"Path does not exist: {path}")
        return
    for item in path.rglob("*"):
        if item.is_file():
            print(f"{item.relative_to(path)} ({item.stat().st_size / (1024*1024):.2f} MB)")

print("--- dist/AssistenteBiblico/models ---")
list_files("dist/AssistenteBiblico/models")

print("\n--- models (raiz) ---")
list_files("models")

hf_hub = Path.home() / ".cache" / "huggingface" / "hub"
print(f"\n--- huggingface hub: {hf_hub} ---")
if hf_hub.exists():
    for f in hf_hub.glob("*whisper*"):
        print(f)
