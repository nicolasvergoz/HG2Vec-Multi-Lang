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
from bs4 import BeautifulSoup
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
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all definitions using the CSS selector
            definition_elements = soup.select('div.NZKOFkdkcvYgD3lqOIJw > div')
            
            # Extract definitions and filter by POS if needed
            cleaned_defs = []
            
            if pos in ["adjective", "noun", "verb"]:
                # We need to find sections with the requested POS
                # This implementation depends on the actual structure of Dictionary.com
                # Assuming POS information is available in elements with a certain class
                sections = soup.find_all(lambda tag: tag.name == 'span' and 
                                                    'pos' in tag.get('class', []))
                
                for section in sections:
                    if pos in section.text.lower():
                        # Find the parent section containing this POS
                        parent_section = section.find_parent('section')
                        if parent_section:
                            # Find all definitions in this section
                            pos_definitions = parent_section.select('div.NZKOFkdkcvYgD3lqOIJw > div')
                            for def_element in pos_definitions:
                                # Get text content only
                                text = def_element.get_text().strip()
                                # Normalize whitespace
                                text = re.sub(r'\s+', ' ', text)
                                cleaned_defs.append(text)
            else:
                # Extract all definitions if no POS filter
                for def_element in definition_elements:
                    # Get text content only
                    text = def_element.get_text().strip()
                    # Normalize whitespace
                    text = re.sub(r'\s+', ' ', text)
                    cleaned_defs.append(text)
            
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