"""Oxford dictionary API."""

import re
import urllib.request
from typing import List, Tuple, Union
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import logging
import random

from hg2vec_multi.tools.downloaders.dictionaries.dictionary_api import DictionaryAPI
from hg2vec_multi.tools.downloaders.dictionary_config import USER_AGENTS
from .config import URL, SELECTORS, SUPPORTED_LANGUAGES


class OxfordAPI(DictionaryAPI):
    """Oxford dictionary API implementation."""
    
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
        """Initialize the Oxford Dictionary API."""
        super().__init__("oxford")
    
    @staticmethod
    def parse_definitions(html_content: str, pos: str = "all") -> List[str]:
        """Parse definitions from Oxford dictionary HTML content.
        
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
        """Get the definition from Oxford Dictionary.
        
        Args:
            word: The word to look up
            pos: Part of speech (noun, verb, adjective, or all)
            
        Returns:
            List of definitions or a tuple (None, url, error_message) if not found
        """
        if pos not in ["all", "adjective", "noun", "verb"]:
            pos = "all"
            
        url = f"{URL}{word}"
        
        # Oxford has server restrictions - need to spoof headers
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
        }
        req = urllib.request.Request(url, headers=headers)
        
        try:
            html = urllib.request.urlopen(req, context=self.ssl_context).read().decode('utf-8')
            
            # Use the BeautifulSoup parser method
            defs = self.parse_definitions(html, pos)
            
            if not defs:
                # If BeautifulSoup parsing fails, fall back to regex method for compatibility
                # Extract definitions
                defs_pat = re.compile('<span class="ind">(.*?)</span>', re.I|re.S)
                
                if pos in ["adjective", "noun", "verb"]:
                    section_pat = re.compile('<section id=.*?class="gramb".*?>(.*?)</section>', re.I|re.S)
                    sections = re.findall(section_pat, html)
                    
                    pos_pat = re.compile('<span class="pos">(.*?)</span>', re.I|re.S)
                    defs = []
                    
                    for section in sections:
                        pos_extracted = re.search(pos_pat, section)
                        
                        if pos_extracted is None:
                            continue
                            
                        pos_extracted = pos_extracted.group(1)
                        
                        if pos not in pos_extracted:
                            continue
                            
                        defs += re.findall(defs_pat, section)
                else:
                    # Extract all definitions
                    defs = re.findall(defs_pat, html)
            
            # Clean HTML tags
            return [self._clean_html(x) for x in defs]
            
        except HTTPError as e:
            return self._handle_http_error(e, word, url)
        except Exception as e:
            return (None, url, f"Error: {str(e)}") 