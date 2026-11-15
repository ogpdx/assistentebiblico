"""
Dicionário dos 66 livros bíblicos com nomes canônicos, abreviações aceitas pelo Holyrics
e variações fonéticas / faladas comuns no português brasileiro.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BookMetadata:
    number: int
    name: str
    abbreviation: str
    aliases: tuple[str, ...] = field(default_factory=tuple)


# Mapeamento completo dos 66 livros da Bíblia protestante padrão (ACF / ARC / NVI).
# As abreviações correspondem às abreviações padrão do Holyrics em português.
BIBLE_BOOKS: list[BookMetadata] = [
    # Antigo Testamento (1 - 39)
    BookMetadata(1, "Gênesis", "Gn", ("genesis", "genisis", "geneses", "livro de genesis")),
    BookMetadata(2, "Êxodo", "Êx", ("exodo", "esodo", "exudo", "livro de exodo")),
    BookMetadata(3, "Levítico", "Lv", ("levitico", "leviticos")),
    BookMetadata(4, "Números", "Nm", ("numeros", "numero")),
    BookMetadata(5, "Deuteronômio", "Dt", ("deuteronomio", "deuteronomios", "deuteronomeo")),
    BookMetadata(6, "Josué", "Js", ("josue", "joshua")),
    BookMetadata(7, "Juízes", "Jz", ("juizes", "juis", "juiz")),
    BookMetadata(8, "Rute", "Rt", ("rute", "ruth")),
    BookMetadata(9, "1 Samuel", "1Sm", ("1 samuel", "primeiro samuel", "primeira samuel", "1º samuel", "1° samuel", "1ª samuel", "1samuel")),
    BookMetadata(10, "2 Samuel", "2Sm", ("2 samuel", "segundo samuel", "segunda samuel", "2º samuel", "2° samuel", "2ª samuel", "2samuel")),
    BookMetadata(11, "1 Reis", "1Rs", ("1 reis", "primeiro reis", "primeira reis", "1º reis", "1° reis", "1ª reis", "1reis", "1 rei", "primeiro rei")),
    BookMetadata(12, "2 Reis", "2Rs", ("2 reis", "segundo reis", "segunda reis", "2º reis", "2° reis", "2ª reis", "2reis", "2 rei", "segundo rei")),
    BookMetadata(13, "1 Crônicas", "1Cr", ("1 cronicas", "primeiro cronicas", "primeira cronicas", "1º cronicas", "1° cronicas", "1ª cronicas", "1cronicas", "1 cronica")),
    BookMetadata(14, "2 Crônicas", "2Cr", ("2 cronicas", "segundo cronicas", "segunda cronicas", "2º cronicas", "2° cronicas", "2ª cronicas", "2cronicas", "2 cronica")),
    BookMetadata(15, "Esdras", "Ed", ("esdras", "esdra")),
    BookMetadata(16, "Neemias", "Ne", ("neemias", "nehemia")),
    BookMetadata(17, "Ester", "Et", ("ester", "esther")),
    BookMetadata(18, "Jó", "Jó", ("jo", "job")),
    BookMetadata(19, "Salmos", "Sl", ("salmos", "salmo", "samos", "os salmos", "o salmo", "livro de salmos", "livro dos salmos", "psalms", "psalm")),
    BookMetadata(20, "Provérbios", "Pv", ("proverbios", "proverbio")),
    BookMetadata(21, "Eclesiastes", "Ec", ("eclesiastes", "eclesiaste")),
    BookMetadata(22, "Cânticos", "Ct", ("canticos", "cantico", "cantares", "cantares de salomao")),
    BookMetadata(23, "Isaías", "Is", ("isaias", "isaia")),
    BookMetadata(24, "Jeremias", "Jr", ("jeremias", "jeremia")),
    BookMetadata(25, "Lamentações", "Lm", ("lamentacoes", "lamentacao", "lamentacoes de jeremias")),
    BookMetadata(26, "Ezequiel", "Ez", ("ezequiel", "ezequiel")),
    BookMetadata(27, "Daniel", "Dn", ("daniel",)),
    BookMetadata(28, "Oséias", "Os", ("oseias", "oseia")),
    BookMetadata(29, "Joel", "Jl", ("joel",)),
    BookMetadata(30, "Amós", "Am", ("amos", "amo")),
    BookMetadata(31, "Obadias", "Ob", ("obadias", "obadia")),
    BookMetadata(32, "Jonas", "Jn", ("jonas", "jona")),
    BookMetadata(33, "Miquéias", "Mq", ("miqueias", "miqueia")),
    BookMetadata(34, "Naum", "Na", ("naum", "naun")),
    BookMetadata(35, "Habacuque", "Hc", ("habacuque", "habacuc", "abacuque")),
    BookMetadata(36, "Sofonias", "Sf", ("sofonias", "sofonia")),
    BookMetadata(37, "Ageu", "Ag", ("ageu", "ageo")),
    BookMetadata(38, "Zacarias", "Zc", ("zacarias", "zacaria")),
    BookMetadata(39, "Malaquias", "Ml", ("malaquias", "malaquia")),

    # Novo Testamento (40 - 66)
    BookMetadata(40, "Mateus", "Mt", ("mateus", "mateo")),
    BookMetadata(41, "Marcos", "Mc", ("marcos", "marco")),
    BookMetadata(42, "Lucas", "Lc", ("lucas", "luca")),
    BookMetadata(43, "João", "Jo", ("joao", "sao joao")),
    BookMetadata(44, "Atos", "At", ("atos", "atos dos apostolos", "ato")),
    BookMetadata(45, "Romanos", "Rm", ("romanos", "romano")),
    BookMetadata(46, "1 Coríntios", "1Co", ("1 corintios", "primeiro corintios", "primeira corintios", "1º corintios", "1° corintios", "1ª corintios", "1corintios", "1 corintio", "primeiro corintio", "1 corinthians", "1º corinthians", "primeiro corinthians", "1corinthians")),
    BookMetadata(47, "2 Coríntios", "2Co", ("2 corintios", "segundo corintios", "segunda corintios", "2º corintios", "2° corintios", "2ª corintios", "2corintios", "2 corintio", "segundo corintio", "2 corinthians", "2º corinthians", "segundo corinthians", "2corinthians")),
    BookMetadata(48, "Gálatas", "Gl", ("galatas", "galata")),
    BookMetadata(49, "Efésios", "Ef", ("efesios", "efesio")),
    BookMetadata(50, "Filipenses", "Fp", ("filipenses", "filipense")),
    BookMetadata(51, "Colossenses", "Cl", ("colossenses", "colossense")),
    BookMetadata(52, "1 Tessalonicenses", "1Ts", ("1 tessalonicenses", "primeiro tessalonicenses", "primeira tessalonicenses", "1º tessalonicenses", "1° tessalonicenses", "1ª tessalonicenses", "1tessalonicenses", "1 tessalonicence", "primeiro tessalonicence")),
    BookMetadata(53, "2 Tessalonicenses", "2Ts", ("2 tessalonicenses", "segundo tessalonicenses", "segunda tessalonicenses", "2º tessalonicenses", "2° tessalonicenses", "2ª tessalonicenses", "2tessalonicenses", "2 tessalonicence", "segundo tessalonicence")),
    BookMetadata(54, "1 Timóteo", "1Tm", ("1 timoteo", "primeiro timoteo", "primeira timoteo", "1º timoteo", "1° timoteo", "1ª timoteo", "1timoteo")),
    BookMetadata(55, "2 Timóteo", "2Tm", ("2 timoteo", "segundo timoteo", "segunda timoteo", "2º timoteo", "2° timoteo", "2ª timoteo", "2timoteo")),
    BookMetadata(56, "Tito", "Tt", ("tito",)),
    BookMetadata(57, "Filemom", "Fm", ("filemom", "filemon")),
    BookMetadata(58, "Hebreus", "Hb", ("hebreus", "hebreu")),
    BookMetadata(59, "Tiago", "Tg", ("tiago", "santiago")),
    BookMetadata(60, "1 Pedro", "1Pe", ("1 pedro", "primeiro pedro", "primeira pedro", "1º pedro", "1° pedro", "1ª pedro", "1pedro")),
    BookMetadata(61, "2 Pedro", "2Pe", ("2 pedro", "segundo pedro", "segunda pedro", "2º pedro", "2° pedro", "2ª pedro", "2pedro")),
    BookMetadata(62, "1 João", "1Jo", ("1 joao", "primeiro joao", "primeira joao", "1º joao", "1° joao", "1ª joao", "1joao")),
    BookMetadata(63, "2 João", "2Jo", ("2 joao", "segundo joao", "segunda joao", "2º joao", "2° joao", "2ª joao", "2joao")),
    BookMetadata(64, "3 João", "3Jo", ("3 joao", "terceiro joao", "terceira joao", "3º joao", "3° joao", "3ª joao", "3joao")),
    BookMetadata(65, "Judas", "Jd", ("judas", "juda")),
    BookMetadata(66, "Apocalipse", "Ap", ("apocalipse", "revelacao")),
]


def find_bible_book(token_sequence: str) -> tuple[BookMetadata | None, str]:
    """Identifica um livro bíblico no início de uma sequência de texto normalizada.

    Retorna uma tupla (BookMetadata, texto_restante) ou (None, texto_original).
    """
    clean_text = token_sequence.strip().lower()

    # Coleta todos os candidatos com seus matches ordenados pelo comprimento do alias decrescente
    # para garantir que '1 corintios' case antes de qualquer outra correspondência menor.
    candidates: list[tuple[int, BookMetadata, str]] = []

    for book in BIBLE_BOOKS:
        abbr_lower = book.abbreviation.lower()
        if clean_text == abbr_lower:
            candidates.append((len(abbr_lower), book, ""))
        elif clean_text.startswith(abbr_lower + " "):
            candidates.append((len(abbr_lower), book, clean_text[len(abbr_lower):].strip()))

        for alias in book.aliases:
            alias_lower = alias.lower()
            if clean_text == alias_lower:
                candidates.append((len(alias_lower), book, ""))
            elif clean_text.startswith(alias_lower + " "):
                candidates.append((len(alias_lower), book, clean_text[len(alias_lower):].strip()))

    if candidates:
        # Pega o match mais longo
        candidates.sort(key=lambda c: c[0], reverse=True)
        return candidates[0][1], candidates[0][2]

    return None, token_sequence
