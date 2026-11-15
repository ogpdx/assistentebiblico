"""
Testes automatizados da auditoria e correção da ETAPA 2 — Interpretador de Comandos e Referências Bíblicas.
"""

import pytest
from src.interpreter import (
    classify_command,
    CommandType,
    BibleReferenceCommand,
    NavigationCommand,
    UnknownCommand,
    normalize_text,
    convert_spoken_numbers_in_text,
    is_valid_bible_reference,
)


class TestBugFixesAudit:
    """Testes específicos para os bugs identificados na auditoria de voz."""

    def test_caso_a_salmos_23_1_nao_deve_somar_para_24(self):
        """Salmos, 23, 1 não pode somar 23+1=24, deve gerar Sl 23:1."""
        cmd = classify_command("Salmos, 23, 1.")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "Salmos"
        assert cmd.book_abbreviation == "Sl"
        assert cmd.chapter == 23
        assert cmd.verse_start == 1
        assert cmd.holyrics_reference == "Sl 23:1"

    def test_caso_b_joao_1316_invalido_deve_retornar_unknown(self):
        """João 1316 não existe no cânon (João só tem 21 caps), deve retornar UNKNOWN."""
        cmd = classify_command("João 1316.")
        assert isinstance(cmd, UnknownCommand)
        assert cmd.command_type == CommandType.UNKNOWN

    def test_preservacao_de_digitos_sem_soma(self):
        """Garante que 'convert_spoken_numbers_in_text' não some dígitos adjacentes."""
        res = convert_spoken_numbers_in_text("salmos 23 1")
        assert res == "salmos 23 1"

        res2 = convert_spoken_numbers_in_text("joao 3 16")
        assert res2 == "joao 3 16"


class TestMandatoryAuditCases:
    """Casos de teste explicitamente exigidos pelo usuário na auditoria."""

    def test_salmos_23(self):
        cmd = classify_command("Salmos, 23")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.holyrics_reference == "Sl 23"

    def test_salmo_23(self):
        cmd = classify_command("Salmo, 23")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.holyrics_reference == "Sl 23"

    def test_salmos_23_1_com_pontuacao(self):
        cmd = classify_command("Salmos, 23, 1")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.holyrics_reference == "Sl 23:1"

    def test_salmos_capitulo_23_versiculo_1(self):
        cmd = classify_command("Salmos, capítulo 23, versículo 1")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.holyrics_reference == "Sl 23:1"

    def test_joao_1316(self):
        cmd = classify_command("João 1316")
        assert isinstance(cmd, UnknownCommand)
        assert cmd.command_type == CommandType.UNKNOWN

    def test_joao_3_16(self):
        cmd = classify_command("João 3:16")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.holyrics_reference == "Jo 3:16"

    def test_joao_capitulo_3_versiculo_16(self):
        cmd = classify_command("João, capítulo 3, versículo 16")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.holyrics_reference == "Jo 3:16"

    def test_primeiro_corintios_capitulo_13_versiculo_4(self):
        cmd = classify_command("Primeiro Coríntios, capítulo 13, versículo 4")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "1 Coríntios"
        assert cmd.book_abbreviation == "1Co"
        assert cmd.chapter == 13
        assert cmd.verse_start == 4
        assert cmd.holyrics_reference == "1Co 13:4"

    def test_1_corinthians_capitulo_13_versiculo_4(self):
        cmd = classify_command("1º Corinthians, capítulo 13, versículo 4")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "1 Coríntios"
        assert cmd.book_abbreviation == "1Co"
        assert cmd.chapter == 13
        assert cmd.verse_start == 4
        assert cmd.holyrics_reference == "1Co 13:4"

    def test_segundo_reis_capitulo_1_versiculo_1(self):
        cmd = classify_command("Segundo Reis, capítulo 1, versículo 1")
        assert isinstance(cmd, BibleReferenceCommand)
        assert cmd.book_name == "2 Reis"
        assert cmd.book_abbreviation == "2Rs"
        assert cmd.chapter == 1
        assert cmd.verse_start == 1
        assert cmd.holyrics_reference == "2Rs 1:1"

    def test_primeiro_salmo_deve_ser_unknown(self):
        """'Primeiro Salmo' sem capítulo não é referência completa -> UNKNOWN."""
        cmd = classify_command("Primeiro Salmo")
        assert isinstance(cmd, UnknownCommand)
        assert cmd.command_type == CommandType.UNKNOWN

    def test_salmos_151_deve_ser_unknown(self):
        """Salmos tem 150 capítulos no cânon protestante de 66 livros. 151 -> UNKNOWN."""
        cmd = classify_command("Salmos 151")
        assert isinstance(cmd, UnknownCommand)
        assert cmd.command_type == CommandType.UNKNOWN

    def test_joao_3_999_deve_ser_unknown(self):
        """João 3 só tem 36 versículos. 999 -> UNKNOWN."""
        cmd = classify_command("João 3:999")
        assert isinstance(cmd, UnknownCommand)
        assert cmd.command_type == CommandType.UNKNOWN


