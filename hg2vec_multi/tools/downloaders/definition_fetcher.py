"""Definition fetcher module for retrieving word definitions from online dictionaries.

This module provides core functionality for fetching individual word definitions
from various dictionary sources.
"""

import random
import time
import logging
import requests
from typing import Dict, List, Optional, Tuple

from hg2vec_multi.tools.downloaders.dictionary_config import (
    ERROR_CODES,
    HTTP_ERROR_MAPPING,
    USER_AGENTS,
    LANGUAGE_DICTIONARIES
)
from hg2vec_multi.tools.downloaders.dictionaries.factory import get_dictionary_api

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_random_user_agent() -> str:
    """Get a random user agent for request headers.
    
    Returns:
        Random user agent string
    """
    return random.choice(USER_AGENTS)


def download_html(url: str, retries: int = 3, timeout: int = 10) -> Tuple[Optional[str], Optional[str]]:
    """Download HTML from a URL.
    
    Args:
        url: URL to download from
        retries: Number of retries on failure
        timeout: Timeout in seconds
        
    Returns:
        Tuple of (html_content, error_message)
    """
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0"
    }
    
    error_message = None
    
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            
            # Check for HTTP errors
            if response.status_code != 200:
                error_code = response.status_code
                error_message = HTTP_ERROR_MAPPING.get(error_code, f"HTTP error {error_code}")
                logger.warning(f"Failed to download {url}: {error_message}")
                
                if error_code in [429, 503]:
                    # Rate limit or service unavailable, wait before retrying
                    wait_time = 2 ** attempt + random.uniform(0, 1)
                    logger.info(f"Waiting {wait_time:.2f} seconds before retry {attempt+1}/{retries}")
                    time.sleep(wait_time)
                    continue
                else:
                    # Other errors, return immediately
                    return None, error_message
            
            return response.text, None
            
        except requests.exceptions.Timeout:
            error_message = ERROR_CODES["timeout"]
            logger.warning(f"Timeout while downloading {url}, retry {attempt+1}/{retries}")
            # Exponential backoff
            wait_time = 2 ** attempt + random.uniform(0, 1)
            time.sleep(wait_time)
            
        except requests.exceptions.ConnectionError:
            error_message = ERROR_CODES["network_error"]
            logger.warning(f"Network error while downloading {url}, retry {attempt+1}/{retries}")
            # Exponential backoff
            wait_time = 2 ** attempt + random.uniform(0, 1)
            time.sleep(wait_time)
            
        except Exception as e:
            error_message = str(e)
            logger.warning(f"Error downloading {url}: {error_message}, retry {attempt+1}/{retries}")
            # Exponential backoff
            wait_time = 2 ** attempt + random.uniform(0, 1)
            time.sleep(wait_time)
    
    # All retries failed
    logger.error(f"Failed to download {url} after {retries} retries")
    return None, error_message or ERROR_CODES["unknown"]


def download_word_definition(word: str, pos: str = "all", language: str = "en") -> Dict[str, str]:
    """Download definitions for a word from appropriate dictionaries.
    
    Args:
        word: Word to look up
        pos: Part of speech filter
        language: Language code
        
    Returns:
        Dictionary of {dictionary_name: definition}
    """
    if language not in LANGUAGE_DICTIONARIES:
        raise ValueError(f"Unsupported language: {language}")
    
    results = {}
    
    # Get dictionaries for the language
    dictionaries = LANGUAGE_DICTIONARIES[language]
    
    # For each dictionary in the language
    for dictionary_name in dictionaries:
        try:
            # Get the dictionary API
            dictionary_api = get_dictionary_api(dictionary_name)
            
            # Get the definition
            definition_result = dictionary_api.get_definition(word, pos)
            
            # If it's a list, it's successful
            if isinstance(definition_result, list) and definition_result:
                results[dictionary_name] = " ".join(definition_result)
            else:
                # It's an error tuple
                _, url, error = definition_result
                logger.warning(f"Could not get definition for '{word}' from {dictionary_name}: {error}")
                
        except Exception as e:
            logger.error(f"Error using {dictionary_name} API for '{word}': {str(e)}")
        
        # Add a small delay between requests to be nice to servers
        time.sleep(0.2)
    
    return results 