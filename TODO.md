# TODO — Assistente Bíblico

## 📌 Etapa 1: Integração com o Holyrics
- [x] Estrutura modular de diretórios criada (`src/core`, `src/config`, `src/holyrics`, `tests`, `scripts`).
- [x] Arquivo de dependências (`requirements.txt`) enxuto e adaptado a máquinas com 8 GB de RAM.
- [x] Sistema de configurações (`src/config/settings.py`) com carregamento de JSON e merge de defaults.
- [x] Mascaramento e proteção de tokens em logs (`src/core/logging_config.py` com `TokenFilter`).
- [x] Exclusão de credenciais sensíveis via `.gitignore`.
- [x] Cliente HTTP (`src/holyrics/client.py`) com tratamento de exceções de conexão, timeout, 401, 403 e payloads inválidos.
- [x] Camada de API de alto nível (`src/holyrics/api.py`) cobrindo `GetCPInfo`, `GetBibleVersionsV2`, `ShowVerse` (por referência e por ID `BBCCCVVV`), `SelectVerse`, `CloseCurrentPresentation` e `ShowQuickPresentation`.
- [x] Ajuste do payload de `ShowVerse` para a especificação da API HTTP do Holyrics (parâmetros enviados na raiz sem o wrapper `input`).
- [x] Script independente de validação interativa (`scripts/test_holyrics_connection.py`).
- [x] Bateria de testes automatizados unitários (`tests/test_settings.py`, `tests/test_holyrics_client.py`, `tests/test_holyrics_api.py`).
- [x] Documentação de instalação e uso (`README.md`).

---

## ⏳ Pendente para Validação Real da Etapa 1 (Ambiente do Usuário)
- [ ] Ativar API Server local no software Holyrics (`Arquivo > Configurações > API Server`).
- [ ] Gerar token em `Gerenciar Permissões`.
- [ ] Inserir token em `config.json`.
- [ ] Executar `python -m scripts.test_holyrics_connection` e confirmar projeção física na tela.

---

## 📌 Etapa 2: Interpretador de Comandos e Referências Bíblicas (Auditado e Corrigido)
- [x] `normalizer.py`: normalização textual refinada, pontuações tratadas como separadores e símbolos ordinais padronizados (1º, 1ª, 2º, etc.).
- [x] `number_converter.py`: **CORREÇÃO CRÍTICA** — eliminação da soma arbitrária de dígitos adjacentes (ex: `23, 1` não soma mais para 24!). Gramática decrescente estrita de números por extenso.
- [x] `canon_data.py`: tabela canônica completa com os 66 livros, quantidade máxima de capítulos e versículos por capítulo.
- [x] `validator.py`: validação canônica de limites (capítulos e versículos existentes). Referências inexistentes ou extrapoladas (ex: `Salmos 151`, `João 1316`, `João 3:999`) rejeitadas com segurança como `UNKNOWN`.
- [x] `bible_books.py`: adição e teste de variantes ("Primeiro Coríntios", "1º Corinthians", "Segundo Reis", "2º Reis", etc.).
- [x] `reference_builder.py`: extração com validação integrada, rejeitando referências incompletas ou inválidas.
- [x] `command_classifier.py`: proteção contra palavras soltas ("voltar", "avançar") e conversas comuns de culto.
- [x] `tests/test_interpreter.py`: suite completa de testes de regressão para todos os casos da auditoria.

---

## 📌 Etapa 3: Reconhecimento de Voz Offline (Auditado e Aprimorado)
- [x] **Causa Raiz de Áudios Vazios Corrigida:** eliminação do descarte precoce do buffer de áudio no modo Push-to-Talk dentro de `src/voice/recorder.py`.
- [x] `audio_utils.py`: métricas acústicas em tempo real (RMS, Pico absoluto, dBFS, alertas de silêncio e clipping) e normalização de ganho automático.
- [x] Indicador de volume dinâmico (VU Meter em ASCII) no console durante a gravação ao vivo.
- [x] `transcriber.py`: novo `initial_prompt` estruturado em frases naturais eclesiásticas em português brasileiro, condicionamento anti-alucinação (`condition_on_previous_text=False`) e busca em feixe (`beam_size=2`).
- [x] `bible_books.py`: ampliação dos aliases fonéticos para Salmos, Êxodo, Deuteronômio, Tessalonicenses, Apocalipse, etc.
- [x] `scripts/test_voice_recognition.py`: painel de diagnóstico com separação clara de 3 fases (`[CAPTURA]`, `[TRANSCRIÇÃO]`, `[INTERPRETAÇÃO]`).
- [x] `scripts/benchmark_models.py`: medição real de latência, RAM e RTF para os modelos `base` e `small`.
- [x] `tests/test_salmos_and_books.py`: suíte completa de testes específicos para Salmos e livros de fonética sensível.

---

## 📌 Etapa 4: Integração do Reconhecimento de Voz com o Holyrics
- [x] Criação do controlador central (`src/core/controller.py` com `VoiceHolyricsController` e `ExecutionResult`).
- [x] Fluxo completo implementado: Captura de Áudio -> Transcrição -> Interpretação -> Validação Canônica -> Consulta de Estado no Holyrics -> Execução Segura -> Sincronização da TV.
- [x] Regra de segurança operacional de navegação: `ActionNext` e `ActionPrevious` só são executados se `GetCurrentPresentation` confirmar `type == "verse"`.
- [x] Bloqueio de navegação se a apresentação ativa for música (`type == "song"`) ou se não houver apresentação ativa.
- [x] Bloqueio estrito de comandos `UNKNOWN` ou referências bíblicas inválidas/inexistentes (ex: `João 1316`, `Salmos 151`).
- [x] Bloqueio de duplicação acidental (evita reexecução da mesma referência em curto intervalo < 2s).
- [x] Tratamento de exceções e tolerância a falhas: Holyrics desconectado ou com erro HTTP não trava o microfone nem o assistente.
- [x] Aplicação interativa de terminal em modo Push-to-Talk (`scripts/run_assistant_cli.py`) com VU Meter dinâmico e feedback do que está projetado na TV.
- [x] Suíte de testes automatizados com mocks (`tests/test_controller.py`) cobrindo todos os cenários obrigatórios.

---

## ⏳ Pendente para a Próxima Etapa (Etapa 5 — Interface Gráfica PySide6)
- [ ] Criação da tela principal moderna em PySide6.
- [ ] Botão de microfone Push-to-Talk visual com indicação de estado (Aguardando / Gravando / Processando).
- [ ] Painel com indicador de conexão em tempo real com o Holyrics.
- [ ] Painel de prévia com opção de confirmação manual ou envio automático.
- [ ] Lista histórica de versículos consultados no culto com botão para reexibir.
