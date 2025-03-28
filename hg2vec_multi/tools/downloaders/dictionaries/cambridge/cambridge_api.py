"""Cambridge dictionary API implementation."""

import re
import urllib.request
from typing import List, Tuple, Union
from urllib.error import HTTPError
from bs4 import BeautifulSoup

from ..dictionary_api import DictionaryAPI
from .config import URL, SELECTORS, SUPPORTED_LANGUAGES


class CambridgeAPI(DictionaryAPI):
    """Cambridge dictionary API implementation."""
    
    @property
    def URL(self) -> str:
        return URL
    
    @property
    def SELECTORS(self) -> dict:
        return SELECTORS
    
    @property
    def SUPPORTED_LANGUAGES(self) -> List[str]:
        return SUPPORTED_LANGUAGES
    
    def __init__(self):
        """Initialize the Cambridge Dictionary API."""
        super().__init__("cambridge")
    
    @staticmethod
    def parse_definitions(html_content: str, pos: str = "all") -> List[str]:
        """Parse definitions from Cambridge dictionary HTML content.
        
        Args:
            html_content: The HTML content to parse.
            pos: Part of speech to filter by. Defaults to "all".
            
        Returns:
            List of definitions.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        selector = SELECTORS.get(pos, SELECTORS["all"])
        definitions = soup.select(selector)
        return [def_.get_text().strip() for def_ in definitions]
    
    def get_definition(self, word: str, pos: str = "all") -> Union[List[str], Tuple[None, str, str]]:
        """Get the definition from Cambridge Dictionary.
        
        Args:
            word: The word to look up
            pos: Part of speech (noun, verb, adjective, or all)
            
        Returns:
            List of definitions or a tuple (None, url, error_message) if not found
        """
        if pos not in ["all", "adjective", "noun", "verb"]:
            pos = "all"
            
        url = self.URL + word
        
        try:
            html = urllib.request.urlopen(url, context=self.ssl_context).read().decode('utf-8')
            
            # Use the BeautifulSoup parser method
            defs = self.parse_definitions(html, pos)
            
            if not defs:
                # If BeautifulSoup parsing fails, fall back to regex method for compatibility
                # Definitions are in a <b> tag with class "def"
                defs_pat = re.compile('<b class="def">(.*?)</b>', re.I|re.S)
                
                # Extract definitions based on part of speech
                if pos in ["adjective", "noun", "verb"]:
                    block_pat = re.compile('<div class="entry-body__el ', re.I|re.S)
                    idx = [m.start() for m in block_pat.finditer(html)] + [len(html)]
                    span = [(idx[i], idx[i+1]) for i in range(len(idx)-1)]
                    
                    pos_pat = re.compile('class="pos".*?>(.*?)</span>', re.I|re.S)
                    defs = []
                    
                    for start, end in span:
                        pos_extracted = re.search(pos_pat, html[start:end])
                        
                        if pos_extracted is None:
                            continue
                            
                        pos_extracted = pos_extracted.group(1)
                        
                        if pos_extracted != pos:
                            continue
                            
                        defs += re.findall(defs_pat, html[start:end])
                else:
                    # Extract all definitions
                    defs = re.findall(defs_pat, html)
                
            # Clean HTML tags from definitions
            return [self._clean_html(x) for x in defs]
            
        except HTTPError as e:
            return self._handle_http_error(e, word, url)
        except Exception as e:
            return (None, url, f"Error: {str(e)}") 