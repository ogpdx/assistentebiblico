"""
Widget de Status Badge com indicador luminoso (LED) e texto de estado.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel


class StatusBadge(QWidget):
    """Cápsula elegante de status para o cabeçalho e estado do sistema."""

    STATES = {
        "idle": {
            "text": "Aguardando",
            "dot_color": "#9ca3af",
            "bg_color": "#181a20",
            "border_color": "#2d313d",
            "text_color": "#9ca3af",
        },
        "listening": {
            "text": "Ouvindo...",
            "dot_color": "#ef4444",
            "bg_color": "#2a1215",
            "border_color": "#dc2626",
            "text_color": "#fca5a5",
        },
        "processing": {
            "text": "Processando...",
            "dot_color": "#f59e0b",
            "bg_color": "#261a06",
            "border_color": "#d97706",
            "text_color": "#fde68a",
        },
        "success": {
            "text": "Projetado na TV",
            "dot_color": "#10b981",
            "bg_color": "#06281e",
            "border_color": "#059669",
            "text_color": "#6ee7b7",
        },
        "error": {
            "text": "Não Reconhecido",
            "dot_color": "#ef4444",
            "bg_color": "#2a1215",
            "border_color": "#ef4444",
            "text_color": "#fca5a5",
        },
    }

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(10, 4, 10, 4)
        self._layout.setSpacing(6)

        self._dot = QLabel("●", self)
        self._dot.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._label = QLabel("Aguardando", self)
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._layout.addWidget(self._dot)
        self._layout.addWidget(self._label)

        self.set_state("idle")

    def set_state(self, state_key: str, custom_text: str | None = None):
        """Define o estado visual do badge."""
        cfg = self.STATES.get(state_key, self.STATES["idle"])
        text = custom_text or cfg["text"]

        self._dot.setStyleSheet(f"color: {cfg['dot_color']}; font-size: 10px; background: transparent;")
        self._label.setText(text)
        self._label.setStyleSheet(f"color: {cfg['text_color']}; font-weight: 600; font-size: 12px; background: transparent;")

        self.setStyleSheet(
            f"StatusBadge {{"
            f"  background-color: {cfg['bg_color']};"
            f"  border: 1px solid {cfg['border_color']};"
            f"  border-radius: 13px;"
            f"}}"
        )
