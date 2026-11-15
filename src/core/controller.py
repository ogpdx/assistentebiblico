"""
Controlador central do Assistente Bíblico.

Orquestra o ciclo operacional completo:
1. Recebe áudio do microfone ou texto.
2. Transcreve com faster-whisper.
3. Interpreta a intenção e valida limites bíblicos.
4. Consulta o estado real do Holyrics via GetCurrentPresentation.
5. Executa a ação segura na API do Holyrics.
6. Retorna resultado com status e sincronização em tempo real.

Princípio de Falha Segura:
- Nunca executa comandos classificados como UNKNOWN.
- Bloqueia comandos de navegação se a apresentação ativa não for bíblica.
- Previne duplicação acidental de comandos idênticos em curto intervalo.
- Bloqueia execução concorrente via Lock.
- Trata quedas de conexão do Holyrics sem travar o sistema.
"""

from dataclasses import dataclass, field
import threading
import time
from typing import Optional
import numpy as np

from src.core.logging_config import get_logger
from src.holyrics.api import HolyricsAPI
from src.holyrics.exceptions import (
    HolyricsError,
    HolyricsConnectionError,
    HolyricsTimeoutError,
    HolyricsAuthError,
    HolyricsPermissionError,
    HolyricsAPIError,
)
from src.interpreter import (
    classify_command,
    CommandType,
    InterpretedCommand,
    BibleReferenceCommand,
    NavigationCommand,
    UnknownCommand,
)
from src.voice.transcriber import SpeechTranscriber, TranscriptionResult

logger = get_logger(__name__)


@dataclass
class ExecutionResult:
    """Resultado detalhado do processamento e execução de um comando."""
    success: bool
    raw_text: str
    command: InterpretedCommand
    action_executed: str
    message: str
    transcription: Optional[TranscriptionResult] = None
    holyrics_response: Optional[dict] = None
    current_presentation: Optional[dict] = None


