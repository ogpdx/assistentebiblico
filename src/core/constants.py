"""
Constantes globais do Assistente Bíblico.
"""

# Informações do aplicativo
APP_NAME = "Assistente Bíblico"
APP_VERSION = "0.1.0"
APP_DESCRIPTION = "Assistente de projeção bíblica por comando de voz para Holyrics"

# Holyrics API Server - valores padrão
DEFAULT_HOLYRICS_HOST = "localhost"
DEFAULT_HOLYRICS_PORT = 8091
DEFAULT_HOLYRICS_TIMEOUT = 10.0  # segundos

# Holyrics API - ações (endpoints) oficiais
# Fonte: https://github.com/holyrics/API-Server
class HolyricsActions:
    """Nomes das ações da API do Holyrics.

    Cada atributo corresponde ao valor exato do parâmetro {action}
    na URL http://[IP]:[PORT]/api/{action}.
    """

    # Sistema
    GET_CP_INFO = "GetCPInfo"

    # Bíblia
    SHOW_VERSE = "ShowVerse"
    SELECT_VERSE = "SelectVerse"
    GET_BIBLE_VERSIONS = "GetBibleVersions"
    GET_BIBLE_VERSIONS_V2 = "GetBibleVersionsV2"
    GET_BIBLE_BOOKS = "GetBibleBooks"
    GET_AVAILABLE_BIBLE_BOOKS = "GetAvailableBibleBooks"
    GET_BIBLE_SETTINGS = "GetBibleSettings"
    IDENTIFY_VERSE_REFERENCES = "IdentifyVerseReferences"
    PARSE_VERSE_ID = "ParseVerseID2VerseReference"
    PARSE_VERSE_ID_GROUP = "ParseVerseID2VerseReferenceGroup"

    # Apresentação
    SHOW_QUICK_PRESENTATION = "ShowQuickPresentation"
    CLOSE_CURRENT_PRESENTATION = "CloseCurrentPresentation"
    CLOSE_CURRENT_QUICK_PRESENTATION = "CloseCurrentQuickPresentation"
    GET_CURRENT_PRESENTATION = "GetCurrentPresentation"

    # Controles de navegação
    ACTION_NEXT = "ActionNext"
    ACTION_PREVIOUS = "ActionPrevious"
    ACTION_GO_TO_INDEX = "ActionGoToIndex"


# Formato de ID de versículo: BBCCCVVV
# BB  = Número do livro (01-66)
# CCC = Capítulo (000-999, preenchido com zeros)
# VVV = Versículo (000-999, preenchido com zeros)
VERSE_ID_FORMAT = "{book:02d}{chapter:03d}{verse:03d}"

# Logging
LOG_DIR = "logs"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
LOG_BACKUP_COUNT = 3
