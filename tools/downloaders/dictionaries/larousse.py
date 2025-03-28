#!/usr/bin/env python3
#
# Copyright (c) 2017-present, All rights reserved.
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
import urllib.parse
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from .base import DictionaryDownloader, remove_diacritics

class LarousseDownloader(DictionaryDownloader):
    """Larousse dictionary downloader for French."""
    
    def __init__(self):
        super().__init__()
        self.name = "Larousse"
        self.short_code = "Lar"
        self.language = "fr"
        # Update headers for French content
        self.headers['Accept-Language'] = 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'
    
    def download(self, word, pos="all"):
        """Downloads word definitions from the Larousse dictionary.
        
        Args:
            word (str): the word to look up
            pos (str): part of speech. If different from 'all', returns
                    only definitions for this part of speech.
                    
        Returns:
            tuple: (definitions, url, error_msg)
                  - definitions: list of definitions found or None if none
                  - url: URL consulted to find definitions or None
                  - error_msg: Error message or None if no error
        """
        # Encode URL with special characters
        encoded_word = urllib.parse.quote(word)
        
        URL = "https://www.larousse.fr/dictionnaires/francais/" + encoded_word
        used_url = URL

        # Larousse has grammatical categories in French
        if pos != "all" and pos not in ["nom", "verbe", "adjectif", "adverbe"]:
            pos = "all"

        try:
            html = self.get_html(URL)
            
            # Use BeautifulSoup to parse the HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check if the word exists
            definitions_list = soup.select('ul.Definitions > li.DivisionDefinition')
            
            if not definitions_list:
                # Word not found - this is not a fatal error
                error_msg = f"Word '{word}' not found in Larousse"
                print(f"\nWARNING: '{word}' not found in Larousse dictionary.")
                return None, used_url, error_msg
                
            definitions = []
            
            # Extract all definitions according to the provided selector
            for definition_element in definitions_list:
                # Create a copy of the element to avoid modifying the original
                definition_copy = BeautifulSoup(str(definition_element), 'html.parser')
                
                # Remove all span tags and their content
                for span in definition_copy.find_all('span'):
                    span.decompose()
                
                # Remove synonym paragraphs and their content
                for p in definition_copy.find_all('p', class_=['LibelleSynonyme', 'Synonymes']):
                    p.decompose()
                
                # Remove definition examples
                for example in definition_copy.find_all(class_='ExempleDefinition'):
                    example.decompose()
                
                # Get the cleaned text
                clean_text = definition_copy.get_text().strip()
                
                # Clean extra whitespace
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                # Add the cleaned definition
                if clean_text:
                    definitions.append(clean_text)
            
            # If no definition is found
            if len(definitions) == 0:
                # Definition not found - this is not a fatal error
                error_msg = f"No definition found for '{word}'"
                if pos != "all":
                    error_msg += f" as {pos}"
                error_msg += " in Larousse."
                
                warning_msg = f"No definition found for '{word}'"
                if pos != "all":
                    warning_msg += f" as {pos}"
                warning_msg += " in Larousse."
                print(f"\nWARNING: {warning_msg}")
                return None, used_url, error_msg
                
            return definitions, None, None
            
        except HTTPError as e:
            # All HTTP errors are considered non-fatal
            error_type = {
                404: "not found",
                504: "Gateway Timeout",
                502: "Bad Gateway",
                503: "Service Unavailable"
            }.get(e.code, f"HTTP error {e.code}")
            
            error_msg = f"Error {e.code}: {error_type} for '{word}'"
            print(f"\nWARNING: HTTP error ({e.code}: {error_type}) for '{word}' in Larousse.")
            return None, used_url, error_msg
            
        except UnicodeDecodeError as e:
            error_msg = f"Unicode decode error for '{word}': {str(e)}"
            print(f"\nWARNING: Unicode decode error for '{word}' in Larousse.")
            return None, used_url, error_msg
            
        except Exception as e:
            error_msg = f"Technical error for '{word}': {str(e)}"
            print(f"\nWARNING: Error for '{word}' in Larousse: {str(e)}")
            return None, used_url, error_msg

# Instance to be imported by the downloader module
downloader = LarousseDownloader() 