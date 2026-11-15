"""
Script independente para testar a conexão com o Holyrics API Server.

Este script verifica:
1. Se o Holyrics está acessível.
2. Se o token de autenticação é válido.
3. Quais traduções bíblicas estão instaladas.
4. Se é possível projetar um versículo de teste.
5. Se é possível fechar a apresentação.

Uso:
    python -m scripts.test_holyrics_connection
    python -m scripts.test_holyrics_connection --host localhost --port 8091 --token SEU_TOKEN
    python -m scripts.test_holyrics_connection --send-verse "João 3:16"

Pré-requisitos:
    1. Holyrics deve estar aberto.
    2. API Server habilitado em: Arquivo > Configurações > API Server.
    3. Token criado em: API Server > Gerenciar Permissões.
    4. config.json deve conter host, porta e token (ou passar via argumentos).
"""

import argparse
import json
import sys
import os

# Adiciona o diretório raiz ao path para imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import Settings
from src.core.logging_config import setup_logging
from src.holyrics.client import HolyricsClient
from src.holyrics.api import HolyricsAPI
from src.holyrics.exceptions import (
    HolyricsAuthError,
    HolyricsConnectionError,
    HolyricsPermissionError,
    HolyricsTimeoutError,
    HolyricsAPIError,
)


# ──────────────────────────────────────────────
# Formatação do terminal
# ──────────────────────────────────────────────

def _ok(msg: str) -> str:
    return f"  [OK] {msg}"


def _fail(msg: str) -> str:
    return f"  [FALHA] {msg}"


def _info(msg: str) -> str:
    return f"  [INFO] {msg}"


def _header(msg: str) -> str:
    return f"\n{'='*60}\n  {msg}\n{'='*60}"


# ──────────────────────────────────────────────
# Testes
# ──────────────────────────────────────────────

def test_connection(api: HolyricsAPI) -> bool:
    """Teste 1: Conexão básica com GetCPInfo."""
    print(_header("TESTE 1: Conexão com o Holyrics"))

    status = api.get_status()
    if status.connected:
        print(_ok(f"Conectado ao Holyrics!"))
        if status.version:
            print(_info(f"Versão: {status.version}"))
        if status.raw_data:
            print(_info(f"Dados do sistema: {json.dumps(status.raw_data, indent=2, ensure_ascii=False)[:500]}"))
        return True
    else:
        print(_fail(f"Não foi possível conectar: {status.message}"))
        print()
        print("  Verifique:")
        print("    1. O Holyrics está aberto?")
        print("    2. O API Server está habilitado?")
        print("       (Arquivo > Configurações > API Server)")
        print("    3. O endereço e a porta estão corretos?")
        print("    4. O firewall permite a conexão?")
        return False


def test_bible_versions(api: HolyricsAPI) -> bool:
    """Teste 2: Listar traduções bíblicas."""
    print(_header("TESTE 2: Traduções Bíblicas Instaladas"))

    try:
        versions = api.get_bible_versions()
        if versions:
            print(_ok(f"{len(versions)} tradução(ões) encontrada(s):"))
            for v in versions:
                print(f"    • {v.key}: {v.title}")
            return True
        else:
            print(_info("Nenhuma tradução encontrada."))
            print("  Isso pode indicar que nenhuma Bíblia está instalada no Holyrics.")
            return True  # Não é necessariamente uma falha
    except HolyricsPermissionError:
        print(_fail("Token sem permissão para GetBibleVersionsV2."))
        print("  Configure a permissão em: API Server > Gerenciar Permissões.")
        return False
    except Exception as e:
        print(_fail(f"Erro: {e}"))
        return False


def test_show_verse(api: HolyricsAPI, reference: str = "João 3:16") -> bool:
    """Teste 3: Projetar um versículo."""
    print(_header(f"TESTE 3: Projetar Versículo — {reference}"))

    try:
        result = api.show_verse(reference=reference)
        status = result.get("status", "")
        if status == "ok":
            print(_ok(f"Versículo '{reference}' projetado com sucesso!"))
            print(_info("Verifique a tela de projeção do Holyrics."))
            return True
        else:
            print(_fail(f"Resposta inesperada: {result}"))
            return False
    except HolyricsPermissionError:
        print(_fail("Token sem permissão para ShowVerse."))
        return False
    except HolyricsAPIError as e:
        print(_fail(f"Erro da API: {e}"))
        print(_info("A referência pode não ter sido reconhecida pelo Holyrics."))
        return False
    except Exception as e:
        print(_fail(f"Erro: {e}"))
        return False


def test_close_presentation(api: HolyricsAPI) -> bool:
    """Teste 4: Fechar a apresentação atual."""
    print(_header("TESTE 4: Fechar Apresentação"))

    try:
        result = api.close_current_presentation()
        status = result.get("status", "")
        if status == "ok":
            print(_ok("Apresentação fechada com sucesso."))
            return True
        else:
            print(_fail(f"Resposta inesperada: {result}"))
            return False
    except HolyricsPermissionError:
        print(_fail("Token sem permissão para CloseCurrentPresentation."))
        return False
    except Exception as e:
        print(_fail(f"Erro: {e}"))
        return False


