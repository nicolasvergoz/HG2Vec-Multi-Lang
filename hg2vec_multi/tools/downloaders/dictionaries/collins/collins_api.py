"""Collins dictionary API implementation."""

import re
import urllib.request
from typing import List, Tuple, Union
from urllib.error import HTTPError

from hg2vec_multi.tools.downloaders.dictionaries.dictionary_api import DictionaryAPI
from hg2vec_multi.tools.downloaders.dictionary_config import DICT_URLS, USER_AGENTS
from .config import URL, SELECTORS, SUPPORTED_LANGUAGES


class CollinsAPI(DictionaryAPI):
    """Collins dictionary API implementation."""
    
    @property
    def URL(self) -> str:
        return URL
    
    @property
    def SELECTORS(self) -> dict:
        return SELECTORS
    
    @property
    def SUPPORTED_LANGUAGES(self) -> List[str]:
        return SUPPORTED_LANGUAGES
    
    @staticmethod
    def parse_definitions(html_content: str, pos: str = "all") -> List[str]:
        """Parse definitions from Collins dictionary HTML content.
        
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
    
    def __init__(self):
        """Initialize the Collins Dictionary API."""
        super().__init__("collins")
    
    def get_definition(self, word: str, pos: str = "all") -> Union[List[str], Tuple[None, str, str]]:
        """Get the definition from Collins Dictionary.
        
        Args:
            word: The word to look up
            pos: Part of speech (noun, verb, adjective, or all)
            
        Returns:
            List of definitions or a tuple (None, url, error_message) if not found
        """
        if pos not in ["all", "adjective", "noun", "verb"]:
            pos = "all"
            
        # Collins URL is not in the config, using a hard-coded URL
        url = f"https://www.collinsdictionary.com/dictionary/english/{word}"
        
        # Collins has server restrictions - need to spoof headers
        headers = {
            'User-Agent': USER_AGENTS[0],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
        }
        req = urllib.request.Request(url, headers=headers)
        
        try:
            html = urllib.request.urlopen(req, context=self.ssl_context).read().decode('utf-8')
            
            # Extract definition blocks
            block_p = re.compile('<div class="content definitions.+?"(.*?)<div class="div copyright', re.I|re.S)
            blocks = " ".join(re.findall(block_p, html))
            
            # Pattern for definitions
            defs_pat = re.compile('<div class="def">(.+?)</div>', re.I|re.S)
            
            if pos in ["adjective", "noun", "verb"]:
                sense_pat = re.compile('<div class="hom">', re.I|re.S)
                idx = [m.start() for m in sense_pat.finditer(blocks)]
                idx.append(len(blocks))
                span = [(idx[i], idx[i+1]) for i in range(len(idx)-1)]
                
                pos_pat = re.compile('class="pos">(.*?)</span>', re.I|re.S)
                defs = []
                
                for start, end in span:
                    pos_extracted = re.search(pos_pat, blocks[start:end])
                    
                    if pos_extracted is None:
                        continue
                        
                    pos_extracted = pos_extracted.group(1)
                    
                    if pos not in pos_extracted:
                        continue
                        
                    defs += re.findall(defs_pat, blocks[start:end])
            else:
                # Extract all definitions
                defs = re.findall(defs_pat, blocks)
            
            # Clean HTML tags
            return [self._clean_html(x) for x in defs]
            
        except HTTPError as e:
            return self._handle_http_error(e, word, url)
        except Exception as e:
            return (None, url, f"Error: {str(e)}") 