class TestCanonValidatorLimits:
    """Testa os limites reais de livros e capítulos."""

    def test_livro_inexistente(self):
        is_val, reason = is_valid_bible_reference(99, 1, 1)
        assert not is_val

    def test_capitulo_zero_ou_negativo(self):
        is_val, _ = is_valid_bible_reference(1, 0, 1)
        assert not is_val
        is_val, _ = is_valid_bible_reference(1, -1, 1)
        assert not is_val

    def test_judas_capitulo_unico(self):
        # Judas (65) só tem 1 capítulo com 25 versículos
        assert is_valid_bible_reference(65, 1, 1)[0] is True
        assert is_valid_bible_reference(65, 1, 25)[0] is True
        assert is_valid_bible_reference(65, 1, 26)[0] is False  # V26 não existe
        assert is_valid_bible_reference(65, 2, 1)[0] is False   # Cap 2 não existe

    def test_intervalo_invertido(self):
        # Versículo inicial maior que final (ex: Rm 8:5-2)
        assert is_valid_bible_reference(45, 8, verse_start=5, verse_end=2)[0] is False


class TestConversasComunsRejeitadas:
    """Garante que conversas comuns de culto nunca gerem comandos ShowVerse."""

    def test_frases_do_culto(self):
        frases = [
            "A paz do Senhor Jesus meus irmãos",
            "Glória a Deus aleluia",
            "Vamos ficar em pé para orar",
            "Abra a sua Bíblia nesta noite",
            "Deus é fiel",
            "Boa noite a todos os irmãos",
            "Amém",
            "O senhor é bom",
            "Segunda feira teremos culto de oração",  # 'segunda' não deve acionar 2 Reis/2 Coríntios sem livro
            "Primeiro vamos orar",                   # 'primeiro' isolado
        ]
        for f in frases:
            cmd = classify_command(f)
            assert isinstance(cmd, UnknownCommand), f"Falha na frase: '{f}' retornou {cmd}"


class TestComandosNavegacaoSeguros:
    """Garante que comandos de navegação precisam ser explícitos."""

    def test_comandos_validos(self):
        assert classify_command("Próximo versículo").command_type == CommandType.ACTION_NEXT
        assert classify_command("Versículo anterior").command_type == CommandType.ACTION_PREVIOUS
        assert classify_command("Limpar projeção").command_type == CommandType.CLEAR_PRESENTATION
        assert classify_command("Limpar tela").command_type == CommandType.CLEAR_PRESENTATION

    def test_palavras_genericas_rejeitadas(self):
        assert isinstance(classify_command("voltar"), UnknownCommand)
        assert isinstance(classify_command("avançar"), UnknownCommand)
        assert isinstance(classify_command("limpar"), UnknownCommand)
        assert isinstance(classify_command("fechar"), UnknownCommand)
        assert isinstance(classify_command("próximo"), UnknownCommand)
        assert isinstance(classify_command("anterior"), UnknownCommand)
