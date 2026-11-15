"""
Utilitário de resolução de caminhos robusto e especializado para Windows e PyInstaller.

Diferencia com rigor:
1. get_app_dir(): Diretório onde o executável (.exe) ou o script inicial está localizado.
2. get_bundle_dir(): Diretório interno do PyInstaller (sys._MEIPASS) onde estão os recursos embutidos.
3. get_user_config_dir(): %APPDATA%/AssistenteBiblico/ para configurações persistentes do usuário.
4. get_user_logs_dir(): %LOCALAPPDATA%/AssistenteBiblico/logs/ para arquivos de log rotativos.
5. get_models_dir(): Procura primeiro em <app_dir>/models/ (modo portátil offline) e depois em %LOCALAPPDATA%/AssistenteBiblico/models/.
"""

import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    """Retorna True se o aplicativo estiver rodando empacotado pelo PyInstaller."""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


def get_app_dir() -> Path:
    """Retorna o diretório base do aplicativo.
    
    - No PyInstaller (congelado): Diretório onde reside o executável (.exe).
    - No ambiente Python normal: Diretório raiz do projeto (onde está main.py).
    """
    if is_frozen():
        return Path(sys.executable).resolve().parent
    else:
        # main.py está na raiz, path_utils está em src/core/
        return Path(__file__).resolve().parent.parent.parent


def get_bundle_dir() -> Path:
    """Retorna o diretório de recursos internos do PyInstaller.
    
    - No PyInstaller (congelado): sys._MEIPASS (ou _internal no modo onedir).
    - No ambiente Python normal: Diretório raiz do projeto.
    """
    if is_frozen():
        return Path(sys._MEIPASS).resolve()
    else:
        return get_app_dir()


def get_user_config_dir() -> Path:
    """Retorna o diretório de configurações do usuário (%APPDATA%/AssistenteBiblico/).
    
    Garante permissão de escrita mesmo quando o executável está instalado
    em Program Files ou pastas de somente leitura.
    """
    appdata = os.getenv("APPDATA")
    if appdata:
        path = Path(appdata) / "AssistenteBiblico"
    else:
        path = get_app_dir() / "config"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_user_logs_dir() -> Path:
    """Retorna o diretório de logs do usuário (%LOCALAPPDATA%/AssistenteBiblico/logs/)."""
    localappdata = os.getenv("LOCALAPPDATA")
    if localappdata:
        path = Path(localappdata) / "AssistenteBiblico" / "logs"
    else:
        path = get_app_dir() / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_models_dir() -> Path:
    """Retorna o diretório onde os modelos do Whisper devem residir.
    
    Prioridade:
    1. Subpasta 'models' na mesma pasta do executável (portátil / offline nativo).
    2. Subpasta 'models' no diretório do projeto.
    3. %LOCALAPPDATA%/AssistenteBiblico/models/ (persistência padrão de usuário no Windows).
    """
    # 1. Checa pasta models ao lado do app / exe
    local_models = get_app_dir() / "models"
    if local_models.exists() and any(local_models.iterdir()):
        return local_models

    # 2. Caminho persistente no perfil do usuário
    localappdata = os.getenv("LOCALAPPDATA")
    if localappdata:
        path = Path(localappdata) / "AssistenteBiblico" / "models"
    else:
        path = local_models

    path.mkdir(parents=True, exist_ok=True)
    return path
