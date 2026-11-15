# 📖 Assistente Bíblico — Controle Remoto por Voz para Holyrics

<p align="center">
  <strong>Controle inteligente e sem fio de projeção bíblica por comando de voz natural durante cultos da igreja.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python" alt="Python Version" />
  <img src="https://img.shields.io/badge/GUI-PySide6-41CD52?logo=qt" alt="PySide6 GUI" />
  <img src="https://img.shields.io/badge/Speech-faster--whisper%20(int8)-purple" alt="faster-whisper" />
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011%20(64--bit)-0078D6?logo=windows" alt="Windows" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License MIT" />
  <img src="https://img.shields.io/badge/Offline-100%25%20Local-brightgreen" alt="Offline Mode" />
</p>

---

## 🎯 Sobre o Projeto

O **Assistente Bíblico** foi desenvolvido para transformar a rotina dos operadores de projeção e pastores durante os cultos. Ele atua como um controle remoto por voz totalmente offline para o **Holyrics**, permitindo que passagens bíblicas sejam faladas com naturalidade e projetadas imediatamente no telão ou TV, **sem interromper o modo de apresentação ou fechar a tela**.

### 🌟 Destaques Principais

- 🎙️ **Reconhecimento de Voz 100% Offline:** Utiliza o motor `faster-whisper` (modelo `small` quantizado em `int8`), sem custos de APIs em nuvem e sem depender de conexão com a internet.
- 🗣️ **Comandos em Fala Natural:** Compreende frases espontâneas de pregação como *"Vamos abrir em João capítulo 3, versículo 16"* ou *"Então, lá em Salmos 23, versículo 1"*.
- 🛡️ **Filtro Canônico Antifalha:** Valida todas as referências contra os 66 livros da Bíblia (limites de capítulos e versículos). Ignora falas comuns do culto (ex: *"Glória a Deus!"*, *"Vamos orar"*) para evitar disparos acidentais.
- ⏩ **Navegação Contínua de Versículos:** Permite avançar ou retroceder versículos dinamicamente com comandos como *"Próximo versículo"* ou *"Versículo anterior"*.
- 🛑 **Parada Segura de Projeção:** Comandos como *"Parar projeção"*, *"Limpar projeção"* ou *"Encerrar projeção"* só fecham a tela se a apresentação atual for de fato bíblica, protegendo letras de músicas e mídias de louvor.
- 🔄 **Dois Modos de Operação:**
  - **Push-to-Talk:** Pressione e segure a tecla <kbd>ENTER</kbd> (ou botão de microfone) para falar.
  - **Automático Inteligente:** O sistema monitora o microfone continuamente com detecção de voz (VAD) desacoplada, sem travar a interface nem causar sobrecarga de hardware.
- 🎨 **Interface Moderna Escura (PySide6):** Visual grafite e índigo, projetado especialmente para cabines e mesas de som com pouca luz, com VU Meter dinâmico e status em tempo real.

---

## 📸 Demonstração da Interface

```
+--------------------------------------------------------------------------+
|  Assistente Bíblico              ● Holyrics Conectado   [⚙️ Configurações]|
|  Controle de projeção de versículos por comando de voz                   |
+--------------------------------------------------------------------------+
|  PROJEÇÃO ATIVA NA TV (HOLYRICS)                                         |
|  João 3:16                                                [🔄 Sincronizar]|
|  Projeção bíblica ativa (Slide 26140/31106). Sincronizado com o Holyrics.|
+--------------------------------------------------------------------------+
|  CONTROLE POR VOZ             Modo: [🎙️ Push-to-Talk ▼]  ● Projetado na TV|
|                                                                          |
|                                ( 🎙️ )                                    |
|                   Segure [ENTER] ou clique para falar                    |
|  [==========================              ] -18.2 dB                     |
+--------------------------------------------------------------------------+
|  ÚLTIMO COMANDO PROCESSADO                                               |
|  Fala Reconhecida:          Comando / Referência:   Status da Projeção:  |
|  "João capítulo 3 versículo 16"  João 3:16          ✅ Versículo projetado|
+--------------------------------------------------------------------------+
|  [ ◀ Versículo Anterior ]   [ Próximo Versículo ▶ ]   [ Limpar Tela (TV) ]|
+--------------------------------------------------------------------------+
```

---

## 🚀 Como Usar

### Exemplos de Comandos Reconhecidos:

| Ação Desejada | Exemplos de Fala Aceitos |
| :--- | :--- |
| **Projetar Versículo** | *"João 3:16"*<br>*"Salmos capítulo 23 versículo 1"*<br>*"Vamos abrir em Romanos 8:1"*<br>*"Abra a sua Bíblia em Gênesis 1:1"*<br>*"Hoje vamos estudar Primeiro Coríntios 13"* |
| **Avançar Versículo** | *"Próximo versículo"*<br>*"Avançar versículo"* |
| **Voltar Versículo** | *"Versículo anterior"*<br>*"Voltar versículo"* |
| **Encerrar Projeção Bíblica** | *"Parar projeção"*<br>*"Limpar projeção"*<br>*"Encerrar projeção"* |
| **Falas Comuns (Ignoradas)** | *"Glória a Deus!"*, *"Vamos orar"*, *"Hoje teremos uma reunião especial"* (Ignorados pelo filtro por segurança) |

