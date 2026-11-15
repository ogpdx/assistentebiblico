"""
Conversor rigoroso de números falados por extenso em português para inteiros.

Regras e garantias de segurança:
- Números que já estão em dígitos (ex: "23", "1", "16") são preservados como entidades independentes.
  NUNCA são somados nem concatenados entre si!
- Sequências por extenso (ex: "vinte e três", "cento e dezenove") são agrupadas apenas quando
  seguem estritamente a gramática decrescente da língua portuguesa:
    [CENTENA] [e] [DEZENA ou 10-19] [e] [UNIDADE]
- Palavras numéricas não compostas e contíguas (ex: "três" seguido de "dezesseis") são convertidas
  em números separados ("3" e "16"), sem agregação ou soma indevida.
"""

import re

UNIDADES: dict[str, int] = {
    "zero": 0,
    "um": 1,
    "uma": 1,
    "dois": 2,
    "duas": 2,
    "tres": 3,
    "três": 3,
    "quatro": 4,
    "cinco": 5,
    "seis": 6,
    "sete": 7,
    "oito": 8,
    "nove": 9,
}

ORDINAIS: dict[str, int] = {
    "primeiro": 1,
    "primeira": 1,
    "segundo": 2,
    "segunda": 2,
    "terceiro": 3,
    "terceira": 3,
    "quarto": 4,
    "quarta": 4,
}

ESPECIAIS_10_A_19: dict[str, int] = {
    "dez": 10,
    "onze": 11,
    "doze": 12,
    "treze": 13,
    "quatorze": 14,
    "catorze": 14,
    "quinze": 15,
    "dezesseis": 16,
    "dezessete": 17,
    "dezoito": 18,
    "dezenove": 19,
}

DEZENAS: dict[str, int] = {
    "vinte": 20,
    "trinta": 30,
    "quarenta": 40,
    "cinquenta": 50,
    "cinqüenta": 50,
    "sessenta": 60,
    "setenta": 70,
    "oitenta": 80,
    "noventa": 90,
}

CENTENAS: dict[str, int] = {
    "cem": 100,
    "cento": 100,
    "duzentos": 200,
    "duzentas": 200,
    "trezentos": 300,
    "trezentas": 300,
    "quatrocentos": 400,
    "quatrocentas": 400,
    "quinhentos": 500,
    "quinhentas": 500,
    "seiscentos": 600,
    "seiscentas": 600,
    "setecentos": 700,
    "setecentas": 700,
    "oitocentos": 800,
    "oitocentas": 800,
    "novecentos": 900,
    "novecentas": 900,
}


def parse_single_number_word(word: str) -> tuple[int | None, str | None]:
    """Identifica o valor e a categoria de uma única palavra numérica.

    Categorias: 'C' (centena), 'D' (dezena 20-90), 'T' (10-19), 'U' (unidade 0-9), 'O' (ordinal).
    """
    if word in CENTENAS:
        return CENTENAS[word], "C"
    if word in DEZENAS:
        return DEZENAS[word], "D"
    if word in ESPECIAIS_10_A_19:
        return ESPECIAIS_10_A_19[word], "T"
    if word in UNIDADES:
        return UNIDADES[word], "U"
    if word in ORDINAIS:
        return ORDINAIS[word], "O"
    return None, None


def convert_spoken_numbers_in_text(text: str) -> str:
    """Substitui palavras por extenso que formam números pelos seus respectivos valores decimais.

    Garante que:
    - Dígitos existentes permaneçam intocados.
    - 'vinte e tres' -> '23'
    - 'cento e dezenove' -> '119'
    - 'joao tres dezesseis' -> 'joao 3 16' (não soma 3 + 16!)
    - 'salmos 23 1' -> 'salmos 23 1' (não soma 23 + 1!)
    """
    tokens = text.split()
    if not tokens:
        return ""

    output_tokens: list[str] = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        # Se o token já for puramente dígito decimal, preserva-o intacto
        if tok.isdigit():
            output_tokens.append(tok)
            i += 1
            continue

        val, cat = parse_single_number_word(tok)
        if val is None:
            # Não é palavra numérica
            output_tokens.append(tok)
            i += 1
            continue

        # É uma palavra numérica. Tenta expandir número composto legítimo
        # Gramática permitida de composição:
        # 1. Ordinal isolado: não se compõe com nada
        if cat == "O":
            output_tokens.append(str(val))
            i += 1
            continue

        # 2. Centena (C)
        if cat == "C":
            # "cem" isolado
            if tok == "cem":
                output_tokens.append("100")
                i += 1
                continue

            current_num = val
            j = i + 1
            # Pode vir "e" seguido de D, T ou U
            if j < n and tokens[j] == "e":
                next_val, next_cat = parse_single_number_word(tokens[j + 1]) if j + 1 < n else (None, None)
                if next_cat in ("D", "T", "U"):
                    current_num += next_val
                    j += 2
                    # Se era D (ex: "cento e vinte"), pode vir ainda "e" + U (ex: "e tres")
                    if next_cat == "D" and j < n and tokens[j] == "e":
                        u_val, u_cat = parse_single_number_word(tokens[j + 1]) if j + 1 < n else (None, None)
                        if u_cat == "U":
                            current_num += u_val
                            j += 2
                    output_tokens.append(str(current_num))
                    i = j
                    continue

            output_tokens.append(str(current_num))
            i += 1
            continue

        # 3. Dezena (D) 20 a 90
        if cat == "D":
            current_num = val
            j = i + 1
            # Pode vir "e" seguido de U
            if j < n and tokens[j] == "e":
                next_val, next_cat = parse_single_number_word(tokens[j + 1]) if j + 1 < n else (None, None)
                if next_cat == "U":
                    current_num += next_val
                    output_tokens.append(str(current_num))
                    i = j + 2
                    continue

            output_tokens.append(str(current_num))
            i += 1
            continue

        # 4. T (10-19) ou U (0-9) isolados
        output_tokens.append(str(val))
        i += 1

    return " ".join(output_tokens)
