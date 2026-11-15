"""
Construtor e extrator rigoroso de referências bíblicas a partir de texto pré-processado.

Aplica regras explícitas e validação canônica de limites (livro, capítulo, versículos).
Se a referência for inválida, inexistente ou incompleta, descarta e retorna None.
"""

import re
from src.interpreter.bible_books import find_bible_book
from src.interpreter.validator import is_valid_bible_reference
from src.interpreter.models import BibleReferenceCommand, CommandType


def parse_bible_reference(text_with_digits: str, original_raw_text: str = "") -> BibleReferenceCommand | None:
    """Tenta extrair e validar uma referência bíblica de um texto que já teve
    números por extenso convertidos em dígitos decimais.

    Suporta falas naturais onde a referência está no meio ou no final da frase.
    Exemplos:
        'entao la em salmos 23 1' -> Salmos 23:1
        'vamos abrir em joao 3 16' -> João 3:16
        'hoje vamos estudar 1 corintios 13' -> 1 Coríntios 13
        'abra sua biblia em romanos capitulo 8 versiculo 1' -> Romanos 8:1
    """
    clean_text = text_with_digits.strip().lower()
    if not clean_text:
        return None

    # Divide o texto em tokens de palavras
    tokens = clean_text.split()
    total_tokens = len(tokens)

    # Varre as posições dos tokens procurando o início de um livro bíblico
    for i in range(total_tokens):
        sub_phrase = " ".join(tokens[i:])
        book, remainder = find_bible_book(sub_phrase)
        if not book:
            continue

        # Se encontrou um livro, verifica se sobrou algo (capítulo / versículo)
        if not remainder:
            continue

        # Remove palavras de ligação / termos comuns de fala
        remainder_clean = re.sub(r"\b(capitulo|capitulos|cap|versiculo|versiculos|vers|v|versiclo)\b", " ", remainder)
        remainder_clean = re.sub(r"\s+", " ", remainder_clean).strip()

        if not remainder_clean:
            continue

        cap: int | None = None
        v_start: int | None = None
        v_end: int | None = None

        # 2. Padrões estruturados para os números que sucedem o livro:
        # Caso 1: Intervalo: "8 1 ao 4" / "8 do 1 ao 4" / "8 1 ate 4" / "8 de 1 a 4" / "8 1-4"
        range_match = re.search(
            r"^(\d+)\s+(?:(?:do|de)\s+)?(\d+)\s*(?:ao|ate|a|-)\s*(\d+)",
            remainder_clean
        )
        if range_match:
            cap = int(range_match.group(1))
            v_start = int(range_match.group(2))
            v_end = int(range_match.group(3))

        # Caso 2: Capítulo e Versículo: "3 16" / "23 1" / "1 2"
        if cap is None:
            verse_match = re.search(r"^(\d+)\s+(\d+)", remainder_clean)
            if verse_match:
                cap = int(verse_match.group(1))
                v_start = int(verse_match.group(2))
                v_end = None

        # Caso 3: Apenas Capítulo: "23" / "1" / "119" / "13"
        if cap is None:
            chapter_only_match = re.search(r"^(\d+)(?:\s|$)", remainder_clean)
            if chapter_only_match:
                cap = int(chapter_only_match.group(1))
                v_start = None
                v_end = None

        # Se encontrou capítulo e versículo válidos para este livro, valida canonicamente
        if cap is not None:
            is_valid, reason = is_valid_bible_reference(
                book_number=book.number,
                chapter=cap,
                verse_start=v_start,
                verse_end=v_end,
            )
            if is_valid:
                return BibleReferenceCommand(
                    command_type=CommandType.BIBLE_REFERENCE,
                    raw_text=original_raw_text or text_with_digits,
                    book_name=book.name,
                    book_abbreviation=book.abbreviation,
                    book_number=book.number,
                    chapter=cap,
                    verse_start=v_start,
                    verse_end=v_end,
                )

    return None