---

## 🛠️ Instalação e Execução

### Opção 1: Usando o Instalador Windows (Recomendado para Produção)
Se você gerou o instalador profissional com o Inno Setup:
1. Execute `Instalador_AssistenteBiblico_v0.1.0.exe`.
2. O aplicativo será instalado em `C:\Program Files\Assistente Bíblico` com atalhos no Menu Iniciar e Área de Trabalho.
3. Abra o app, clique em **⚙️ Configurações**, informe o IP/Porta e cole o **Token da API do Holyrics**.
4. Pronto para usar em qualquer computador sem precisar de Python instalado!

---

### Opção 2: Executando a Partir do Código-Fonte (Desenvolvedores)

#### Requisitos do Sistema:
- **SO:** Windows 10 ou 11 (64-bit)
- **RAM:** 8 GB recomendado
- **Python:** 3.10 ou superior

#### 1. Clonar o repositório:
```bash
git clone https://github.com/SEU_USUARIO/assistente-biblico.git
cd assistente-biblico
```

#### 2. Criar e ativar um ambiente virtual:
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### 3. Instalar as dependências:
```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

#### 4. Configurar a Conexão com o Holyrics:
No Holyrics:
1. Vá em `Arquivo` > `Configurações` > `API Server`.
2. Ative o servidor HTTP local (padrão porta `8091`).
3. Em `Gerenciar Permissões`, crie ou copie o seu **Token de Autenticação**.
4. Inicie o Assistente Bíblico e insira o token na janela **⚙️ Configurações** (ou crie um arquivo `config.json` a partir do `config.example.json`).

#### 5. Iniciar o Aplicativo:
```powershell
python main.py
```

---

## 🧪 Testes Automatizados

O projeto possui uma cobertura completa de testes unitários e de integração:

```powershell
# Executar todos os testes
python -m pytest tests/ -v

# Testes de GUI PySide6
python -m pytest tests/test_gui.py -v

# Testes de interpretação e segurança de comandos
python -m pytest tests/test_etapa7_1.py -v
```

---

## 📦 Como Gerar o Executável e o Instalador

Para empacotar a aplicação e criar o instalador Windows autônomo com o modelo offline embutido:

1. Instale o **Inno Setup 6**: [jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)
2. Execute o script de compilação completa:
```powershell
python scripts/compile_all.py
```
O instalador final estará pronto em: `dist/installer/Instalador_AssistenteBiblico_v0.1.0.exe`.

---

## 📁 Estrutura do Projeto

```text
assistenteVoz/
├── src/
│   ├── core/                  # Controlador principal, constantes e logging seguro
│   │   ├── controller.py      # Orquestrador voz -> interpretação -> API
│   │   ├── logging_config.py  # Filtro de segurança (TokenFilter) e logs
│   │   └── path_utils.py      # Resolução robusta de caminhos (%APPDATA% / portátil)
│   ├── config/                # Gerenciador de configurações (config.json)
│   ├── interpreter/           # Mecanismo de NLP bíblico
│   │   ├── canon_data.py      # Limites canônicos de capítulos e versículos dos 66 livros
│   │   ├── command_classifier.py # Classificador de intenções e comandos
│   │   ├── normalizer.py      # Normalização fonética e pontuação
│   │   └── number_converter.py# Conversor estrito de números por extenso em português
│   ├── holyrics/              # Integração HTTP com a API Server oficial do Holyrics
│   ├── voice/                 # Captura de áudio, VAD e faster-whisper offline
│   └── ui/                    # Interface gráfica em PySide6
│       ├── main_window.py     # Janela principal
│       ├── threads.py         # Workers assíncronos (sem congelamento de UI)
│       ├── widgets/           # Widgets customizados (VU Meter dinâmico, Status Badge)
│       └── dialogs/           # Modal de configurações com campo de Token
├── scripts/                   # Scripts de build, auditoria e testes ao vivo
├── tests/                     # Bateria de testes automatizados com pytest
├── main.py                    # Ponto de entrada do aplicativo
└── requirements.txt           # Dependências do projeto
```

---

## 🔒 Segurança e Privacidade

- **100% Local:** Nenhum áudio, comando ou dado é transmitido para servidores de terceiros ou serviços em nuvem.
- **Proteção de Credenciais:** O token do Holyrics é protegido por filtros em todos os arquivos de log (`TokenFilter`) e nunca é exposto na tela principal ou compartilhado no build.
- **Diretórios Seguros:** As preferências e tokens do usuário são mantidos com segurança em `%APPDATA%\AssistenteBiblico\`, sobrevivendo a reinstalações ou atualizações de versão sem serem apagados.

---

## 📄 Licença

Distribuído sob a licença **MIT**. Veja o arquivo `LICENSE` para mais detalhes.
