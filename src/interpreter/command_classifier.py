"""
Classificador de comandos de voz do Assistente Bíblico.

Recebe um texto transcrito e orquestra a normalização,
conversão de números e classificação em:
- Navegação (ACTION_NEXT, ACTION_PREVIOUS, CLEAR_PRESENTATION)
- Projeção Bíblica (BIBLE_REFERENCE)
- Não reconhecido (UNKNOWN)
"""

import re
from src.interpreter.normalizer import normalize_text
from src.interpreter.number_converter import convert_spoken_numbers_in_text
from src.interpreter.reference_builder import parse_bible_reference
from src.interpreter.models import (
    CommandType,
    InterpretedCommand,
    NavigationCommand,
    UnknownCommand,
)

# Padrões de expressões para comandos de navegação rápida
# REQUISITO DE SEGURANÇA OPERACIONAL:
# Não aceitar palavras genéricas isoladas como "voltar", "avançar" ou "fechar".
# Exigir comandos compostos e intencionais para prevenir disparos acidentais durante o culto.
NEXT_PATTERNS = [
    r"^proximo versiculo$",
    r"^avancar versiculo$",
    r"^avanca versiculo$",
    r"^proximo slide$",
]

PREV_PATTERNS = [
    r"^versiculo anterior$",
    r"^voltar versiculo$",
    r"^volta versiculo$",
    r"^retroceder versiculo$",
    r"^slide anterior$",
]

CLEAR_PATTERNS = [
    r"^limpar projecao$",
    r"^limpar tela$",
    r"^parar projecao$",
    r"^encerrar projecao$",
    r"^fechar projecao$",
    r"^fechar apresentacao$",
    r"^apagar tela$",
    r"^tirar da tela$",
]


def classify_command(raw_text: str) -> InterpretedCommand:
    """Interpreta um comando de fala natural do pastor/operador.

    Args:
        raw_text: Texto obtido do reconhecimento de voz.

    Returns:
        Instância de InterpretedCommand (NavigationCommand, BibleReferenceCommand ou UnknownCommand).
    """
    if not raw_text or not raw_text.strip():
        return UnknownCommand(
            command_type=CommandType.UNKNOWN,
            raw_text="",
            reason="Texto de entrada vazio."
        )

    # 1. Normalização básica
    normalized = normalize_text(raw_text, strip_accents=True)

    # 2. Testa se é comando de navegação imediata
    for pat in NEXT_PATTERNS:
        if re.search(pat, normalized):
            return NavigationCommand(
                command_type=CommandType.ACTION_NEXT,
                raw_text=raw_text
            )

    for pat in PREV_PATTERNS:
        if re.search(pat, normalized):
            return NavigationCommand(
                command_type=CommandType.ACTION_PREVIOUS,
                raw_text=raw_text
            )

    for pat in CLEAR_PATTERNS:
        if re.search(pat, normalized):
            return NavigationCommand(
                command_type=CommandType.CLEAR_PRESENTATION,
                raw_text=raw_text
            )

    # 3. Conversão de números falados por extenso para dígitos
    text_with_digits = convert_spoken_numbers_in_text(normalized)

    # 4. Tenta interpretar como referência bíblica
    bible_cmd = parse_bible_reference(text_with_digits, original_raw_text=raw_text)
    if bible_cmd:
        return bible_cmd

    # 5. Se não atendeu a nenhum padrão, retorna UNKNOWN
    return UnknownCommand(
        command_type=CommandType.UNKNOWN,
        raw_text=raw_text,
        reason=f"A frase '{raw_text}' não corresponde a uma referência bíblica ou comando reconhecido."
    )
