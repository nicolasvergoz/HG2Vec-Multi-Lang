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

import urllib.parse
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from .base import DictionaryDownloader, remove_diacritics

class RobertDownloader(DictionaryDownloader):
    """Le Robert dictionary downloader."""
    
    def __init__(self):
        super().__init__()
        self.name = "Le Robert"
        self.short_code = "Rob"
        self.language = "fr"
        # Update headers for French content
        self.headers['Accept-Language'] = 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'
    
    def download(self, word, pos="all"):
        """Downloads word definitions from Le Robert dictionary.
        
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
        # First remove diacritics to improve URL compatibility
        normalized_word = remove_diacritics(word)
        
        # Convert to URL-safe format
        encoded_word = urllib.parse.quote(normalized_word)
        
        URL = "https://dictionnaire.lerobert.com/definition/" + encoded_word
        
        # Also try with the original word as fallback (encoded)
        fallback_url = "https://dictionnaire.lerobert.com/definition/" + urllib.parse.quote(word)
        
        # URL actually used (will be updated if we use the fallback)
        used_url = URL

        # Le Robert has grammatical categories in French
        if pos != "all" and pos not in ["nom", "verbe", "adjectif", "adverbe"]:
            pos = "all"

        try:
            # Try first with the normalized word (without diacritics)
            html = self.get_html(URL)
            
            # Use BeautifulSoup to parse the HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check if the word exists
            if soup.find("section", class_="def") is None:
                # If the word doesn't exist with the version without diacritics, try with the original version
                if normalized_word != word:
                    print(f"\nINFO: Trying alternative URL with original spelling for '{word}'")
                    try:
                        html_fallback = self.get_html(fallback_url)
                        soup = BeautifulSoup(html_fallback, 'html.parser')
                        used_url = fallback_url
                        
                        if soup.find("section", class_="def") is None:
                            # Word not found - this is not a fatal error
                            error_msg = f"Word '{word}' not found in Le Robert"
                            print(f"\nWARNING: '{word}' not found in Le Robert dictionary.")
                            return None, used_url, error_msg
                    except HTTPError as e:
                        # Word not found - this is not a fatal error
                        error_msg = f"HTTP Error {e.code} when accessing the page with accents"
                        print(f"\nWARNING: '{word}' not found in Le Robert dictionary.")
                        return None, fallback_url, error_msg
                    except Exception as e:
                        # Any other error - this is not a fatal error
                        error_msg = f"Error when accessing the page with accents: {str(e)}"
                        print(f"\nWARNING: Error for '{word}' in Le Robert: {str(e)}")
                        return None, fallback_url, error_msg
                else:
                    # Word not found - this is not a fatal error
                    error_msg = f"Word '{word}' not found in Le Robert"
                    print(f"\nWARNING: '{word}' not found in Le Robert dictionary.")
                    return None, used_url, error_msg
                
            definitions = []
            
            # Extract all definitions
            if pos == "all":
                # Find all definition sections
                for section in soup.find_all("section", class_="def"):
                    # For each section, find all definitions with the d_dfn class
                    for def_entry in section.find_all(class_="d_dfn"):
                        definition_text = def_entry.get_text().strip()
                        if definition_text:
                            definitions.append(definition_text)
                            
                    # Also look for definitions in elements with the d_gls class
                    for gls_entry in section.find_all(class_="d_gls"):
                        gls_text = gls_entry.get_text().strip()
                        if gls_text:
                            definitions.append(gls_text)
            else:
                # Look only for definitions corresponding to the requested part of speech
                for section in soup.find_all("section", class_="def"):
                    # Check the part of speech
                    pos_element = section.find(class_="cat")
                    if pos_element and pos.lower() in pos_element.get_text().lower():
                        # Look for definitions with the d_dfn class
                        for def_entry in section.find_all(class_="d_dfn"):
                            definition_text = def_entry.get_text().strip()
                            if definition_text:
                                definitions.append(definition_text)
                        
                        # Also look for definitions in elements with the d_gls class
                        for gls_entry in section.find_all(class_="d_gls"):
                            gls_text = gls_entry.get_text().strip()
                            if gls_text:
                                definitions.append(gls_text)
            
            # If no definition is found
            if len(definitions) == 0:
                # Definition not found - this is not a fatal error
                error_msg = f"No definition found for '{word}'"
                if pos != "all":
                    error_msg += f" as {pos}"
                error_msg += " in Le Robert."
                
                warning_msg = f"No definition found for '{word}'"
                if pos != "all":
                    warning_msg += f" as {pos}"
                warning_msg += " in Le Robert."
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
            print(f"\nWARNING: HTTP error ({e.code}: {error_type}) for '{word}' in Le Robert.")
            return None, used_url, error_msg
            
        except UnicodeDecodeError as e:
            error_msg = f"Unicode decode error for '{word}': {str(e)}"
            print(f"\nWARNING: Unicode decode error for '{word}' in Le Robert.")
            return None, used_url, error_msg
            
        except Exception as e:
            error_msg = f"Technical error for '{word}': {str(e)}"
            print(f"\nWARNING: Error for '{word}' in Le Robert: {str(e)}")
            return None, used_url, error_msg

# Instance to be imported by the downloader module
downloader = RobertDownloader() 