def test_show_verse_by_id(api: HolyricsAPI) -> bool:
    """Teste 5: Projetar versículo por ID (BBCCCVVV)."""
    print(_header("TESTE 5: Projetar Versículo por ID (João 3:16 = 43003016)"))

    try:
        result = api.show_verse(verse_id="43003016")
        status = result.get("status", "")
        if status == "ok":
            print(_ok("Versículo projetado por ID com sucesso!"))
            return True
        else:
            print(_fail(f"Resposta inesperada: {result}"))
            return False
    except Exception as e:
        print(_fail(f"Erro: {e}"))
        return False


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Testa a conexão com o Holyrics API Server.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  python -m scripts.test_holyrics_connection
  python -m scripts.test_holyrics_connection --host 192.168.1.100 --port 8091 --token abc123
  python -m scripts.test_holyrics_connection --send-verse "Salmos 23:1"
  python -m scripts.test_holyrics_connection --skip-verse
        """,
    )
    parser.add_argument("--host", help="Endereço do Holyrics (sobrescreve config.json)")
    parser.add_argument("--port", type=int, help="Porta do API Server (sobrescreve config.json)")
    parser.add_argument("--token", help="Token de autenticação (sobrescreve config.json)")
    parser.add_argument("--send-verse", default="João 3:16", help="Referência bíblica para teste (padrão: João 3:16)")
    parser.add_argument("--skip-verse", action="store_true", help="Pular o teste de projeção de versículo")
    parser.add_argument("--config", default="config.json", help="Caminho do arquivo de configuração")
    parser.add_argument("--verbose", action="store_true", help="Ativar logs detalhados")

    args = parser.parse_args()

    # Configura logging
    import logging
    setup_logging(level=logging.DEBUG if args.verbose else logging.WARNING)

    # Carrega configurações
    settings = Settings(args.config)

    # Argumentos da linha de comando sobrescrevem config.json
    host = args.host or settings.holyrics_host
    port = args.port or settings.holyrics_port
    token = args.token or settings.holyrics_token

    print(_header("TESTE DE CONEXÃO — HOLYRICS API SERVER"))
    print(f"  Endereço: {host}:{port}")
    print(f"  Token: {'***configurado***' if token else '(NÃO CONFIGURADO)'}")
    print(f"  Config: {args.config}")

    if not token:
        print()
        print("  ⚠️  Token não configurado!")
        print()
        print("  Para configurar:")
        print("    1. Abra o Holyrics.")
        print("    2. Vá em: Arquivo > Configurações > API Server.")
        print("    3. Habilite o API Server Local.")
        print("    4. Clique em 'Gerenciar Permissões'.")
        print("    5. Crie um novo token.")
        print("    6. Copie o token para config.json ou use --token.")
        print()
        sys.exit(1)

    # Cria cliente e API
    client = HolyricsClient(host=host, port=port, token=token)
    api = HolyricsAPI(client)

    results = []

    # Teste 1: Conexão
    connected = test_connection(api)
    results.append(("Conexão", connected))

    if not connected:
        print()
        print("="*60)
        print("  RESULTADO: Conexão falhou. Testes subsequentes cancelados.")
        print("="*60)
        client.close()
        sys.exit(1)

    # Teste 2: Traduções bíblicas
    results.append(("Traduções bíblicas", test_bible_versions(api)))

    # Teste 3: Projetar versículo
    if not args.skip_verse:
        results.append(("Projetar versículo (referência)", test_show_verse(api, args.send_verse)))

        # Pequena pausa para visualizar o versículo
        import time
        time.sleep(2)

        # Teste 4: Fechar apresentação
        results.append(("Fechar apresentação", test_close_presentation(api)))

        time.sleep(1)

        # Teste 5: Projetar por ID
        results.append(("Projetar versículo (ID)", test_show_verse_by_id(api)))

        time.sleep(2)

        # Fecha novamente
        test_close_presentation(api)

    # Resumo
    print(_header("RESUMO DOS TESTES"))
    total = len(results)
    passed = sum(1 for _, ok in results if ok)

    for name, ok in results:
        status_str = "[OK]" if ok else "[FALHA]"
        print(f"  {status_str:>8}  {name}")

    print()
    print(f"  Resultado: {passed}/{total} testes passaram.")

    if passed == total:
        print()
        print("  ✅ Integração com o Holyrics validada com sucesso!")
        print("  O Assistente Bíblico está pronto para projetar versículos.")
    else:
        print()
        print("  ⚠️  Alguns testes falharam. Revise as mensagens acima.")

    print()
    client.close()
    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