class VoiceHolyricsController:
    """Controlador que orquestra voz, interpretação e API do Holyrics."""

    def __init__(
        self,
        api: HolyricsAPI,
        transcriber: Optional[SpeechTranscriber] = None,
        duplicate_threshold_seconds: float = 2.0,
    ):
        self.api = api
        self.transcriber = transcriber
        self.duplicate_threshold_seconds = duplicate_threshold_seconds

        self._lock = threading.Lock()
        self._last_command_str: str = ""
        self._last_command_time: float = 0.0

    def get_current_presentation_state(self) -> dict | None:
        """Consulta o estado real da apresentação atualmente ativa no Holyrics."""
        try:
            return self.api.get_current_presentation()
        except HolyricsError as exc:
            logger.warning("Erro ao consultar apresentação atual: %s", exc)
            return None

    def process_text(self, text: str, transcription_info: Optional[TranscriptionResult] = None) -> ExecutionResult:
        """Processa um texto, interpreta a intenção e executa a ação segura no Holyrics.

        Args:
            text: Texto do comando ou transcrição.
            transcription_info: Metadados opcionais da transcrição.

        Returns:
            ExecutionResult com diagnóstico completo da execução.
        """
        with self._lock:
            raw_text = (text or "").strip()

            # 1. Se o texto for vazio
            if not raw_text:
                cmd = UnknownCommand(
                    command_type=CommandType.UNKNOWN,
                    raw_text="",
                    reason="Texto vazio recebido para processamento.",
                )
                return ExecutionResult(
                    success=False,
                    raw_text="",
                    command=cmd,
                    action_executed="None",
                    message="Nenhuma fala ou texto detectado.",
                    transcription=transcription_info,
                )

            # 2. Interpretação e Validação Canônica
            cmd = classify_command(raw_text)

            # 3. Bloqueio estrito de UNKNOWN
            if isinstance(cmd, UnknownCommand) or cmd.command_type == CommandType.UNKNOWN:
                logger.info("Comando rejeitado por segurança: '%s' (Motivo: %s)", raw_text, cmd.reason)
                return ExecutionResult(
                    success=False,
                    raw_text=raw_text,
                    command=cmd,
                    action_executed="None",
                    message=f"Comando não reconhecido ou inválido: {cmd.reason}",
                    transcription=transcription_info,
                )

            # 4. Prevenção de duplicação acidental por repetição rápida
            current_time = time.perf_counter()
            cmd_signature = f"{cmd.command_type.value}:{getattr(cmd, 'holyrics_reference', '')}"
            if (
                cmd_signature == self._last_command_str
                and (current_time - self._last_command_time) < self.duplicate_threshold_seconds
            ):
                logger.warning("Comando duplicado ignorado por segurança: %s", cmd_signature)
                return ExecutionResult(
                    success=False,
                    raw_text=raw_text,
                    command=cmd,
                    action_executed="None",
                    message="Comando idêntico ignorado por prevenção de duplicação rápida.",
                    transcription=transcription_info,
                )

            # 5. Execução de Acordo com a Natureza do Comando
            try:
                # ── CASO A: Projeção Bíblica (BIBLE_REFERENCE) ──
                if isinstance(cmd, BibleReferenceCommand):
                    logger.info("Enviando versículo ao Holyrics: '%s'", cmd.holyrics_reference)
                    res = self.api.show_verse(reference=cmd.holyrics_reference)

                    self._last_command_str = cmd_signature
                    self._last_command_time = current_time

                    pres_state = self.get_current_presentation_state()
                    return ExecutionResult(
                        success=True,
                        raw_text=raw_text,
                        command=cmd,
                        action_executed="ShowVerse",
                        message=f"Versículo '{cmd.display_name}' projetado com sucesso na TV!",
                        transcription=transcription_info,
                        holyrics_response=res,
                        current_presentation=pres_state,
                    )

                # ── CASO B: Comandos de Navegação ──
                elif isinstance(cmd, NavigationCommand):
                    # B.1: Limpar Projeção (CLEAR_PRESENTATION)
                    if cmd.command_type == CommandType.CLEAR_PRESENTATION:
                        # REGRA DE SEGURANÇA: só encerra apresentação bíblica
                        pres_before = self.get_current_presentation_state()

                        if pres_before is None:
                            msg = "Nenhuma apresentação ativa para encerrar."
                            logger.info(msg)
                            return ExecutionResult(
                                success=False,
                                raw_text=raw_text,
                                command=cmd,
                                action_executed="None",
                                message=msg,
                                transcription=transcription_info,
                                current_presentation=None,
                            )

                        pres_type_before = str(pres_before.get("type", "")).lower()
                        if pres_type_before != "verse":
                            msg = f"Limpeza bloqueada: a apresentação ativa não é bíblica (tipo: '{pres_type_before}'). Não é seguro fechar."
                            logger.warning(msg)
                            return ExecutionResult(
                                success=False,
                                raw_text=raw_text,
                                command=cmd,
                                action_executed="None",
                                message=msg,
                                transcription=transcription_info,
                                current_presentation=pres_before,
                            )

                        # Apresentação bíblica confirmada — executa encerramento
                        res = self.api.close_current_presentation()
                        self._last_command_str = cmd_signature
                        self._last_command_time = current_time

                        # Confirma encerramento consultando novamente
                        pres_after = self.get_current_presentation_state()
                        pres_type_after = str(pres_after.get("type", "")).lower() if pres_after else ""

                        if pres_after is None or pres_type_after != "verse":
                            return ExecutionResult(
                                success=True,
                                raw_text=raw_text,
                                command=cmd,
                                action_executed="CloseCurrentPresentation",
                                message="Projeção bíblica encerrada com sucesso.",
                                transcription=transcription_info,
                                holyrics_response=res,
                                current_presentation=None,
                            )
                        else:
                            return ExecutionResult(
                                success=False,
                                raw_text=raw_text,
                                command=cmd,
                                action_executed="CloseCurrentPresentation",
                                message="Comando enviado, mas o Holyrics ainda mostra uma apresentação. Resultado inconclusivo.",
                                transcription=transcription_info,
                                holyrics_response=res,
                                current_presentation=pres_after,
                            )

                    # B.2: Próximo ou Anterior (ACTION_NEXT / ACTION_PREVIOUS)
                    # REGRA DE SEGURANÇA CRÍTICA:
                    # Consulta GetCurrentPresentation antes de navegar!
                    pres = self.get_current_presentation_state()

                    if pres is None:
                        msg = "Navegação cancelada: nenhuma apresentação ativa na TV."
                        logger.warning(msg)
                        return ExecutionResult(
                            success=False,
                            raw_text=raw_text,
                            command=cmd,
                            action_executed="None",
                            message=msg,
                            transcription=transcription_info,
                            current_presentation=None,
                        )

                    pres_type = str(pres.get("type", "")).lower()
                    if pres_type != "verse":
                        msg = f"Navegação cancelada: a apresentação ativa não é bíblica (tipo atual: '{pres_type}')."
                        logger.warning(msg)
                        return ExecutionResult(
                            success=False,
                            raw_text=raw_text,
                            command=cmd,
                            action_executed="None",
                            message=msg,
                            transcription=transcription_info,
                            current_presentation=pres,
                        )

                    # Apresentação bíblica ativa confirmada: executa navegação
                    if cmd.command_type == CommandType.ACTION_NEXT:
                        res = self.api.action_next()
                        action_name = "ActionNext"
                        action_desc = "avançado para o próximo versículo"
                    else:
                        res = self.api.action_previous()
                        action_name = "ActionPrevious"
                        action_desc = "retornado para o versículo anterior"

                    self._last_command_str = cmd_signature
                    self._last_command_time = current_time

                    pres_after = self.get_current_presentation_state()
                    active_verse = pres_after.get("name") if pres_after else "TV atualizada"

                    return ExecutionResult(
                        success=True,
                        raw_text=raw_text,
                        command=cmd,
                        action_executed=action_name,
                        message=f"Sucesso: {action_desc} (Exibindo: {active_verse}).",
                        transcription=transcription_info,
                        holyrics_response=res,
                        current_presentation=pres_after,
                    )

                # Fallback de segurança para comandos desconhecidos
                return ExecutionResult(
                    success=False,
                    raw_text=raw_text,
                    command=cmd,
                    action_executed="None",
                    message="Tipo de comando não suportado.",
                    transcription=transcription_info,
                )

            except HolyricsConnectionError as exc:
                msg = f"Holyrics offline ou inacessível: {exc}"
                logger.error(msg)
                return ExecutionResult(
                    success=False,
                    raw_text=raw_text,
                    command=cmd,
                    action_executed="Error",
                    message="Não foi possível conectar ao Holyrics. Verifique se o API Server está ligado.",
                    transcription=transcription_info,
                )
            except HolyricsAuthError as exc:
                msg = f"Erro de autenticação no Holyrics: {exc}"
                logger.error(msg)
                return ExecutionResult(
                    success=False,
                    raw_text=raw_text,
                    command=cmd,
                    action_executed="Error",
                    message="Token do Holyrics inválido. Verifique o config.json.",
                    transcription=transcription_info,
                )
            except HolyricsPermissionError as exc:
                msg = f"Permissão negada no Holyrics: {exc}"
                logger.error(msg)
                return ExecutionResult(
                    success=False,
                    raw_text=raw_text,
                    command=cmd,
                    action_executed="Error",
                    message="Token sem permissão para esta ação no Holyrics.",
                    transcription=transcription_info,
                )
            except HolyricsError as exc:
                msg = f"Erro na API do Holyrics: {exc}"
                logger.error(msg)
                return ExecutionResult(
                    success=False,
                    raw_text=raw_text,
                    command=cmd,
                    action_executed="Error",
                    message=f"Falha ao executar comando no Holyrics: {exc}",
                    transcription=transcription_info,
                )

    def process_audio(self, audio: np.ndarray) -> ExecutionResult:
        """Processa um buffer de áudio (16kHz mono), transcreve e executa no Holyrics.

        Args:
            audio: Array numpy float32.

        Returns:
            ExecutionResult da operação.
        """
        if self.transcriber is None:
            cmd = UnknownCommand(
                command_type=CommandType.UNKNOWN,
                raw_text="",
                reason="Transcritor de voz não foi inicializado no controlador.",
            )
            return ExecutionResult(
                success=False,
                raw_text="",
                command=cmd,
                action_executed="None",
                message="Mecanismo de voz não configurado.",
            )

        # Transcrição via faster-whisper
        t_res = self.transcriber.transcribe(audio, apply_normalization=True)

        if not t_res.text or t_res.is_uncertain:
            reason = "Áudio vazio ou incerteza acústica detectada pelo Whisper."
            cmd = UnknownCommand(
                command_type=CommandType.UNKNOWN,
                raw_text=t_res.text,
                reason=reason,
            )
            return ExecutionResult(
                success=False,
                raw_text=t_res.text,
                command=cmd,
                action_executed="None",
                message=f"Fala não compreendida com segurança suficiente: {reason}",
                transcription=t_res,
            )

        return self.process_text(t_res.text, transcription_info=t_res)
