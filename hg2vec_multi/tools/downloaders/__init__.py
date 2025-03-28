"""Dictionary downloader package for fetching definitions from various sources."""

# Dictionary API classes
from hg2vec_multi.tools.downloaders.dictionaries import (
    DictionaryAPI,
    CambridgeAPI,
    OxfordAPI,
    RobertAPI,
    DictionaryComAPI,
    CollinsAPI,
    get_dictionary_api
)

# Definition fetcher functionality
from hg2vec_multi.tools.downloaders.definition_fetcher import (
    download_word_definition
)

# Definition batch processor
from hg2vec_multi.tools.downloaders.definition_batch_processor import (
    DefinitionDownloader
)

# Export error codes from dictionary_config
from hg2vec_multi.tools.downloaders.dictionary_config import ERROR_CODES

__all__ = [
    # Dictionary APIs
    "DictionaryAPI",
    "CambridgeAPI",
    "OxfordAPI",
    "RobertAPI",
    "DictionaryComAPI", 
    "CollinsAPI",
    "get_dictionary_api",
    
    # Downloaders
    "download_word_definition",
    "DefinitionDownloader",
    
    # Error codes
    "ERROR_CODES"
] 