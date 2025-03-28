"""Dictionary API factory module."""

from typing import Dict, Type

from hg2vec_multi.tools.downloaders.dictionaries.dictionary_api import DictionaryAPI
from hg2vec_multi.tools.downloaders.dictionaries.cambridge import CambridgeAPI
from hg2vec_multi.tools.downloaders.dictionaries.oxford import OxfordAPI
from hg2vec_multi.tools.downloaders.dictionaries.robert import RobertAPI
from hg2vec_multi.tools.downloaders.dictionaries.dictionary_com import DictionaryComAPI
from hg2vec_multi.tools.downloaders.dictionaries.collins import CollinsAPI


# Dictionary API registry
DICTIONARY_APIS: Dict[str, Type[DictionaryAPI]] = {
    "cambridge": CambridgeAPI,
    "dictionary": DictionaryComAPI,
    "collins": CollinsAPI,
    "oxford": OxfordAPI,
    "robert": RobertAPI
}


def get_dictionary_api(name: str) -> DictionaryAPI:
    """Get a dictionary API instance by name.
    
    Args:
        name: The name of the dictionary API
        
    Returns:
        A DictionaryAPI instance
        
    Raises:
        ValueError: If the dictionary name is not supported
    """
    if name not in DICTIONARY_APIS:
        raise ValueError(
            f"Dictionary '{name}' is not supported. "
            f"Available options: {', '.join(DICTIONARY_APIS.keys())}"
        )
    
    return DICTIONARY_APIS[name]() 