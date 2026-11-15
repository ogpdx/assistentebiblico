"""
Validador canônico de referências bíblicas.

Aplica o princípio de falha segura:
- Verifica existência do livro (1 a 66).
- Verifica existência do capítulo no livro específico.
- Verifica existência do(s) versículo(s) no capítulo específico.
- Garante integridade de intervalos (verse_start <= verse_end).
- Rejeita referências parciais, inexistentes ou fora dos limites canônicos.
"""

from src.interpreter.canon_data import BIBLE_CANON_CHAPTERS_VERSES


def is_valid_bible_reference(
    book_number: int,
    chapter: int,
    verse_start: int | None = None,
    verse_end: int | None = None,
) -> tuple[bool, str]:
    """Valida se uma referência bíblica existe no cânon bíblico dos 66 livros.

    Returns:
        Tupla (is_valid: bool, reason: str). Se válido, reason é vazia.
    """
    # 1. Valida existência do livro
    if book_number not in BIBLE_CANON_CHAPTERS_VERSES:
        return False, f"Livro com índice {book_number} não existe no cânon bíblico."

    chapters_dict = BIBLE_CANON_CHAPTERS_VERSES[book_number]
    max_chapters = len(chapters_dict)

    # 2. Valida capítulo
    if chapter <= 0:
        return False, f"Capítulo deve ser maior que zero (recebido: {chapter})."

    if chapter > max_chapters:
        return False, f"Capítulo {chapter} inválido para este livro (máximo: {max_chapters})."

    # 3. Se for apenas capítulo (sem versículos), é válido
    if verse_start is None and verse_end is None:
        return True, ""

    max_verses = chapters_dict.get(chapter, 0)

    # 4. Valida versículo inicial
    if verse_start is not None:
        if verse_start <= 0:
            return False, f"Versículo deve ser maior que zero (recebido: {verse_start})."
        if verse_start > max_verses:
            return False, f"Versículo {verse_start} inválido para o capítulo {chapter} (máximo: {max_verses})."

    # 5. Valida versículo final (se for intervalo)
    if verse_end is not None:
        if verse_start is None:
            return False, "Versículo final informado sem versículo inicial."
        if verse_end <= 0:
            return False, f"Versículo final deve ser maior que zero (recebido: {verse_end})."
        if verse_end > max_verses:
            return False, f"Versículo final {verse_end} inválido para o capítulo {chapter} (máximo: {max_verses})."
        if verse_start > verse_end:
            return False, f"Intervalo invertido: versículo inicial ({verse_start}) maior que final ({verse_end})."

    return True, ""
