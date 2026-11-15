"""
Normalizador de texto para transcrições de áudio.

Limpa e padroniza a entrada do usuário:
- Converte para minúsculas.
- Converte pontuações que atuam como delimitadores (vírgulas, pontos, dois-pontos, ponto-e-vírgula)
  em espaços protegidos.
- Preserva hífens em intervalos ou os normaliza adequadamente.
- Normaliza caracteres ordinais (1º, 1ª, 2º, 2ª, 1°, 2°).
- Remove espaços duplicados e nas bordas.
"""

import re
import unicodedata


def remove_accents(text: str) -> str:
    """Remove acentos de uma string, mantendo caracteres alfanuméricos básicos.

    Ex: 'Gênesis' -> 'Genesis', 'João' -> 'Joao'
    """
    normalized = unicodedata.normalize("NFD", text)
    return "".join(c for c in normalized if unicodedata.category(c) != "Mn")


def normalize_text(text: str, strip_accents: bool = False) -> str:
    """Normaliza o texto transcrito para interpretação.

    Args:
        text: Texto bruto vindo do reconhecimento de voz ou digitação.
        strip_accents: Se True, remove acentos gráficos.

    Returns:
        Texto limpo e padronizado.
    """
    if not text:
        return ""

    text = text.lower().strip()

    # Normaliza ordinais com símbolos para padrão uniforme
    # Ex: '1º', '1°', '1ª' -> '1'
    text = re.sub(r"\b1[º°ªa]\b", "1", text)
    text = re.sub(r"\b2[º°ªa]\b", "2", text)
    text = re.sub(r"\b3[º°ªa]\b", "3", text)

    # Substitui dois pontos (ex: '3:16') por espaço delimitador: '3 16'
    text = re.sub(r":", " ", text)

    # Substitui pontuações comuns de transcrição por espaço
    text = re.sub(r"[,;!\?\(\)\[\]\{\}\"\'\/\\~^`´]", " ", text)

    # Ponto final que não seja número decimal
    text = re.sub(r"\.", " ", text)

    # Opcional: remover acentos
    if strip_accents:
        text = remove_accents(text)

    # Normaliza múltiplos espaços
    text = re.sub(r"\s+", " ", text).strip()

    return text
