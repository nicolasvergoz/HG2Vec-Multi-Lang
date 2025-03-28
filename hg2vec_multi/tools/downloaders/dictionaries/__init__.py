"""Dictionary modules package."""

from hg2vec_multi.tools.downloaders.dictionaries.dictionary_api import DictionaryAPI
from hg2vec_multi.tools.downloaders.dictionaries.cambridge import CambridgeAPI
from hg2vec_multi.tools.downloaders.dictionaries.oxford import OxfordAPI
from hg2vec_multi.tools.downloaders.dictionaries.robert import RobertAPI
from hg2vec_multi.tools.downloaders.dictionaries.dictionary_com import DictionaryComAPI
from hg2vec_multi.tools.downloaders.dictionaries.collins import CollinsAPI
from hg2vec_multi.tools.downloaders.dictionaries.factory import get_dictionary_api

__all__ = [
    "DictionaryAPI",
    "CambridgeAPI",
    "OxfordAPI",
    "RobertAPI",
    "DictionaryComAPI",
    "CollinsAPI",
    "get_dictionary_api"
] 