"""
Ponto de entrada principal do Assistente Bíblico.
Inicia o aplicativo desktop PySide6.
"""

import sys
import os
import logging
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from src.core.logging_config import setup_logging, get_logger
from src.config.settings import Settings
from src.ui.main_window import MainWindow

logger = get_logger("main")


def main():
    # Inicializa o logging
    setup_logging(level=logging.INFO)
    logger.info("Iniciando o Assistente Bíblico...")

    app = QApplication(sys.argv)
    app.setApplicationName("Assistente Bíblico")
    app.setOrganizationName("AssistenteBíblico")

    # Carrega configurações
    config_path = "config.json"
    if not os.path.exists(config_path):
        logger.warning("config.json não encontrado na raiz, usando configurações padrão.")
    settings = Settings(config_path)

    # Cria e exibe a janela principal
    window = MainWindow(settings=settings)
    window.show()

    # Executa o loop de eventos
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
