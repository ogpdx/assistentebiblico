"""
Consulta as abreviações oficiais de livros bíblicos aceitas pelo Holyrics.

Uso:
    python -m scripts.fetch_bible_books

Salva o resultado em data/holyrics_bible_books.json para referência.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import Settings
from src.core.logging_config import setup_logging
from src.holyrics.client import HolyricsClient
from src.holyrics.api import HolyricsAPI
from src.holyrics.exceptions import HolyricsError

import logging
setup_logging(level=logging.WARNING)


def main() -> None:
    settings = Settings("config.json")
    client = HolyricsClient(
        host=settings.holyrics_host,
        port=settings.holyrics_port,
        token=settings.holyrics_token,
    )
    api = HolyricsAPI(client)

    print("Consultando livros bíblicos no Holyrics (language_id='pt')...\n")

    try:
        books = api.get_bible_books(language_id="pt")
    except HolyricsError as e:
        print(f"Erro: {e}")
        print("Tente verificar se o token tem permissão para GetBibleBooks.")
        client.close()
        sys.exit(1)

    if not books:
        print("Nenhum livro retornado. Verifique o Holyrics.")
        client.close()
        sys.exit(1)

    print(f"{len(books)} livros encontrados:\n")
    print(f"{'#':>3}  {'Abreviação':<10}  {'Nome'}")
    print("-" * 50)
    for b in books:
        idx = b.get("number", b.get("index", "?"))
        abbr = b.get("abbreviation", b.get("abbrev", "?"))
        name = b.get("name", "?")
        print(f"{idx:>3}  {abbr:<10}  {name}")

    # Salva em arquivo JSON para referência
    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "holyrics_bible_books.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(books, f, indent=2, ensure_ascii=False)

    print(f"\nDados salvos em {output_path}")
    client.close()


if __name__ == "__main__":
    main()
