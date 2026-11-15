"""
Modelos e construtores de comandos e referências bíblicas estruturadas.

Define os objetos de resultado que serão devolvidos ao controlador:
- NavigationCommand (ACTION_NEXT, ACTION_PREVIOUS, CLEAR_PRESENTATION)
- BibleReferenceCommand (Livro, capítulo, versículos)
- UnknownCommand (quando a intenção não for compreendida)
"""

from dataclasses import dataclass
from enum import Enum


class CommandType(str, Enum):
    BIBLE_REFERENCE = "BIBLE_REFERENCE"
    ACTION_NEXT = "ACTION_NEXT"
    ACTION_PREVIOUS = "ACTION_PREVIOUS"
    CLEAR_PRESENTATION = "CLEAR_PRESENTATION"
    UNKNOWN = "UNKNOWN"


@dataclass
class InterpretedCommand:
    """Classe base para comandos interpretados."""
    command_type: CommandType
    raw_text: str
    confidence: float = 1.0


@dataclass
class NavigationCommand(InterpretedCommand):
    """Comando de navegação simples (Próximo, Anterior, Limpar)."""
    pass


@dataclass
class BibleReferenceCommand(InterpretedCommand):
    """Comando de projeção de uma referência bíblica estruturada."""
    book_name: str = ""
    book_abbreviation: str = ""
    book_number: int = 0
    chapter: int = 0
    verse_start: int | None = None
    verse_end: int | None = None

    @property
    def holyrics_reference(self) -> str:
        """Monta a string de referência no formato otimizado e aceito pelo Holyrics.

        Exemplos:
            - Jo 3:16
            - 1Rs 1:2
            - Sl 23
            - Rm 8:1-4
        """
        ref = f"{self.book_abbreviation} {self.chapter}"
        if self.verse_start is not None:
            ref += f":{self.verse_start}"
            if self.verse_end is not None and self.verse_end != self.verse_start:
                ref += f"-{self.verse_end}"
        return ref

    @property
    def display_name(self) -> str:
        """Formato amigável por extenso para exibição ao usuário na interface."""
        ref = f"{self.book_name} {self.chapter}"
        if self.verse_start is not None:
            ref += f":{self.verse_start}"
            if self.verse_end is not None and self.verse_end != self.verse_start:
                ref += f"-{self.verse_end}"
        return ref


@dataclass
class UnknownCommand(InterpretedCommand):
    """Comando não reconhecido ou ambíguo."""
    reason: str = "Não foi possível identificar uma referência bíblica ou comando de navegação válido."
