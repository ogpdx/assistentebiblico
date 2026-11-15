# Guia de Distribuição — Assistente Bíblico para Windows

O **Assistente Bíblico** foi compilado no modo autônomo portátil (`onedir`), não exigindo Python instalado no computador de destino.

---

## 1. Estrutura de Arquivos

```text
AssistenteBiblico/
├── AssistenteBiblico.exe          # Executável do aplicativo (inicia sem janela de terminal)
├── config.json                    # Arquivo de configuração (IP, porta e token do Holyrics)
├── config.example.json            # Modelo limpo de configuração
├── models/                        # Pasta com o modelo offline faster-whisper (small)
└── _internal/                     # Runtime, DLLs C++ (CTranslate2, PortAudio) e PySide6
```

---

## 2. Como Instalar em Outro Computador

1. **Copie a pasta inteira `AssistenteBiblico`** para o computador da igreja (ex: em `C:\Programas\AssistenteBiblico` ou no `Desktop`).
2. **Crie ou copie o `config.json`**:
   - Abra o `config.json` e informe o token da API gerado no Holyrics da máquina local:
     ```json
     {
       "holyrics": {
         "host": "localhost",
         "port": 8091,
         "token": "SEU_TOKEN_AQUI"
       }
     }
     ```
3. **Execução 100% Offline**:
   - A pasta `models/` já contém os arquivos do modelo Whisper (`model.bin`, `vocabulary.json`, `config.json`).
   - Não é necessário ter acesso à internet para iniciar ou reconhecer a voz.
4. **Criar Atalho**:
   - Clique com o botão direito em `AssistenteBiblico.exe` e selecione **Enviar para > Área de trabalho (criar atalho)**.

---

## 3. Diretórios de Dados no Windows

- **Configurações**: Se não houver `config.json` na pasta do executável, ele buscará/gravará em `%APPDATA%\AssistenteBiblico\config.json`.
- **Logs**: Gravados com rotação automática em `%LOCALAPPDATA%\AssistenteBiblico\logs\assistente_biblico.log` (tokens de autenticação são automaticamente mascarados).
- **Modelos**: Se a pasta `models/` estiver ao lado do executável, ela será usada prioritariamente.
