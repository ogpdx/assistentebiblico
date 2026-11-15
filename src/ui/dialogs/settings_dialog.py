"""
Diálogo de configurações do Assistente Bíblico.

Permite:
- Selecionar o microfone de entrada.
- Testar o microfone em tempo real com VU Meter dinâmico.
- Escolher o modelo faster-whisper (Base / Small).
- Configurar Host e Porta do Holyrics API Server.
- Testar a conexão com o Holyrics em tempo real.
- Preserva o token de autenticação sem expô-lo.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QPushButton,
    QFrame,
    QMessageBox,
)

from src.config.settings import Settings
from src.holyrics.client import HolyricsClient
from src.holyrics.api import HolyricsAPI
from src.voice.recorder import AudioRecorder, list_audio_devices
from src.voice.audio_utils import AudioMetrics
from src.ui.widgets.vu_meter import VUMeterWidget


class SettingsDialog(QDialog):
    """Janela modal de configurações do aplicativo."""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Configurações — Assistente Bíblico")
        self.setMinimumWidth(480)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowType.WindowContextHelpButtonHint)

        self._mic_test_recorder: AudioRecorder | None = None

        self._setup_ui()
        self._load_values()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # ── SEÇÃO 1: HOLYRICS API SERVER ──
        lbl_hly = QLabel("CONEXÃO COM O HOLYRICS", self)
        lbl_hly.setProperty("class", "section-title")
        main_layout.addWidget(lbl_hly)

        card_hly = QFrame(self)
        card_hly.setProperty("class", "card")
        layout_hly = QVBoxLayout(card_hly)
        layout_hly.setSpacing(10)
        layout_hly.setContentsMargins(14, 14, 14, 14)

        # Host e Porta
        h_row = QHBoxLayout()
        v_host = QVBoxLayout()
        v_host.addWidget(QLabel("Endereço IP / Host:", self))
        self.txt_host = QLineEdit(self)
        self.txt_host.setPlaceholderText("localhost")
        v_host.addWidget(self.txt_host)
        h_row.addLayout(v_host, stretch=2)

        v_port = QVBoxLayout()
        v_port.addWidget(QLabel("Porta:", self))
        self.spin_port = QSpinBox(self)
        self.spin_port.setRange(1, 65535)
        self.spin_port.setValue(8091)
        v_port.addWidget(self.spin_port)
        h_row.addLayout(v_port, stretch=1)
        layout_hly.addLayout(h_row)

        # Token da API do Holyrics
        v_token = QVBoxLayout()
        v_token.addWidget(QLabel("Token da API do Holyrics:", self))
        h_token_row = QHBoxLayout()
        self.txt_token = QLineEdit(self)
        self.txt_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_token.setPlaceholderText("Cole o token gerado no Holyrics aqui...")
        h_token_row.addWidget(self.txt_token, stretch=1)

        self.btn_toggle_token_visibility = QPushButton("👁️", self)
        self.btn_toggle_token_visibility.setFixedWidth(36)
        self.btn_toggle_token_visibility.setToolTip("Mostrar/Ocultar Token")
        self.btn_toggle_token_visibility.clicked.connect(self._toggle_token_visibility)
        h_token_row.addWidget(self.btn_toggle_token_visibility)
        v_token.addLayout(h_token_row)
        layout_hly.addLayout(v_token)

        # Botão Testar Conexão + Status
        test_h_row = QHBoxLayout()
        self.btn_test_conn = QPushButton("Testar Conexão", self)
        self.btn_test_conn.clicked.connect(self._test_holyrics_connection)
        test_h_row.addWidget(self.btn_test_conn)

        self.lbl_conn_status = QLabel("Não testado", self)
        self.lbl_conn_status.setStyleSheet("color: #9ca3af; font-size: 12px;")
        test_h_row.addWidget(self.lbl_conn_status, stretch=1)
        layout_hly.addLayout(test_h_row)

        main_layout.addWidget(card_hly)

        # ── SEÇÃO 2: MICROFONE E ÁUDIO ──
        lbl_mic = QLabel("DISPOSITIVO DE MICROFONE", self)
        lbl_mic.setProperty("class", "section-title")
        main_layout.addWidget(lbl_mic)

        card_mic = QFrame(self)
        card_mic.setProperty("class", "card")
        layout_mic = QVBoxLayout(card_mic)
        layout_mic.setSpacing(10)
        layout_mic.setContentsMargins(14, 14, 14, 14)

        self.combo_devices = QComboBox(self)
        self._populate_audio_devices()
        layout_mic.addWidget(self.combo_devices)

        # Teste de Microfone ao Vivo
        layout_mic.addWidget(QLabel("Nível de Entrada (Teste):", self))
        self.vu_test = VUMeterWidget(self)
        layout_mic.addWidget(self.vu_test)

        test_mic_row = QHBoxLayout()
        self.btn_toggle_mic_test = QPushButton("Iniciar Teste de Microfone", self)
        self.btn_toggle_mic_test.clicked.connect(self._toggle_mic_test)
        test_mic_row.addWidget(self.btn_toggle_mic_test)

        self.lbl_mic_test_status = QLabel("Fale para ver a barra se mover", self)
        self.lbl_mic_test_status.setStyleSheet("color: #6b7280; font-size: 11px;")
        test_mic_row.addWidget(self.lbl_mic_test_status, stretch=1)
        layout_mic.addLayout(test_mic_row)

        main_layout.addWidget(card_mic)

        # ── SEÇÃO 3: MODELO DE RECONHECIMENTO (WHISPER) ──
        lbl_model = QLabel("MODELO FASTER-WHISPER", self)
        lbl_model.setProperty("class", "section-title")
        main_layout.addWidget(lbl_model)

        card_model = QFrame(self)
        card_model.setProperty("class", "card")
        layout_model = QVBoxLayout(card_model)
        layout_model.setSpacing(6)
        layout_model.setContentsMargins(14, 14, 14, 14)

        self.combo_model = QComboBox(self)
        self.combo_model.addItem("small (Recomendado — Maior precisão para Bíblia)", "small")
        self.combo_model.addItem("base (Mais leve e rápido — menor RAM)", "base")
        layout_model.addWidget(self.combo_model)

        lbl_ram_tip = QLabel("Ambos utilizam quantização int8 em CPU (compatíveis com seus 8 GB de RAM).", self)
        lbl_ram_tip.setStyleSheet("color: #9ca3af; font-size: 11px;")
        layout_model.addWidget(lbl_ram_tip)

        main_layout.addWidget(card_model)

        # ── BOTÕES DE SALVAR / CANCELAR ──
        btn_box = QHBoxLayout()
        btn_box.addStretch(1)

        self.btn_cancel = QPushButton("Cancelar", self)
        self.btn_cancel.clicked.connect(self.reject)
        btn_box.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Salvar Configurações", self)
        self.btn_save.setProperty("class", "btn-primary")
        self.btn_save.clicked.connect(self._save_and_close)
        btn_box.addWidget(self.btn_save)

        main_layout.addLayout(btn_box)

    def _populate_audio_devices(self):
        """Lista os microfones no combobox."""
        devices = list_audio_devices()
        self.combo_devices.clear()

        for d in devices:
            title = f"[{d['index']}] {d['name']}"
            if d.get("is_default"):
                title += " (Padrão)"
            self.combo_devices.addItem(title, d["index"])

    def _load_values(self):
        """Carrega valores existentes do Settings."""
        self.txt_host.setText(self.settings.holyrics_host)
        self.spin_port.setValue(self.settings.holyrics_port)
        self.txt_token.setText(self.settings.holyrics_token or "")

        # Modelo
        current_model = self.settings.get("voice", "model", default="small")
        idx = self.combo_model.findData(current_model)
        if idx >= 0:
            self.combo_model.setCurrentIndex(idx)

        # Dispositivo de áudio salvo
        saved_dev = self.settings.get("voice", "device_index")
        if saved_dev is not None:
            dev_idx = self.combo_devices.findData(saved_dev)
            if dev_idx >= 0:
                self.combo_devices.setCurrentIndex(dev_idx)

    def _test_holyrics_connection(self):
        """Testa conexão imediata com os valores preenchidos."""
        host = self.txt_host.text().strip() or "localhost"
        port = self.spin_port.value()
        token = self.txt_token.text().strip()

        self.lbl_conn_status.setText("Conectando...")
        self.lbl_conn_status.setStyleSheet("color: #f59e0b; font-size: 12px;")
        self.btn_test_conn.setEnabled(False)

        def do_test():
            client = HolyricsClient(host=host, port=port, token=token, timeout=4.0)
            api = HolyricsAPI(client)
            status = api.get_status()
            client.close()
            return status

        # Executa teste rápido
        QTimer.singleShot(50, lambda: self._handle_test_result(do_test()))

    def _handle_test_result(self, status):
        self.btn_test_conn.setEnabled(True)
        if status.connected:
            self.lbl_conn_status.setText("✅ Conectado com sucesso!")
            self.lbl_conn_status.setStyleSheet("color: #10b981; font-weight: bold; font-size: 12px;")
        else:
            self.lbl_conn_status.setText(f"❌ Falha: {status.message[:40]}")
            self.lbl_conn_status.setStyleSheet("color: #ef4444; font-size: 12px;")

    def _toggle_mic_test(self):
        """Inicia ou para o teste dinâmico do microfone."""
        if self._mic_test_recorder and self._mic_test_recorder.is_recording:
            # Para teste
            self._mic_test_recorder.stop_recording()
            self._mic_test_recorder = None
            self.btn_toggle_mic_test.setText("Iniciar Teste de Microfone")
            self.vu_test.reset()
            self.lbl_mic_test_status.setText("Teste parado.")
        else:
            # Inicia teste
            dev_idx = self.combo_devices.currentData()
            self._mic_test_recorder = AudioRecorder(device_index=dev_idx, mode="push_to_talk")

            def on_level(metrics: AudioMetrics):
                # Atualização do VU Meter
                self.vu_test.set_level(metrics.rms, metrics.peak, metrics.dbfs)

            self._mic_test_recorder.on_level_meter = on_level

            if self._mic_test_recorder.start_recording():
                self.btn_toggle_mic_test.setText("Parar Teste de Microfone")
                self.lbl_mic_test_status.setText("Microfone ativo! Fale para ver o volume.")
            else:
                QMessageBox.warning(self, "Aviso", "Não foi possível abrir o microfone selecionado.")

    def _toggle_token_visibility(self):
        """Alterna entre exibir e ocultar o token."""
        if self.txt_token.echoMode() == QLineEdit.EchoMode.Password:
            self.txt_token.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_token_visibility.setText("🙈")
        else:
            self.txt_token.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_token_visibility.setText("👁️")

    def _save_and_close(self):
        """Salva as configurações modificadas."""
        # Se o teste de microfone estava ligado, para
        if self._mic_test_recorder and self._mic_test_recorder.is_recording:
            self._mic_test_recorder.stop_recording()
            self._mic_test_recorder = None

        self.settings.set("holyrics", "host", self.txt_host.text().strip() or "localhost")
        self.settings.set("holyrics", "port", self.spin_port.value())
        self.settings.set("holyrics", "token", self.txt_token.text().strip())
        self.settings.set("voice", "model", self.combo_model.currentData())
        self.settings.set("voice", "device_index", self.combo_devices.currentData())

        try:
            self.settings.save()
            self.accept()
        except Exception as exc:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar configurações: {exc}")

    def closeEvent(self, event):
        """Garante que o gravador de teste seja desligado ao fechar o diálogo."""
        if self._mic_test_recorder and self._mic_test_recorder.is_recording:
            self._mic_test_recorder.stop_recording()
            self._mic_test_recorder = None
        super().closeEvent(event)
