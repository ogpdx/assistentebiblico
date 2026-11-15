"""
Script de diagnóstico: testa o comportamento de navegação de versículos
no Holyrics API Server em cenários reais de culto.

Objetivos:
1. Verificar se ShowVerse substitui a apresentação atual ou a sobrepõe.
2. Verificar se ActionNext/ActionPrevious funcionam com versículos.
3. Verificar se GetCurrentPresentation retorna dados úteis sobre o versículo ativo.
4. Verificar se chamar ShowVerse duas vezes fecha a primeira apresentação.
5. Verificar o comportamento com ids (múltiplos versículos em um envio).

Uso:
    python -m scripts.test_verse_navigation
"""

import json
import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.settings import Settings
from src.core.logging_config import setup_logging
from src.holyrics.client import HolyricsClient
from src.holyrics.api import HolyricsAPI
from src.holyrics.exceptions import HolyricsError

import logging
setup_logging(level=logging.WARNING)


def header(msg: str) -> None:
    print(f"\n{'='*60}")
    print(f"  {msg}")
    print(f"{'='*60}")


def ok(msg: str) -> None:
    print(f"  [OK] {msg}")


def info(msg: str) -> None:
    print(f"  [INFO] {msg}")


def fail(msg: str) -> None:
    print(f"  [FALHA] {msg}")


def safe_json(data, max_len: int = 600) -> str:
    s = json.dumps(data, indent=2, ensure_ascii=False)
    return s[:max_len] + ("..." if len(s) > max_len else "")


def pause(seconds: float = 3.0, msg: str = "") -> None:
    if msg:
        info(f"{msg} (aguardando {seconds}s...)")
    time.sleep(seconds)


