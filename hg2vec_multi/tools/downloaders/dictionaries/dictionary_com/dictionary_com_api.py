"""Dictionary.com API implementation."""

import re
import urllib.request
from typing import List, Tuple, Union
from urllib.error import HTTPError

from hg2vec_multi.tools.downloaders.dictionaries.dictionary_api import DictionaryAPI
from hg2vec_multi.tools.downloaders.dictionary_config import DICT_URLS
from .config import URL, SELECTORS, SUPPORTED_LANGUAGES


class DictionaryComAPI(DictionaryAPI):
    """Dictionary.com API implementation."""
    
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
        """Initialize the Dictionary.com API."""
        super().__init__("dictionary")
    
    def get_definition(self, word: str, pos: str = "all") -> Union[List[str], Tuple[None, str, str]]:
        """Get the definition from Dictionary.com.
        
        Args:
            word: The word to look up
            pos: Part of speech (noun, verb, adjective, or all)
            
        Returns:
            List of definitions or a tuple (None, url, error_message) if not found
        """
        if pos not in ["all", "adjective", "noun", "verb"]:
            pos = "all"
            
        # Dictionary.com URL is not in the config, using a hard-coded URL
        url = f"http://www.dictionary.com/browse/{word}"
        
        try:
            html = urllib.request.urlopen(url, context=self.ssl_context).read().decode('utf-8')
            
            # Extract definition blocks
            block_pat = re.compile('<section class="css-171jvig(.*?)</section>', re.I|re.S)
            blocks = re.findall(block_pat, html)
            
            # Pattern for definitions within blocks
            defs_pat = re.compile('<span class=".+?css-1e3ziqc.+?>(.*?)</span>', re.I|re.S)
            
            if pos in ["adjective", "noun", "verb"]:
                pos_pat = re.compile('class=.+pos">(.*?)</span>', re.I|re.S)
                defs = []
                
                for block in blocks:
                    pos_extracted = re.search(pos_pat, block)
                    
                    if pos_extracted is None:
                        continue
                        
                    pos_extracted = pos_extracted.group(1)
                    
                    if pos not in pos_extracted:
                        continue
                    
                    # Filter out sentence examples and labels
                    defs += [re.sub('<span class="luna-example.+$', '', x) 
                            for x in re.findall(defs_pat, block) 
                            if "luna-label" not in x]
            else:
                # Extract all definitions
                defs = re.findall(defs_pat, " ".join(blocks))
                defs = [re.sub('<span class="luna-example.+$', '', x) 
                       for x in defs if "luna-label" not in x]
            
            # Clean HTML tags
            return [self._clean_html(x) for x in defs]
            
        except HTTPError as e:
            return self._handle_http_error(e, word, url)
        except Exception as e:
            return (None, url, f"Error: {str(e)}")

    @staticmethod
    def parse_definitions(html_content: str, pos: str = "all") -> List[str]:
        """Parse definitions from Dictionary.com HTML content.
        
        Args:
            html_content: The HTML content to parse.
            pos: Part of speech to filter by. Defaults to "all".
            
        Returns:
            List of definitions.
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        selector = SELECTORS.get(pos, SELECTORS["all"])
        definitions = soup.select(selector)
        return [def_.get_text().strip() for def_ in definitions] 