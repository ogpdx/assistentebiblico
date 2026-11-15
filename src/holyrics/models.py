"""
Modelos de dados para a integração com o Holyrics.

Dataclasses que representam as respostas e objetos da API,
facilitando o acesso tipado aos dados retornados.
"""

from dataclasses import dataclass, field


@dataclass
class BibleVersion:
    """Tradução/versão bíblica disponível no Holyrics.

    Attributes:
        key: Identificador da versão (ex: "pt_arc", "pt_nvi").
        title: Nome completo da tradução (ex: "Almeida Revista e Corrigida").
    """
    key: str
    title: str

    @classmethod
    def from_api(cls, data: dict) -> "BibleVersion":
        """Cria uma instância a partir da resposta da API.

        Args:
            data: Dicionário retornado por GetBibleVersionsV2.
        """
        return cls(
            key=data.get("key", ""),
            title=data.get("title", ""),
        )


@dataclass
class BibleBook:
    """Informações de um livro bíblico.

    Attributes:
        index: Número do livro (1-66).
        name: Nome completo (ex: "Gênesis").
        abbreviation: Abreviação (ex: "Gn").
    """
    index: int
    name: str
    abbreviation: str = ""

    @classmethod
    def from_api(cls, data: dict) -> "BibleBook":
        """Cria uma instância a partir da resposta da API."""
        return cls(
            index=data.get("index", 0),
            name=data.get("name", ""),
            abbreviation=data.get("abbreviation", ""),
        )


@dataclass
class VerseReference:
    """Referência bíblica estruturada.

    Attributes:
        book_number: Número do livro (1-66).
        book_name: Nome do livro.
        chapter: Número do capítulo.
        verse_start: Versículo inicial.
        verse_end: Versículo final (None se for um único versículo).
        version: Versão/tradução bíblica (opcional).
    """
    book_number: int
    book_name: str
    chapter: int
    verse_start: int
    verse_end: int | None = None
    version: str | None = None

    @property
    def verse_id(self) -> str:
        """ID no formato BBCCCVVV para o versículo inicial."""
        return f"{self.book_number:02d}{self.chapter:03d}{self.verse_start:03d}"

    @property
    def verse_ids(self) -> list[str]:
        """Lista de IDs BBCCCVVV para o intervalo de versículos."""
        if self.verse_end is None:
            return [self.verse_id]
        return [
            f"{self.book_number:02d}{self.chapter:03d}{v:03d}"
            for v in range(self.verse_start, self.verse_end + 1)
        ]

    @property
    def display_reference(self) -> str:
        """Referência formatada para exibição (ex: 'João 3:16-18')."""
        ref = f"{self.book_name} {self.chapter}:{self.verse_start}"
        if self.verse_end is not None and self.verse_end != self.verse_start:
            ref += f"-{self.verse_end}"
        return ref

    def __str__(self) -> str:
        return self.display_reference


@dataclass
class HolyricsStatus:
    """Status da conexão com o Holyrics.

    Attributes:
        connected: Se a conexão está ativa.
        version: Versão do Holyrics (se disponível).
        message: Mensagem descritiva do status.
        raw_data: Dados brutos retornados por GetCPInfo.
    """
    connected: bool
    version: str = ""
    message: str = ""
    raw_data: dict = field(default_factory=dict)
