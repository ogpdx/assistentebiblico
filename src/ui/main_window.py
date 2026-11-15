"""
Janela principal do Assistente Bíblico em PySide6.

Estrutura visual:
A. Cabeçalho (Título, Status Holyrics, Microfone)
B. Área de Operação (Push-to-Talk OU Automático, VU Meter, Estados)
C. Card de Destaque da Referência Atual na TV (Sincronizada em tempo real)
D. Painel de Diagnóstico do Reconhecimento (Fala -> Interpretado -> Ação)
E. Controles Auxiliares (Próximo, Anterior, Limpar, Sincronizar, Configurações)
F. Rodapé (Latência, Modelo Ativo, Mensagens de Integridade)
"""

from typing import Optional
import numpy as np
from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QStatusBar,
    QMessageBox,
    QComboBox,
    QStackedWidget,
)

from src.config.settings import Settings
from src.core.controller import VoiceHolyricsController, ExecutionResult
from src.core.logging_config import get_logger
from src.holyrics.client import HolyricsClient
from src.holyrics.api import HolyricsAPI
from src.voice.recorder import AudioRecorder, list_audio_devices
from src.voice.transcriber import SpeechTranscriber
from src.voice.audio_utils import AudioMetrics
from src.ui.styles.theme import DARK_THEME_QSS
from src.ui.widgets.vu_meter import VUMeterWidget
from src.ui.widgets.status_badge import StatusBadge
from src.ui.threads import CommandProcessingWorker, HolyricsSyncWorker, AutoListenWorker
from src.ui.dialogs.settings_dialog import SettingsDialog

logger = get_logger(__name__)

# Constantes de modo
MODE_PTT = 0
MODE_AUTO = 1