def main() -> None:
    settings = Settings("config.json")
    client = HolyricsClient(
        host=settings.holyrics_host,
        port=settings.holyrics_port,
        token=settings.holyrics_token,
    )
    api = HolyricsAPI(client)

    # Verifica conexão
    status = api.get_status()
    if not status.connected:
        print("Holyrics não conectado. Execute test_holyrics_connection primeiro.")
        sys.exit(1)

    header("TESTE DE NAVEGAÇÃO DE VERSÍCULOS")
    print("  Este teste vai projetar versículos na tela do Holyrics.")
    print("  Observe a TV/projetor durante os testes.\n")

    results = {}

    # ──────────────────────────────────────────────
    # TESTE A: ShowVerse com referência simples
    # ──────────────────────────────────────────────
    header("TESTE A: ShowVerse com referência 'João 3:16'")
    try:
        result = api.show_verse(reference="João 3:16")
        ok(f"ShowVerse com referência: {result.get('status')}")
        pause(3, "Verifique se João 3:16 apareceu na tela")
    except HolyricsError as e:
        fail(f"Erro: {e}")
        results["A"] = False

        # Tenta em inglês caso a referência em PT não funcione
        info("Tentando com referência em inglês: 'John 3:16'")
        try:
            result = api.show_verse(reference="John 3:16")
            ok(f"ShowVerse com referência inglês: {result.get('status')}")
            info("NOTA: O Holyrics pode exigir referências em formato específico.")
            pause(3)
        except HolyricsError as e2:
            fail(f"Também falhou em inglês: {e2}")

    # ──────────────────────────────────────────────
    # TESTE B: GetCurrentPresentation (o que está projetado agora?)
    # ──────────────────────────────────────────────
    header("TESTE B: GetCurrentPresentation")
    try:
        result = client.request("GetCurrentPresentation")
        data = result.get("data")
        if data:
            ok("Apresentação ativa detectada!")
            info(f"slide_number: {data.get('slide_number')}")
            info(f"total_slides: {data.get('total_slides')}")
            info(f"slide_type: {data.get('slide_type')}")
            info(f"type: {data.get('type')}")
            info(f"Dados completos:\n{safe_json(data)}")
            results["B_has_data"] = True
        else:
            info("GetCurrentPresentation retornou null/vazio.")
            results["B_has_data"] = False
    except HolyricsError as e:
        fail(f"Erro: {e}")
        results["B_has_data"] = False

    # ──────────────────────────────────────────────
    # TESTE C: ActionNext — avança para o próximo versículo
    # ──────────────────────────────────────────────
    header("TESTE C: ActionNext (avançar versículo)")
    try:
        result = client.request("ActionNext")
        ok(f"ActionNext: {result.get('status')}")
        pause(3, "Verifique se o versículo avançou (ex: João 3:17)")
    except HolyricsError as e:
        fail(f"Erro: {e}")

    # Consulta novamente para ver se mudou
    try:
        result = client.request("GetCurrentPresentation")
        data = result.get("data")
        if data:
            info(f"Após ActionNext — slide_number: {data.get('slide_number')}, total_slides: {data.get('total_slides')}")
    except HolyricsError:
        pass

    # ──────────────────────────────────────────────
    # TESTE D: ActionPrevious — volta para o versículo anterior
    # ──────────────────────────────────────────────
    header("TESTE D: ActionPrevious (voltar versículo)")
    try:
        result = client.request("ActionPrevious")
        ok(f"ActionPrevious: {result.get('status')}")
        pause(3, "Verifique se voltou ao versículo anterior (ex: João 3:16)")
    except HolyricsError as e:
        fail(f"Erro: {e}")

    # ──────────────────────────────────────────────
    # TESTE E: ShowVerse substituindo a apresentação ativa
    # ──────────────────────────────────────────────
    header("TESTE E: Segundo ShowVerse — substitui sem fechar?")
    info("Enviando Salmos 23:1 enquanto João 3:16 está ativo...")
    try:
        result = api.show_verse(reference="Sl 23:1")
        ok(f"ShowVerse Sl 23:1: {result.get('status')}")
        pause(3, "Verifique se a tela mudou de João 3 para Salmos 23")
        results["E_replace"] = True
    except HolyricsError as e:
        fail(f"Erro: {e}")
        # Tenta por ID
        info("Tentando por ID: 19023001 (Sl 23:1)")
        try:
            result = api.show_verse(verse_id="19023001")
            ok(f"ShowVerse por ID: {result.get('status')}")
            pause(3)
            results["E_replace"] = True
        except HolyricsError as e2:
            fail(f"Também falhou por ID: {e2}")
            results["E_replace"] = False

    # ──────────────────────────────────────────────
    # TESTE F: ShowVerse com múltiplos IDs (intervalo)
    # ──────────────────────────────────────────────
    header("TESTE F: ShowVerse com múltiplos IDs (Sl 23:1-4)")
    ids = ["19023001", "19023002", "19023003", "19023004"]
    try:
        result = api.show_verse(verse_ids=ids)
        ok(f"ShowVerse com 4 IDs: {result.get('status')}")
        pause(3, "Verifique se Salmos 23:1-4 apareceu (pode ser slides separados)")

        # Consulta quantos slides foram criados
        result = client.request("GetCurrentPresentation")
        data = result.get("data")
        if data:
            info(f"Total de slides: {data.get('total_slides')}")
            info(f"Slide atual: {data.get('slide_number')}")
            results["F_total_slides"] = data.get("total_slides")
    except HolyricsError as e:
        fail(f"Erro: {e}")

    # Testa ActionNext neste cenário
    info("ActionNext para percorrer slides dos versículos...")
    for i in range(3):
        try:
            client.request("ActionNext")
            pause(1.5)
            result = client.request("GetCurrentPresentation")
            data = result.get("data", {})
            info(f"  Slide {data.get('slide_number')}/{data.get('total_slides')}")
        except HolyricsError:
            pass

    # ──────────────────────────────────────────────
    # TESTE G: GetBibleSettings
    # ──────────────────────────────────────────────
    header("TESTE G: GetBibleSettings")
    try:
        result = client.request("GetBibleSettings")
        data = result.get("data", {})
        ok("Configurações bíblicas obtidas:")
        info(f"show_x_verses: {data.get('show_x_verses')}")
        info(f"versão tab 1: {data.get('tab_version_1')}")
        info(f"versão tab 2: {data.get('tab_version_2')}")
        info(f"uppercase: {data.get('uppercase')}")
        info(f"separator: {data.get('multiple_verses_separator_type')}")
        info(f"Dados completos:\n{safe_json(data)}")
        results["G_show_x"] = data.get("show_x_verses")
    except HolyricsError as e:
        fail(f"Erro: {e}")

    # ──────────────────────────────────────────────
    # TESTE H: ShowVerse por referência de intervalo em texto
    # ──────────────────────────────────────────────
    header("TESTE H: ShowVerse com referência em intervalo 'Rm 8:1-4'")
    try:
        result = api.show_verse(reference="Rm 8:1-4")
        ok(f"ShowVerse Rm 8:1-4: {result.get('status')}")
        pause(3, "Verifique se Romanos 8:1-4 apareceu")
    except HolyricsError as e:
        fail(f"Erro: {e}")
        info("Tentando 'Romanos 8:1-4'...")
        try:
            result = api.show_verse(reference="Romanos 8:1-4")
            ok(f"ShowVerse por nome completo: {result.get('status')}")
            pause(3)
        except HolyricsError as e2:
            fail(f"Também falhou: {e2}")

    # ──────────────────────────────────────────────
    # Fecha e RESUMO
    # ──────────────────────────────────────────────
    pause(2)
    try:
        api.close_current_presentation()
        info("Apresentação fechada para encerrar testes.")
    except HolyricsError:
        pass

    header("RESUMO DOS RESULTADOS")
    print("  Revise as observações acima e responda:")
    print()
    print("  1. O ShowVerse com referência em PT funcionou? (Teste A)")
    print("  2. O ActionNext avançou o versículo? (Teste C)")
    print("  3. O ActionPrevious retrocedeu? (Teste D)")
    print("  4. Enviar outro ShowVerse substituiu a apresentação")
    print("     sem fechar manualmente? (Teste E)")
    print("  5. Múltiplos IDs criaram slides individuais? (Teste F)")
    print("  6. ShowVerse com intervalo em texto funcionou? (Teste H)")
    print()
    print("  Copie toda a saída deste terminal e envie para análise.")

    client.close()


if __name__ == "__main__":
    main()
