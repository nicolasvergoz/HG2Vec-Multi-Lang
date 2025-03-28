#!/usr/bin/env python3
#
# Copyright (c) 2017-present, All rights reserved.
# Written by Julien Tissier <30314448+tca19@users.noreply.github.com>
#
# This file is part of Dict2vec.
#
# Dict2vec is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Dict2vec is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License at the root of this repository for
# more details.
#
# You should have received a copy of the GNU General Public License
# along with Dict2vec.  If not, see <http://www.gnu.org/licenses/>.

import re
from urllib.error import HTTPError
from .base import DictionaryDownloader

class DictionaryDotComDownloader(DictionaryDownloader):
    """Dictionary.com dictionary downloader."""
    
    def __init__(self):
        super().__init__()
        self.name = "Dictionary.com"
        self.short_code = "Dic"
        self.language = "en"
    
    def download(self, word, pos="all"):
        """Download definitions from Dictionary.com.
        
        Args:
            word (str): The word to look up
            pos (str): Part of speech filter (default: "all")
            
        Returns:
            tuple: (definitions, url, error_msg)
                  - definitions: liste des définitions trouvées ou None si aucune
                  - url: URL consultée pour trouver les définitions ou None
                  - error_msg: Message d'erreur ou None si aucune erreur
        """
        URL = "http://www.dictionary.com/browse/" + word

        if pos not in ["all", "adjective", "noun", "verb"]:
            pos = "all"

        try:
            html = self.get_html(URL)

            # New pattern to match the updated selector div.NZKOFkdkcvYgD3lqOIJw > div
            defs_pat = re.compile('<div class="NZKOFkdkcvYgD3lqOIJw"><div>(.*?)</div></div>', re.I|re.S)
            
            # Extract sections based on POS if needed
            if pos in ["adjective", "noun", "verb"]:
                # For filtering by POS, we need to adapt this part to the new HTML structure
                # This is a placeholder - the exact implementation would depend on how POS is marked in the new structure
                # This is a placeholder - the exact implementation would depend on how POS is marked in the new structure
                pos_pat = re.compile('class=.+pos">(.*?)</span>', re.I|re.S)
                sections = re.findall(pos_pat, html)
                
                # Extract definitions from sections matching the requested POS
                raw_defs = []
                for section in sections:
                    if pos in section.lower():
                        raw_defs.extend(re.findall(defs_pat, section))
            else:
                # Extract all definitions without filtering by POS
                raw_defs = re.findall(defs_pat, html)
            
            # Clean the definitions by removing all HTML tags and normalizing whitespace
            cleaned_defs = []
            for def_text in raw_defs:
                # Remove HTML tags but preserve the text content
                cleaned = self.clean_html(def_text, '<.+?>')
                # Remove comment tags and normalize whitespace
                cleaned = re.sub('<!--\s*-->', ' ', cleaned)
                cleaned = re.sub('\s+', ' ', cleaned).strip()
                cleaned_defs.append(cleaned)
            
            if not cleaned_defs:
                return None, URL, f"No definition found for '{word}' in Dictionary.com"
                
            return cleaned_defs, None, None

        except HTTPError as e:
            error_msg = f"HTTP Error {e.code} for '{word}' in Dictionary.com"
            return None, URL, error_msg
        except UnicodeDecodeError as e:
            error_msg = f"Unicode decode error for '{word}' in Dictionary.com: {str(e)}"
            return None, URL, error_msg
        except IndexError as e:
            error_msg = f"Index error for '{word}' in Dictionary.com: {str(e)}"
            return None, URL, error_msg
        except Exception as e:
            error_msg = f"Error for '{word}' in Dictionary.com: {str(e)}"
            print("\nERROR: * timeout error.")
            print("       * retry dictionary.com -", word)
            return None, URL, error_msg

# Instance to be imported by the downloader module
downloader = DictionaryDotComDownloader() 