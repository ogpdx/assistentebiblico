"""
Script interativo para testar o interpretador de comandos e referências bíblicas
diretamente no terminal via digitação.

Uso:
    python -m scripts.test_interpreter_cli
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.interpreter import (
    classify_command,
    CommandType,
    BibleReferenceCommand,
    NavigationCommand,
    UnknownCommand,
)


def main():
    print("=" * 65)
    print("  INTERPRETADOR BÍBLICO — MODO DE TESTE INTERATIVO")
    print("=" * 65)
    print("Digite frases como se fossem a fala do pastor.")
    print("Digite 'sair' para encerrar.\n")

    exemplos = [
        "Salmos, 23, 1",
        "João 1316 (invalido)",
        "João 3:16",
        "Salmos 151 (invalido)",
        "Primeiro Coríntios, capítulo 13, versículo 4",
        "1º Corinthians, capítulo 13, versículo 4",
        "Segundo Reis, capítulo 1, versículo 1",
        "Primeiro Salmo (invalido)",
        "Próximo versículo",
        "Limpar projeção",
    ]
    print("Exemplos sugeridos:")
    for ex in exemplos:
        print(f"  • {ex}")
    print("-" * 65)

    while True:
        try:
            texto = input("\nFale ou digite: ").strip()
        except (KeyboardInterrupt, EOFError):
            break

        if not texto:
            continue
        if texto.lower() in ("sair", "exit", "quit"):
            break

        cmd = classify_command(texto)

        print("\nResultado da Interpretação:")
        print(f"  Tipo do Comando : {cmd.command_type.value}")

        if isinstance(cmd, BibleReferenceCommand):
            print(f"  Livro           : {cmd.book_name} (nº {cmd.book_number})")
            print(f"  Capítulo        : {cmd.chapter}")
            print(f"  Versículo(s)    : {cmd.verse_start}" + (f" até {cmd.verse_end}" if cmd.verse_end else ""))
            print(f"  Payload Holyrics: '{cmd.holyrics_reference}'")
            print(f"  Exibição UI     : '{cmd.display_name}'")
        elif isinstance(cmd, NavigationCommand):
            print(f"  Ação Mapeada    : API {cmd.command_type.value}")
        elif isinstance(cmd, UnknownCommand):
            print(f"  Motivo / Recusa : {cmd.reason}")

    print("\nEncerrado.")


if __name__ == "__main__":
    main()
