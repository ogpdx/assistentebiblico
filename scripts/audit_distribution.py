"""
Script de auditoria e validação da distribuição empacotada em dist/AssistenteBiblico.
Atualizado para faster-whisper >= 1.0 (CTranslate2):
O vocabulário e tokenizer são compostos por 'tokenizer.json' e/ou 'vocabulary.json'/'vocabulary.txt'.
"""

import os
import sys
import json
from pathlib import Path

def run_distribution_audit(dist_dir: str = "dist/AssistenteBiblico"):
    print("=" * 65)
    print("  AUDITORIA DE DISTRIBUIÇÃO E INTEGRIDADE DO EXECUTÁVEL")
    print("=" * 65)
    
    dist_path = Path(dist_dir).resolve()
    print(f"Diretório auditado: {dist_path}\n")

    if not dist_path.exists():
        print(f"[ERRO CRÍTICO] A pasta {dist_path} não foi encontrada!")
        return False

    exe_path = dist_path / "AssistenteBiblico.exe"
    if not exe_path.exists():
        print(f"[ERRO CRÍTICO] O executável {exe_path} não foi encontrado!")
        return False
    print(f"[OK] Executável presente: {exe_path.name} ({exe_path.stat().st_size / (1024*1024):.2f} MB)")

    # 1. Auditoria do Modelo Whisper SMALL (faster-whisper / CTranslate2)
    print("\n[1/4] Auditoria do Modelo Whisper (Modo Offline):")
    models_dir = dist_path / "models"
    
    model_found = False
    
    if models_dir.exists():
        print(f"  Pasta de modelos encontrada em: {models_dir}")
        bin_files = list(models_dir.rglob("model.bin"))
        if bin_files:
            model_found = True
            for bf in bin_files:
                parent = bf.parent
                print(f"  [OK] Modelo CTranslate2 localizado em: {parent}")
                print(f"       Binário de pesos (model.bin): {bf.stat().st_size / (1024*1024):.2f} MB")
                
                # Checa configuração
                cfg_file = parent / "config.json"
                print(f"       Arquivo de configuração (config.json): {'OK' if cfg_file.exists() else 'FALTA'}")
                
                # No faster-whisper / CTranslate2, o tokenizer é 'tokenizer.json'
                # e o vocabulário pode ser 'vocabulary.json' ou 'vocabulary.txt'
                tok_file = parent / "tokenizer.json"
                voc_txt = parent / "vocabulary.txt"
                voc_json = parent / "vocabulary.json"
                has_vocab = voc_txt.exists() or voc_json.exists()
                
                print(f"       Tokenizador (tokenizer.json): {'OK' if tok_file.exists() else 'FALTA'}")
                vocab_name = "vocabulary.txt" if voc_txt.exists() else ("vocabulary.json" if voc_json.exists() else "Nenhum")
                print(f"       Vocabulário ({vocab_name}): {'OK' if has_vocab else 'FALTA'}")
        else:
            print("  [ALERTA] Nenhum 'model.bin' encontrado dentro de dist/AssistenteBiblico/models.")
    else:
        print("  [ALERTA] Pasta dist/AssistenteBiblico/models NÃO existe.")

    # 2. Auditoria do config.json
    print("\n[2/4] Auditoria de Configuração e Preservação de Token:")
    cfg_dist = dist_path / "config.json"
    if cfg_dist.exists():
        try:
            with open(cfg_dist, "r", encoding="utf-8") as f:
                data = json.load(f)
            hly = data.get("holyrics", {})
            token = hly.get("token", "")
            host = hly.get("host", "")
            port = hly.get("port", "")
            masked_token = f"{token[:3]}***{token[-2:]}" if len(token) > 5 else ("***" if token else "(Vazio)")
            print(f"  [OK] config.json presente na distribuição.")
            print(f"       Host: {host}:{port}")
            print(f"       Token: {masked_token} (Preservado com sucesso)")
        except Exception as e:
            print(f"  [ERRO] Falha ao ler config.json: {e}")
    else:
        print("  [AVISO] config.json não está na pasta dist/AssistenteBiblico.")

    # 3. Auditoria de DLLs e Dependências Nativas
    print("\n[3/4] Auditoria de Dependências Nativas (Sem dependência de Python instalado):")
    ct2_files = list(dist_path.rglob("*ctranslate2*"))
    print(f"  CTranslate2: {'[OK] Presente (' + str(len(ct2_files)) + ' arquivos)' if ct2_files else '[FALTA]'}")
    
    pa_files = list(dist_path.rglob("*portaudio*"))
    print(f"  PortAudio:   {'[OK] Presente (' + str(len(pa_files)) + ' arquivos)' if pa_files else '[FALTA]'}")

    qt_files = list(dist_path.rglob("qwindows.dll"))
    print(f"  Qt Windows:  {'[OK] qwindows.dll presente' if qt_files else '[ALERTA] qwindows.dll não localizado'}")

    # 4. Resumo de Tamanho
    total_size_bytes = sum(f.stat().st_size for f in dist_path.rglob('*') if f.is_file())
    print(f"\n[4/4] Resumo de Tamanho:")
    print(f"  Tamanho total da pasta de distribuição: {total_size_bytes / (1024*1024):.2f} MB")
    print("=" * 65)

if __name__ == "__main__":
    run_distribution_audit()
