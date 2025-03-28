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

class CambridgeDownloader(DictionaryDownloader):
    """Cambridge dictionary downloader."""
    
    def __init__(self):
        super().__init__()
        self.name = "Cambridge"
        self.short_code = "Cam"
        self.language = "en"
    
    def download(self, word, pos="all"):
        """Download definitions from Cambridge dictionary.
        
        Args:
            word (str): The word to look up
            pos (str): Part of speech filter (default: "all")
            
        Returns:
            tuple: (definitions, url, error_msg)
                  - definitions: liste des définitions trouvées ou None si aucune
                  - url: URL consultée pour trouver les définitions ou None
                  - error_msg: Message d'erreur ou None si aucune erreur
        """
        URL = "https://dictionary.cambridge.org/dictionary/english/" + word

        if pos not in ["all", "adjective", "noun", "verb"]:
            pos = "all"

        try:
            html = self.get_html(URL)
            soup = BeautifulSoup(html, 'html.parser')
            
            # Utiliser le nouveau sélecteur pour trouver toutes les définitions
            all_definitions = soup.select('div.def')
            
            # Si besoin de filtrer par partie du discours (POS)
            if pos in ["adjective", "noun", "verb"]:
                cleaned_defs = []
                
                # Trouver tous les blocs d'entrée
                entry_blocks = soup.select('div.entry-body__el')
                
                for block in entry_blocks:
                    # Chercher le type de partie du discours dans ce bloc
                    pos_element = block.select_one('span.pos')
                    
                    # Si la partie du discours correspond à celle demandée
                    if pos_element and pos in pos_element.text.lower():
                        # Extraire les définitions de ce bloc
                        definitions = block.select('div.def')
                        for def_element in definitions:
                            # Extraire le texte pur et le nettoyer
                            text = def_element.get_text().strip()
                            # Normaliser les espaces
                            text = re.sub(r'\s+', ' ', text)
                            cleaned_defs.append(text)
            else:
                # Si aucun filtre de partie du discours, prendre toutes les définitions
                cleaned_defs = []
                for def_element in all_definitions:
                    # Extraire le texte pur et le nettoyer
                    text = def_element.get_text().strip()
                    # Normaliser les espaces
                    text = re.sub(r'\s+', ' ', text)
                    cleaned_defs.append(text)
            
            # Si aucune définition n'a été trouvée
            if not cleaned_defs:
                return None, URL, f"No definition found for '{word}' in Cambridge dictionary"
                
            return cleaned_defs, None, None

        except HTTPError as e:
            error_msg = f"HTTP Error {e.code} for '{word}' in Cambridge dictionary"
            return None, URL, error_msg
        except UnicodeDecodeError as e:
            error_msg = f"Unicode decode error for '{word}' in Cambridge dictionary: {str(e)}"
            return None, URL, error_msg
        except Exception as e:
            error_msg = f"Error for '{word}' in Cambridge dictionary: {str(e)}"
            print(f"\nERROR: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, URL, error_msg

# Instance to be imported by the downloader module
downloader = CambridgeDownloader() 