"""
Widget de VU Meter em PySide6 para exibição dinâmica de volume em tempo real.
"""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QProgressBar, QWidget, QHBoxLayout, QLabel


class VUMeterWidget(QWidget):
    """Barra horizontal com medidor de volume (RMS e dBFS) e indicador de pico."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.bar = QProgressBar(self)
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)

        self.lbl_db = QLabel("-inf dB", self)
        self.lbl_db.setStyleSheet("color: #6b7280; font-size: 11px; min-width: 50px;")
        self.lbl_db.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.bar, stretch=1)
        layout.addWidget(self.lbl_db)

    def set_level(self, rms: float, peak: float, dbfs: float):
        """Atualiza a barra com os valores calculados do áudio."""
        # Mapeia RMS (0.0 a ~0.35) para 0 - 100%
        pct = int(min(max(rms * 280, 0.0), 100.0))
        self.bar.setValue(pct)

        if rms > 1e-5:
            self.lbl_db.setText(f"{dbfs:.1f} dB")
            if peak >= 0.98:
                self.lbl_db.setStyleSheet("color: #ef4444; font-weight: bold; font-size: 11px;")
            else:
                self.lbl_db.setStyleSheet("color: #9ca3af; font-size: 11px;")
        else:
            self.lbl_db.setText("-inf dB")
            self.lbl_db.setStyleSheet("color: #6b7280; font-size: 11px;")

    def reset(self):
        """Reseta a barra para zero."""
        self.bar.setValue(0)
        self.lbl_db.setText("-inf dB")
        self.lbl_db.setStyleSheet("color: #6b7280; font-size: 11px;")
