"""Robert dictionary API implementation."""

import time
import urllib.request
import urllib.parse
import random
from typing import List, Tuple, Union
from urllib.error import HTTPError
from bs4 import BeautifulSoup

from ..dictionary_api import DictionaryAPI
from hg2vec_multi.tools.downloaders.dictionary_config import USER_AGENTS
from .config import URL, SELECTORS, SUPPORTED_LANGUAGES


class RobertAPI(DictionaryAPI):
    """Robert dictionary API implementation."""
    
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
        """Initialize the Le Robert Dictionary API."""
        super().__init__("robert")
    
    @staticmethod
    def parse_definitions(html_content: str, pos: str = "all") -> List[str]:
        """Parse definitions from Robert dictionary HTML content.
        
        Args:
            html_content: The HTML content to parse.
            pos: Part of speech to filter by. Defaults to "all".
            
        Returns:
            List of definitions.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        selector = SELECTORS.get(pos, SELECTORS["all"])
        definitions = soup.select(selector)
        return [def_.get_text().strip().replace("'", " ") for def_ in definitions]
    
    def get_definition(self, word: str, pos: str = "all") -> Union[List[str], Tuple[None, str, str]]:
        """Get the definition from Le Robert Dictionary.
        
        Args:
            word: The word to look up
            pos: Part of speech (noun, verb, adjective, or all)
            
        Returns:
            List of definitions or a tuple (None, url, error_message) if not found
        """
        if pos not in ["all", "adjective", "noun", "verb"]:
            pos = "all"
            
        # URL encode the word (for words with apostrophes)
        encoded_word = urllib.parse.quote(word.strip())
        url = f"{URL}{encoded_word}"
        
        # Le Robert has server restrictions - need to spoof headers
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'none',
            'Accept-Language': 'fr-FR,fr;q=0.8,en-US;q=0.5,en;q=0.3',
        }
        req = urllib.request.Request(url, headers=headers)
        
        try:
            # Wait to avoid overwhelming the server
            time.sleep(0.5)
            
            response = urllib.request.urlopen(req, context=self.ssl_context)
            html = response.read().decode('utf-8')
            
            # Use the BeautifulSoup parser method first
            defs = self.parse_definitions(html, pos)
            
            if not defs:
                # If BeautifulSoup parsing fails, fall back to manual parsing
                soup = BeautifulSoup(html, 'html.parser')
                
                # Find all definition blocks
                blocks = soup.find_all('span', {'class': 'b_text'})
                
                # For each block, extract the definitions based on POS if specified
                defs = []
                
                if pos in ["adjective", "noun", "verb"]:
                    # Map English POS to French POS
                    pos_map = {
                        "adjective": "adjectif",
                        "noun": "nom",
                        "verb": "verbe"
                    }
                    french_pos = pos_map[pos]
                    
                    # Find POS markers
                    pos_blocks = soup.find_all('span', {'class': 'cat_grammar'})
                    
                    for idx, pos_block in enumerate(pos_blocks):
                        if french_pos in pos_block.text.lower():
                            # Get the next definition block
                            if idx < len(blocks):
                                defs.append(blocks[idx].text.strip())
                else:
                    # Get all definitions
                    for block in blocks:
                        defs.append(block.text.strip())
                
                if defs:
                    # Process French definitions:
                    # 1. Replace apostrophes with spaces to avoid merging words
                    processed_defs = []
                    for definition in defs:
                        # Replace different types of apostrophes with spaces
                        definition = definition.replace("'", " ")
                        definition = definition.replace("'", " ")
                        processed_defs.append(definition)
                    
                    defs = processed_defs
            
            if defs:
                return defs
            else:
                return (None, url, "Aucune définition trouvée")
            
        except HTTPError as e:
            return self._handle_http_error(e, word, url)
        except Exception as e:
            return (None, url, f"Error: {str(e)}") 