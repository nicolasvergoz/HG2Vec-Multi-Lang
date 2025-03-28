#!/usr/bin/env python3
"""
Dictionary downloaders package.

This package provides dictionary downloaders for various online dictionaries.
"""

# Import base class and standards
from .base import DictionaryDownloader, STANDARD_SHORT_CODES, STANDARD_NAMES

# Import all dictionary downloaders
from .cambridge import downloader as cambridge_downloader
from .dictionary_com import downloader as dictionary_downloader
from .collins import downloader as collins_downloader
from .robert import downloader as robert_downloader
from .larousse import downloader as larousse_downloader

# Dictionary mapping short codes to downloaders
DICTIONARY_DOWNLOADERS = {
    "Cam": cambridge_downloader,
    "Dic": dictionary_downloader, 
    "Col": collins_downloader,
    "Rob": robert_downloader,
    "Lar": larousse_downloader
}

# Get downloader instance by short code or name
def get_downloader(name_or_code):
    """Get a dictionary downloader by its short code or name.
    
    Args:
        name_or_code (str): Short code or name for the dictionary
        
    Returns:
        DictionaryDownloader: Dictionary downloader instance
        
    Raises:
        KeyError: If no downloader exists for the given short code or name
    """
    # Try to get standard short code first
    standard_code = DictionaryDownloader.get_standard_short_code(name_or_code)
    
    # Try to find by short code
    if standard_code in DICTIONARY_DOWNLOADERS:
        return DICTIONARY_DOWNLOADERS[standard_code]
    
    # If not found by short code, try to find a downloader where the object matches the name_or_code
    for downloader in DICTIONARY_DOWNLOADERS.values():
        if downloader == name_or_code:
            return downloader
            
    raise KeyError(f"No downloader found for: {name_or_code}")

# Get all downloaders
def get_all_downloaders():
    """Get all available dictionary downloaders.
    
    Returns:
        dict: Dictionary of all downloaders, keyed by short code
    """
    return DICTIONARY_DOWNLOADERS

# Get all downloaders for a specific language
def get_language_downloaders(language):
    """Get all dictionary downloaders for a specific language.
    
    Args:
        language (str): Language code ('en' or 'fr')
        
    Returns:
        dict: Dictionary of downloaders for the language, keyed by short code
    """
    return {
        code: downloader for code, downloader in DICTIONARY_DOWNLOADERS.items()
        if downloader.language == language
    }

# Utility functions for finding downloaders
def get_downloader_by_name(name):
    """Get a dictionary downloader by its name.
    
    Args:
        name (str): Name of the dictionary
        
    Returns:
        DictionaryDownloader: Dictionary downloader instance
        
    Raises:
        KeyError: If no downloader exists for the given name
    """
    for downloader in DICTIONARY_DOWNLOADERS.values():
        if downloader.name.lower() == name.lower():
            return downloader
    raise KeyError(f"No downloader found for name: {name}")

def get_downloader_by_short_code(short_code):
    """Get a dictionary downloader by its short code.
    
    Args:
        short_code (str): Short code for the dictionary
        
    Returns:
        DictionaryDownloader: Dictionary downloader instance
        
    Raises:
        KeyError: If no downloader exists for the given short code
    """
    if short_code in DICTIONARY_DOWNLOADERS:
        return DICTIONARY_DOWNLOADERS[short_code]
    raise KeyError(f"No downloader found for short code: {short_code}") 