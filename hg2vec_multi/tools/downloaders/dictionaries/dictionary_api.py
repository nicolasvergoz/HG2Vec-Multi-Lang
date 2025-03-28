"""Base class for dictionary APIs."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Union
import requests
from bs4 import BeautifulSoup
import re
import ssl
from urllib.error import HTTPError
from ..dictionary_config import ERROR_CODES, HTTP_ERROR_MAPPING, USER_AGENTS
import random
import time

class DictionaryAPI(ABC):
    """Base class for dictionary APIs."""
    
    @property
    @abstractmethod
    def URL(self) -> str:
        """Base URL for the dictionary."""
        pass
    
    @property
    @abstractmethod
    def SELECTORS(self) -> dict:
        """CSS selectors for different parts of speech."""
        pass
    
    @property
    @abstractmethod
    def SUPPORTED_LANGUAGES(self) -> List[str]:
        """List of supported languages."""
        pass
    
    def __init__(self, name: str):
        """Initialize the dictionary API.
        
        Args:
            name: The name of the dictionary
        """
        self.name = name
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": random.choice(USER_AGENTS)
        })
        # Create SSL context for urllib requests
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
    
    def get_definition(self, word: str, pos: str = "all") -> Union[List[str], Tuple[None, str, str]]:
        """Get the definition of a word.
        
        Args:
            word: The word to look up.
            pos: Part of speech to filter by. Defaults to "all".
            
        Returns:
            List of definitions or tuple of (None, error_code, error_message).
        """
        try:
            url = f"{self.URL}{word}"
            response = self.session.get(url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            selector = self.SELECTORS.get(pos, self.SELECTORS["all"])
            definitions = soup.select(selector)
            
            if not definitions:
                return None, "not_found", ERROR_CODES["not_found"]
            
            return [def_.get_text().strip() for def_ in definitions]
            
        except requests.exceptions.RequestException as e:
            error_code = HTTP_ERROR_MAPPING.get(e.response.status_code, "unknown_error")
            return None, error_code, ERROR_CODES[error_code]
        except Exception as e:
            return None, "unknown_error", str(e)
    
    @staticmethod
    @abstractmethod
    def parse_definitions(html_content: str, pos: str = "all") -> List[str]:
        """Parse definitions from HTML content.
        
        Args:
            html_content: The HTML content to parse.
            pos: Part of speech to filter by. Defaults to "all".
            
        Returns:
            List of definitions.
        """
        pass
    
    def _handle_http_error(self, error: HTTPError, word: str, url: str) -> Tuple[None, str, str]:
        """Handle HTTP errors from dictionary requests.
        
        Args:
            error: The HTTPError
            word: The word that was being looked up
            url: The URL that was accessed
            
        Returns:
            Tuple (None, url, error_message)
        """
        error_code = error.code
        error_message = HTTP_ERROR_MAPPING.get(
            error_code, 
            f"HTTP Error {error_code}"
        )
        return (None, url, f"Error {error_code}: {error_message}")
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text.
        
        Args:
            text: HTML text
            
        Returns:
            Cleaned text
        """
        cleaner = re.compile('<.+?>', re.I|re.S)
        return re.sub(cleaner, '', text).strip() 