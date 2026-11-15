"""
Estilo visual profissional (QSS) para o Assistente Bíblico.

Paleta de cores:
- Background: #0f1115 (grafite escuro refinado)
- Cards / Containers: #181a20 (cinza grafite)
- Bordas: #262933 (cinza neutro)
- Texto principal: #f3f4f6 (branco suave)
- Texto secundário: #9ca3af (cinza médio)
- Destaque primário: #4f46e5 (índigo vibrante) / hover: #4338ca
- Sucesso / Projetado: #10b981 (esmeralda)
- Gravação ativa: #ef4444 (vermelho vivo)
- Processando / Alerta: #f59e0b (âmbar)
"""

DARK_THEME_QSS = """
/* ── Configurações Globais ── */
QWidget {
    background-color: #0f1115;
    color: #f3f4f6;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    selection-background-color: #4f46e5;
    selection-color: #ffffff;
}

/* ── Janela Principal e Painéis ── */
QMainWindow {
    background-color: #0f1115;
}

QDialog {
    background-color: #12141a;
}

QFrame.card {
    background-color: #181a20;
    border: 1px solid #262933;
    border-radius: 10px;
}

QFrame.card-highlight {
    background-color: #1a1c26;
    border: 1px solid #4f46e5;
    border-radius: 10px;
}

/* ── Cabeçalho e Títulos ── */
QLabel.app-title {
    font-size: 20px;
    font-weight: 700;
    color: #ffffff;
    letter-spacing: 0.5px;
}

QLabel.app-subtitle {
    font-size: 12px;
    color: #9ca3af;
    font-weight: 400;
}

QLabel.section-title {
    font-size: 11px;
    font-weight: 700;
    color: #6366f1;
    text-transform: uppercase;
    letter-spacing: 1px;
}

/* ── Destaque da Referência Ativa ── */
QLabel.verse-display {
    font-size: 26px;
    font-weight: 700;
    color: #10b981;
}

QLabel.verse-subtext {
    font-size: 13px;
    color: #9ca3af;
}

/* ── Botões Gerais ── */
QPushButton {
    background-color: #22252e;
    color: #e5e7eb;
    border: 1px solid #2f3442;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #2b303c;
    border-color: #4f46e5;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #1e2129;
}

QPushButton:disabled {
    background-color: #16181f;
    border-color: #22252e;
    color: #4b5563;
}

/* ── Botão Primário / Destaque ── */
QPushButton.btn-primary {
    background-color: #4f46e5;
    color: #ffffff;
    border: 1px solid #6366f1;
    font-weight: 600;
}

QPushButton.btn-primary:hover {
    background-color: #4338ca;
    border-color: #818cf8;
}

QPushButton.btn-primary:pressed {
    background-color: #3730a3;
}

/* ── Botão Principal de PUSH-TO-TALK ── */
QPushButton#btn_ptt {
    background-color: #1f222b;
    border: 2px solid #3b4252;
    border-radius: 45px;
    min-height: 90px;
    max-height: 90px;
    min-width: 90px;
    max-width: 90px;
    font-size: 28px;
    color: #ffffff;
}

QPushButton#btn_ptt:hover {
    background-color: #2a2f3d;
    border-color: #6366f1;
}

QPushButton#btn_ptt[recording="true"] {
    background-color: #dc2626;
    border-color: #f87171;
    color: #ffffff;
}

QPushButton#btn_ptt[processing="true"] {
    background-color: #d97706;
    border-color: #fbbf24;
}

/* ── Badges de Status ── */
QLabel.badge {
    border-radius: 12px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 600;
}

QLabel.badge-idle {
    background-color: #1e222d;
    color: #9ca3af;
    border: 1px solid #374151;
}

QLabel.badge-listening {
    background-color: #450a0a;
    color: #fca5a5;
    border: 1px solid #dc2626;
}

QLabel.badge-processing {
    background-color: #451a03;
    color: #fde68a;
    border: 1px solid #d97706;
}

QLabel.badge-success {
    background-color: #064e3b;
    color: #6ee7b7;
    border: 1px solid #10b981;
}

QLabel.badge-error {
    background-color: #450a0a;
    color: #fca5a5;
    border: 1px solid #ef4444;
}

/* ── Barra de Progresso / VU Meter ── */
QProgressBar {
    background-color: #12141a;
    border: 1px solid #262933;
    border-radius: 4px;
    text-align: center;
    color: transparent;
    max-height: 8px;
    min-height: 8px;
}

QProgressBar::chunk {
    background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:0.7 #3b82f6, stop:0.95 #ef4444);
    border-radius: 3px;
}

/* ── Campos de Entrada e Seleção ── */
QLineEdit, QComboBox, QSpinBox {
    background-color: #16181f;
    border: 1px solid #2d313d;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f3f4f6;
    font-size: 13px;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #6366f1;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #181a20;
    border: 1px solid #2f3442;
    selection-background-color: #4f46e5;
    selection-color: #ffffff;
    color: #e5e7eb;
}

/* ── Rodapé / Status Bar ── */
QStatusBar {
    background-color: #0c0d10;
    border-top: 1px solid #1f222a;
    color: #6b7280;
    font-size: 11px;
}

/* ── Scrollbars Sutis ── */
QScrollBar:vertical {
    border: none;
    background: #0f1115;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #272a34;
    min-height: 20px;
    border-radius: 3px;
}

QScrollBar::handle:vertical:hover {
    background: #4f46e5;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