class MainWindow(QMainWindow):
    """Janela principal do Assistente Bíblico."""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self.settings = settings

        self.setWindowTitle("Assistente Bíblico — Controle por Voz")
        self.setMinimumSize(780, 700)
        self.resize(840, 740)
        self.setStyleSheet(DARK_THEME_QSS)

        # Componentes do Core
        self.client: Optional[HolyricsClient] = None
        self.api: Optional[HolyricsAPI] = None
        self.transcriber: Optional[SpeechTranscriber] = None
        self.controller: Optional[VoiceHolyricsController] = None
        self.recorder: Optional[AudioRecorder] = None

        # Workers
        self._processing_worker: Optional[CommandProcessingWorker] = None
        self._sync_worker: Optional[HolyricsSyncWorker] = None
        self._auto_worker: Optional[AutoListenWorker] = None

        # Estado da gravação Push-to-Talk
        self._is_holding_talk = False
        # Modo atual
        self._current_mode = MODE_PTT

        self._init_backend()
        self._setup_ui()
        self._start_background_sync()

    def _init_backend(self):
        """Inicializa os clientes, modelos e controladores existentes."""
        host = self.settings.holyrics_host
        port = self.settings.holyrics_port
        token = self.settings.holyrics_token

        self.client = HolyricsClient(host=host, port=port, token=token, timeout=self.settings.holyrics_timeout)
        self.api = HolyricsAPI(self.client)

        # Transcritor
        model_name = self.settings.get("voice", "model", default="small")
        self.transcriber = SpeechTranscriber(
            model_size=model_name,
            device="cpu",
            compute_type="int8",
            beam_size=2,
        )

        # Controlador central
        self.controller = VoiceHolyricsController(
            api=self.api,
            transcriber=self.transcriber,
            duplicate_threshold_seconds=2.0,
        )

        # Gravador de áudio (Push-to-Talk)
        dev_idx = self.settings.get("voice", "device_index")
        self.recorder = AudioRecorder(device_index=dev_idx, mode="push_to_talk")
        self.recorder.on_level_meter = self._on_audio_level_meter

    def _setup_ui(self):
        """Constrói a interface com todas as seções A, B, C, D, E, F."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(24, 20, 24, 16)
        root_layout.setSpacing(16)

        # ── SEÇÃO A: CABEÇALHO ──
        header_layout = QHBoxLayout()

        v_title = QVBoxLayout()
        v_title.setSpacing(2)
        lbl_title = QLabel("Assistente Bíblico", self)
        lbl_title.setProperty("class", "app-title")
        lbl_sub = QLabel("Controle de projeção de versículos por comando de voz", self)
        lbl_sub.setProperty("class", "app-subtitle")
        v_title.addWidget(lbl_title)
        v_title.addWidget(lbl_sub)
        header_layout.addLayout(v_title, stretch=1)

        # Indicador de Conexão com Holyrics
        self.badge_hly = QLabel("● Holyrics Verificando...", self)
        self.badge_hly.setStyleSheet("background-color: #1e222d; color: #9ca3af; border: 1px solid #374151; border-radius: 12px; padding: 4px 12px; font-weight: 600; font-size: 11px;")
        header_layout.addWidget(self.badge_hly)

        # Botão Configurações
        self.btn_open_settings = QPushButton("⚙️ Configurações", self)
        self.btn_open_settings.clicked.connect(self._open_settings)
        header_layout.addWidget(self.btn_open_settings)

        root_layout.addLayout(header_layout)

        # ── SEÇÃO D: DESTAQUE DA REFERÊNCIA ATUAL NA TV (Topo) ──
        card_tv = QFrame(self)
        card_tv.setProperty("class", "card-highlight")
        layout_tv = QHBoxLayout(card_tv)
        layout_tv.setContentsMargins(20, 16, 20, 16)

        v_tv_info = QVBoxLayout()
        v_tv_info.setSpacing(4)
        lbl_tv_title = QLabel("PROJEÇÃO ATIVA NA TV (HOLYRICS)", self)
        lbl_tv_title.setProperty("class", "section-title")
        self.lbl_active_verse = QLabel("Nenhum versículo ativo", self)
        self.lbl_active_verse.setProperty("class", "verse-display")
        self.lbl_active_details = QLabel("A tela de projeção está vazia ou exibindo outro conteúdo.", self)
        self.lbl_active_details.setProperty("class", "verse-subtext")
        v_tv_info.addWidget(lbl_tv_title)
        v_tv_info.addWidget(self.lbl_active_verse)
        v_tv_info.addWidget(self.lbl_active_details)
        layout_tv.addLayout(v_tv_info, stretch=1)

        # Botão de sincronização manual rápida
        self.btn_sync = QPushButton("🔄 Sincronizar", self)
        self.btn_sync.clicked.connect(self._manual_sync)
        layout_tv.addWidget(self.btn_sync)

        root_layout.addWidget(card_tv)

        # ── SEÇÃO B: ÁREA PRINCIPAL DE OPERAÇÃO ──
        card_op = QFrame(self)
        card_op.setProperty("class", "card")
        layout_op = QVBoxLayout(card_op)
        layout_op.setContentsMargins(20, 20, 20, 20)
        layout_op.setSpacing(14)

        # Topo: Seletor de Modo + Status Badge
        top_op = QHBoxLayout()
        lbl_op_title = QLabel("CONTROLE POR VOZ", self)
        lbl_op_title.setProperty("class", "section-title")
        top_op.addWidget(lbl_op_title)
        top_op.addStretch(1)

        # Seletor de Modo
        lbl_mode = QLabel("Modo:", self)
        lbl_mode.setStyleSheet("color: #9ca3af; font-size: 12px;")
        top_op.addWidget(lbl_mode)
        self.combo_mode = QComboBox(self)
        self.combo_mode.addItem("🎙️ Push-to-Talk")
        self.combo_mode.addItem("📡 Automático")
        self.combo_mode.setCurrentIndex(MODE_PTT)
        self.combo_mode.currentIndexChanged.connect(self._on_mode_changed)
        self.combo_mode.setStyleSheet("min-width: 160px;")
        top_op.addWidget(self.combo_mode)

        top_op.addSpacing(12)
        self.status_badge = StatusBadge(self)
        top_op.addWidget(self.status_badge)
        layout_op.addLayout(top_op)

        # Stacked Widget: Push-to-Talk vs Automático
        self.mode_stack = QStackedWidget(self)

        # --- Página 0: Push-to-Talk ---
        ptt_page = QWidget(self)
        ptt_layout = QVBoxLayout(ptt_page)
        ptt_layout.setContentsMargins(0, 0, 0, 0)
        ptt_layout.setSpacing(10)

        btn_center_layout = QHBoxLayout()
        btn_center_layout.addStretch(1)
        self.btn_ptt = QPushButton("🎙️", self)
        self.btn_ptt.setObjectName("btn_ptt")
        self.btn_ptt.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_ptt.pressed.connect(self._on_ptt_pressed)
        self.btn_ptt.released.connect(self._on_ptt_released)
        btn_center_layout.addWidget(self.btn_ptt)
        btn_center_layout.addStretch(1)
        ptt_layout.addLayout(btn_center_layout)

        self.lbl_ptt_hint = QLabel("Segure [ENTER] ou clique para falar", self)
        self.lbl_ptt_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_ptt_hint.setStyleSheet("color: #9ca3af; font-size: 13px; font-weight: 500;")
        ptt_layout.addWidget(self.lbl_ptt_hint)

        self.mode_stack.addWidget(ptt_page)

        # --- Página 1: Modo Automático ---
        auto_page = QWidget(self)
        auto_layout = QVBoxLayout(auto_page)
        auto_layout.setContentsMargins(0, 0, 0, 0)
        auto_layout.setSpacing(10)

        # Indicador de estado automático
        auto_status_row = QHBoxLayout()
        self.lbl_auto_icon = QLabel("📡", self)
        self.lbl_auto_icon.setStyleSheet("font-size: 36px; background: transparent;")
        auto_status_row.addStretch(1)
        auto_status_row.addWidget(self.lbl_auto_icon)

        self.lbl_auto_status = QLabel("Escuta automática desativada", self)
        self.lbl_auto_status.setStyleSheet("color: #9ca3af; font-size: 15px; font-weight: 600;")
        auto_status_row.addWidget(self.lbl_auto_status)
        auto_status_row.addStretch(1)
        auto_layout.addLayout(auto_status_row)

        # Botões de controle automático
        auto_btn_row = QHBoxLayout()
        auto_btn_row.addStretch(1)

        self.btn_auto_start = QPushButton("▶ Iniciar Escuta", self)
        self.btn_auto_start.setStyleSheet("background-color: #065f46; color: #6ee7b7; border: 1px solid #10b981; border-radius: 8px; padding: 8px 20px; font-weight: 600;")
        self.btn_auto_start.clicked.connect(self._start_auto_listen)
        auto_btn_row.addWidget(self.btn_auto_start)

        self.btn_auto_pause = QPushButton("⏸ Pausar", self)
        self.btn_auto_pause.setStyleSheet("background-color: #78350f; color: #fde68a; border: 1px solid #f59e0b; border-radius: 8px; padding: 8px 20px; font-weight: 600;")
        self.btn_auto_pause.clicked.connect(self._toggle_auto_pause)
        self.btn_auto_pause.setEnabled(False)
        auto_btn_row.addWidget(self.btn_auto_pause)

        self.btn_auto_stop = QPushButton("⏹ Parar", self)
        self.btn_auto_stop.setStyleSheet("background-color: #7f1d1d; color: #fca5a5; border: 1px solid #ef4444; border-radius: 8px; padding: 8px 20px; font-weight: 600;")
        self.btn_auto_stop.clicked.connect(self._stop_auto_listen)
        self.btn_auto_stop.setEnabled(False)
        auto_btn_row.addWidget(self.btn_auto_stop)

        auto_btn_row.addStretch(1)
        auto_layout.addLayout(auto_btn_row)

        self.mode_stack.addWidget(auto_page)

        layout_op.addWidget(self.mode_stack)

        # VU Meter (compartilhado entre modos)
        self.vu_meter = VUMeterWidget(self)
        layout_op.addWidget(self.vu_meter)

        root_layout.addWidget(card_op)

        # ── SEÇÃO C: RESULTADO DO RECONHECIMENTO & DIAGNÓSTICO ──
        card_res = QFrame(self)
        card_res.setProperty("class", "card")
        layout_res = QVBoxLayout(card_res)
        layout_res.setContentsMargins(18, 14, 18, 14)
        layout_res.setSpacing(8)

        lbl_res_title = QLabel("ÚLTIMO COMANDO PROCESSADO", self)
        lbl_res_title.setProperty("class", "section-title")
        layout_res.addWidget(lbl_res_title)

        grid_res = QHBoxLayout()

        # Coluna 1: Fala Transcrita
        v_col1 = QVBoxLayout()
        v_col1.addWidget(QLabel("Fala Reconhecida:", self))
        self.lbl_transcribed_text = QLabel("—", self)
        self.lbl_transcribed_text.setStyleSheet("color: #ffffff; font-weight: 600; font-size: 14px;")
        self.lbl_transcribed_text.setWordWrap(True)
        v_col1.addWidget(self.lbl_transcribed_text)
        grid_res.addLayout(v_col1, stretch=2)

        # Coluna 2: Referência / Comando
        v_col2 = QVBoxLayout()
        v_col2.addWidget(QLabel("Comando / Referência:", self))
        self.lbl_interpreted_ref = QLabel("—", self)
        self.lbl_interpreted_ref.setStyleSheet("color: #6366f1; font-weight: 700; font-size: 14px;")
        v_col2.addWidget(self.lbl_interpreted_ref)
        grid_res.addLayout(v_col2, stretch=1)

        # Coluna 3: Resultado da Operação
        v_col3 = QVBoxLayout()
        v_col3.addWidget(QLabel("Status da Projeção:", self))
        self.lbl_exec_result = QLabel("Aguardando comando...", self)
        self.lbl_exec_result.setStyleSheet("color: #9ca3af; font-size: 13px;")
        self.lbl_exec_result.setWordWrap(True)
        v_col3.addWidget(self.lbl_exec_result)
        grid_res.addLayout(v_col3, stretch=2)

        layout_res.addLayout(grid_res)
        root_layout.addWidget(card_res)

        # ── SEÇÃO E: CONTROLES AUXILIARES DE NAVEGAÇÃO ──
        ctrl_layout = QHBoxLayout()
        ctrl_layout.setSpacing(10)

        self.btn_prev = QPushButton("◀  Versículo Anterior", self)
        self.btn_prev.clicked.connect(self._nav_previous)
        ctrl_layout.addWidget(self.btn_prev, stretch=1)

        self.btn_next = QPushButton("Próximo Versículo  ▶", self)
        self.btn_next.clicked.connect(self._nav_next)
        ctrl_layout.addWidget(self.btn_next, stretch=1)

        self.btn_clear = QPushButton("Limpar Tela (TV)", self)
        self.btn_clear.clicked.connect(self._clear_presentation)
        ctrl_layout.addWidget(self.btn_clear, stretch=1)

        root_layout.addLayout(ctrl_layout)

        # ── SEÇÃO F: RODAPÉ E DIAGNÓSTICO ──
        status_bar = QStatusBar(self)
        self.setStatusBar(status_bar)

        self.lbl_status_device = QLabel("Microfone: Padrão", self)
        self.lbl_status_model = QLabel(f"Whisper: {self.settings.get('voice', 'model', default='small')}", self)
        self.lbl_status_latency = QLabel("Latência: —", self)

        status_bar.addWidget(self.lbl_status_device, 1)
        status_bar.addWidget(self.lbl_status_model, 1)
        status_bar.addPermanentWidget(self.lbl_status_latency)

    def _start_background_sync(self):
        """Inicia a thread de sincronização periódica com o Holyrics."""
        self._sync_worker = HolyricsSyncWorker(api=self.api, interval_seconds=2.0, parent=self)
        self._sync_worker.presentation_synced.connect(self._on_presentation_synced)
        self._sync_worker.connection_status_changed.connect(self._on_connection_status_changed)
        self._sync_worker.start()

    # ──────────────────────────────────────────────
    # Seletor de Modo
    # ──────────────────────────────────────────────

    def _on_mode_changed(self, index: int):
        """Alterna entre Push-to-Talk e Automático de forma segura."""
        # Interrompe qualquer operação em andamento no modo anterior
        if self._current_mode == MODE_PTT:
            if self._is_holding_talk:
                self._is_holding_talk = False
                if self.recorder.is_recording:
                    self.recorder.stop_recording()
        elif self._current_mode == MODE_AUTO:
            self._stop_auto_listen()

        self._current_mode = index
        self.mode_stack.setCurrentIndex(index)
        self.vu_meter.reset()
        self.status_badge.set_state("idle")

        if index == MODE_PTT:
            self.lbl_ptt_hint.setText("Segure [ENTER] ou clique para falar")
        else:
            self.lbl_auto_status.setText("Escuta automática desativada")
            self.lbl_auto_status.setStyleSheet("color: #9ca3af; font-size: 15px; font-weight: 600;")

    # ──────────────────────────────────────────────
    # Ações de Push-to-Talk
    # ──────────────────────────────────────────────

    def _on_ptt_pressed(self):
        """Disparado quando o botão PTT é clicado/segurado ou ao apertar ENTER."""
        if self._current_mode != MODE_PTT:
            return
        if self._is_holding_talk:
            return

        # Impede gravação se já estiver processando outro comando
        if self._processing_worker and self._processing_worker.isRunning():
            return

        self._is_holding_talk = True
        self.status_badge.set_state("listening")
        self.lbl_ptt_hint.setText("Ouvindo... Solte o botão ou ENTER para enviar")
        self.btn_ptt.setProperty("recording", True)
        self.btn_ptt.style().unpolish(self.btn_ptt)
        self.btn_ptt.style().polish(self.btn_ptt)

        # Inicia gravação no recorder
        self.recorder.start_recording()

    def _on_ptt_released(self):
        """Disparado quando o botão PTT é solto ou tecla ENTER liberada."""
        if self._current_mode != MODE_PTT:
            return
        if not self._is_holding_talk:
            return

        self._is_holding_talk = False
        self.status_badge.set_state("processing")
        self.lbl_ptt_hint.setText("Processando voz e consultando Holyrics...")
        self.btn_ptt.setProperty("recording", False)
        self.btn_ptt.setProperty("processing", True)
        self.btn_ptt.style().unpolish(self.btn_ptt)
        self.btn_ptt.style().polish(self.btn_ptt)

        # Finaliza gravação e recupera o áudio
        audio = self.recorder.stop_recording()
        self.vu_meter.reset()

        if audio is None or len(audio) < 1600:
            self._on_processing_finished(
                ExecutionResult(
                    success=False,
                    raw_text="",
                    command=None,
                    action_executed="None",
                    message="Áudio muito curto ou inaudível.",
                )
            )
            return

        # Despacha processamento em thread separada
        self._processing_worker = CommandProcessingWorker(
            controller=self.controller,
            audio_data=audio,
            parent=self,
        )
        self._processing_worker.finished.connect(self._on_processing_finished)
        self._processing_worker.start()

    # ──────────────────────────────────────────────
    # Escuta Automática
    # ──────────────────────────────────────────────

    def _start_auto_listen(self):
        """Inicia a escuta automática com VAD."""
        if self._auto_worker and self._auto_worker.isRunning():
            return

        dev_idx = self.settings.get("voice", "device_index")
        self._auto_worker = AutoListenWorker(
            controller=self.controller,
            device_index=dev_idx,
            sample_rate=16000,
            vad_threshold=0.015,
            silence_seconds=1.0,
            parent=self,
        )
        self._auto_worker.speech_detected.connect(self._on_auto_speech_detected)
        self._auto_worker.result_ready.connect(self._on_processing_finished)
        self._auto_worker.listening_status.connect(self._on_auto_listening_status)
        self._auto_worker.error_occurred.connect(self._on_auto_error)
        self._auto_worker.level_meter.connect(self._on_auto_level_meter)
        self._auto_worker.start()

        self.btn_auto_start.setEnabled(False)
        self.btn_auto_pause.setEnabled(True)
        self.btn_auto_stop.setEnabled(True)

    def _stop_auto_listen(self):
        """Para a escuta automática com segurança."""
        if self._auto_worker and self._auto_worker.isRunning():
            self._auto_worker.stop()
            self._auto_worker.wait(2000)
            self._auto_worker = None

        self.btn_auto_start.setEnabled(True)
        self.btn_auto_pause.setEnabled(False)
        self.btn_auto_stop.setEnabled(False)
        self.btn_auto_pause.setText("⏸ Pausar")
        self.lbl_auto_status.setText("Escuta automática desativada")
        self.lbl_auto_status.setStyleSheet("color: #9ca3af; font-size: 15px; font-weight: 600;")
        self.status_badge.set_state("idle")
        self.vu_meter.reset()

    def _toggle_auto_pause(self):
        """Alterna entre pausar e retomar a escuta automática."""
        if not self._auto_worker:
            return

        if self._auto_worker.is_paused:
            self._auto_worker.resume()
            self.btn_auto_pause.setText("⏸ Pausar")
            self.lbl_auto_status.setText("Escuta automática ativa — aguardando fala...")
            self.lbl_auto_status.setStyleSheet("color: #10b981; font-size: 15px; font-weight: 600;")
            self.status_badge.set_state("idle", "Escutando")
        else:
            self._auto_worker.pause()
            self.btn_auto_pause.setText("▶ Retomar")
            self.lbl_auto_status.setText("⏸ Escuta automática PAUSADA")
            self.lbl_auto_status.setStyleSheet("color: #f59e0b; font-size: 15px; font-weight: 600;")
            self.status_badge.set_state("idle", "Pausado")
            self.vu_meter.reset()

    @Slot()
    def _on_auto_speech_detected(self):
        """Callback: VAD detectou início de fala no modo automático."""
        self.status_badge.set_state("listening", "Fala detectada...")

    @Slot(bool)
    def _on_auto_listening_status(self, is_active: bool):
        """Callback: status da escuta automática mudou."""
        if is_active:
            self.lbl_auto_status.setText("Escuta automática ativa — aguardando fala...")
            self.lbl_auto_status.setStyleSheet("color: #10b981; font-size: 15px; font-weight: 600;")
            self.status_badge.set_state("idle", "Escutando")
        else:
            self.lbl_auto_status.setText("Escuta automática desativada")
            self.lbl_auto_status.setStyleSheet("color: #9ca3af; font-size: 15px; font-weight: 600;")
            self.status_badge.set_state("idle")

    @Slot(str)
    def _on_auto_error(self, msg: str):
        """Callback: erro no modo automático."""
        self._stop_auto_listen()
        self.combo_mode.setCurrentIndex(MODE_PTT)
        self.lbl_exec_result.setText(f"⚠️ {msg}")
        self.lbl_exec_result.setStyleSheet("color: #ef4444; font-size: 13px;")
        self.status_badge.set_state("error", "Erro")
        QMessageBox.warning(self, "Erro na Escuta Automática", f"A escuta automática foi interrompida:\n{msg}\n\nVoltando para Push-to-Talk.")

    @Slot(AudioMetrics)
    def _on_auto_level_meter(self, metrics: AudioMetrics):
        """Atualização do VU Meter no modo automático."""
        QTimer.singleShot(0, lambda: self.vu_meter.set_level(metrics.rms, metrics.peak, metrics.dbfs))

    # ──────────────────────────────────────────────
    # Callbacks Compartilhados (PTT e Automático)
    # ──────────────────────────────────────────────

    @Slot(object)
    def _on_audio_level_meter(self, metrics: AudioMetrics):
        """Atualização thread-safe do medidor de volume (Push-to-Talk)."""
        if self._is_holding_talk:
            QTimer.singleShot(0, lambda: self.vu_meter.set_level(metrics.rms, metrics.peak, metrics.dbfs))

    @Slot(ExecutionResult)
    def _on_processing_finished(self, result: ExecutionResult):
        """Callback após processamento da transcrição e execução no Holyrics."""
        # Atualiza visual do botão PTT se estiver nesse modo
        if self._current_mode == MODE_PTT:
            self.btn_ptt.setProperty("processing", False)
            self.btn_ptt.style().unpolish(self.btn_ptt)
            self.btn_ptt.style().polish(self.btn_ptt)
            self.lbl_ptt_hint.setText("Segure [ENTER] ou clique para falar")

        # Atualiza campos de diagnóstico
        self.lbl_transcribed_text.setText(f'"{result.raw_text}"' if result.raw_text else "(Vazio)")

        if result.command:
            cmd_name = result.command.command_type.value
            if hasattr(result.command, "display_name"):
                self.lbl_interpreted_ref.setText(result.command.display_name)
            else:
                self.lbl_interpreted_ref.setText(cmd_name)
        else:
            self.lbl_interpreted_ref.setText("—")

        # Status Badge e Mensagem de Execução
        if result.success:
            # Tratamento especial para CLEAR_PRESENTATION
            if result.action_executed == "CloseCurrentPresentation":
                self.status_badge.set_state("success", "Projeção Encerrada")
                self.lbl_active_verse.setText("Nenhum versículo na TV")
                self.lbl_active_verse.setStyleSheet("color: #9ca3af; font-size: 22px; font-weight: 600;")
                self.lbl_active_details.setText("Projeção bíblica encerrada.")
            else:
                self.status_badge.set_state("success", "Projetado na TV")
            self.lbl_exec_result.setText(f"✅ {result.message}")
            self.lbl_exec_result.setStyleSheet("color: #10b981; font-weight: 600; font-size: 13px;")
            if result.current_presentation:
                self._update_tv_display(result.current_presentation)
        else:
            # No modo automático, UNKNOWN é esperado e silencioso
            if (
                self._current_mode == MODE_AUTO
                and result.command
                and result.command.command_type.value == "UNKNOWN"
            ):
                self.status_badge.set_state("idle", "Escutando")
                # Exibe no diagnóstico mas NÃO bloqueia
                self.lbl_exec_result.setText("Ignorado (fala sem comando válido)")
                self.lbl_exec_result.setStyleSheet("color: #6b7280; font-size: 13px;")
            else:
                self.status_badge.set_state("error", "Bloqueado")
                self.lbl_exec_result.setText(f"⚠️ {result.message}")
                self.lbl_exec_result.setStyleSheet("color: #ef4444; font-size: 13px;")

        # Latência no rodapé
        if result.transcription:
            self.lbl_status_latency.setText(f"Inferência: {result.transcription.inference_time_seconds:.2f}s")

        # Força atualização da TV após execução bem-sucedida
        if result.success:
            self._manual_sync()

    # ──────────────────────────────────────────────
    # Navegação Auxiliar e Sincronização
    # ──────────────────────────────────────────────

    def _nav_next(self):
        """Avança versículo via controlador (com checagem de tipo)."""
        self._dispatch_text_command("Próximo versículo")

    def _nav_previous(self):
        """Volta versículo via controlador (com checagem de tipo)."""
        self._dispatch_text_command("Versículo anterior")

    def _clear_presentation(self):
        """Fecha a apresentação da tela."""
        self._dispatch_text_command("Limpar projeção")

    def _dispatch_text_command(self, text: str):
        """Dispara um comando em texto em background."""
        if self._processing_worker and self._processing_worker.isRunning():
            return

        self.status_badge.set_state("processing")
        self._processing_worker = CommandProcessingWorker(
            controller=self.controller,
            text_command=text,
            parent=self,
        )
        self._processing_worker.finished.connect(self._on_processing_finished)
        self._processing_worker.start()

    def _manual_sync(self):
        """Consulta imediata da apresentação atual."""
        pres = self.controller.get_current_presentation_state()
        self._update_tv_display(pres)

    @Slot(object)
    def _on_presentation_synced(self, pres_data: Optional[dict]):
        """Atualização periódica recebida da thread de sincronização."""
        self._update_tv_display(pres_data)

    def _update_tv_display(self, pres_data: Optional[dict]):
        """Atualiza a área de destaque com o versículo projetado na TV."""
        if pres_data and (pres_data.get("type") == "verse" or "slide_number" in pres_data):
            name = pres_data.get("name") or pres_data.get("id") or "Versículo"
            slide = pres_data.get("slide_number", "")
            total = pres_data.get("total_slides", "")
            slide_info = f"Slide {slide}" if not total else f"Slide {slide}/{total}"
            self.lbl_active_verse.setText(name)
            self.lbl_active_verse.setStyleSheet("color: #10b981; font-size: 28px; font-weight: 700;")
            self.lbl_active_details.setText(f"Projeção bíblica ativa ({slide_info}). Sincronizado com o Holyrics.")
        elif pres_data and pres_data.get("type"):
            tipo = pres_data.get("type")
            self.lbl_active_verse.setText(f"Conteúdo: {tipo.upper()}")
            self.lbl_active_verse.setStyleSheet("color: #f59e0b; font-size: 22px; font-weight: 700;")
            self.lbl_active_details.setText("A apresentação atual não é bíblica.")
        else:
            self.lbl_active_verse.setText("Nenhum versículo na TV")
            self.lbl_active_verse.setStyleSheet("color: #9ca3af; font-size: 22px; font-weight: 600;")
            self.lbl_active_details.setText("A tela de projeção está livre ou desligada.")

    @Slot(bool)
    def _on_connection_status_changed(self, is_connected: bool):
        """Atualiza o badge de conectividade do Holyrics."""
        if is_connected:
            self.badge_hly.setText("● Holyrics Conectado")
            self.badge_hly.setStyleSheet("background-color: #064e3b; color: #6ee7b7; border: 1px solid #10b981; border-radius: 12px; padding: 4px 12px; font-weight: 600; font-size: 11px;")
        else:
            self.badge_hly.setText("● Holyrics Desconectado")
            self.badge_hly.setStyleSheet("background-color: #450a0a; color: #fca5a5; border: 1px solid #ef4444; border-radius: 12px; padding: 4px 12px; font-weight: 600; font-size: 11px;")

    # ──────────────────────────────────────────────
    # Eventos de Teclado (Push-to-Talk via ENTER)
    # ──────────────────────────────────────────────

    def keyPressEvent(self, event: QKeyEvent):
        if self._current_mode != MODE_PTT:
            super().keyPressEvent(event)
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not event.isAutoRepeat() and not self._is_holding_talk:
                self._on_ptt_pressed()
                return
        super().keyPressEvent(event)

    def keyReleaseEvent(self, event: QKeyEvent):
        if self._current_mode != MODE_PTT:
            super().keyReleaseEvent(event)
            return
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if not event.isAutoRepeat() and self._is_holding_talk:
                self._on_ptt_released()
                return
        super().keyReleaseEvent(event)

    def _open_settings(self):
        """Abre a janela modal de configurações."""
        # Pausa o modo automático durante as configurações
        was_auto_running = self._auto_worker and self._auto_worker.isRunning()
        if was_auto_running:
            self._auto_worker.pause()

        dlg = SettingsDialog(self.settings, self)
        if dlg.exec():
            # Recarrega configurações
            dev_idx = self.settings.get("voice", "device_index")
            self.recorder.device_index = dev_idx
            model_name = self.settings.get("voice", "model", default="small")
            self.lbl_status_model.setText(f"Whisper: {model_name}")

            # Re-inicializa cliente
            self.client = HolyricsClient(
                host=self.settings.holyrics_host,
                port=self.settings.holyrics_port,
                token=self.settings.holyrics_token,
                timeout=self.settings.holyrics_timeout,
            )
            self.api = HolyricsAPI(self.client)
            self.controller.api = self.api
            self._manual_sync()

        # Retoma escuta automática se estava ativa
        if was_auto_running and self._auto_worker:
            self._auto_worker.resume()

    def closeEvent(self, event):
        """Encerra com segurança todas as threads e streams de áudio."""
        # Para escuta automática
        if self._auto_worker and self._auto_worker.isRunning():
            self._auto_worker.stop()
            self._auto_worker.wait(2000)

        if self._sync_worker:
            self._sync_worker.stop()

        if self.recorder and self.recorder.is_recording:
            self.recorder.stop_recording()

        if self.client:
            self.client.close()

        super().closeEvent(event)
