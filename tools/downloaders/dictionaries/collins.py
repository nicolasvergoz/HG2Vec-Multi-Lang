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
import random
from urllib.error import HTTPError
from bs4 import BeautifulSoup
from .base import DictionaryDownloader

class CollinsDownloader(DictionaryDownloader):
    """Collins dictionary downloader."""
    
    def __init__(self):
        super().__init__()
        self.name = "Collins"
        self.short_code = "Col"
        self.language = "en"
        
        # Liste des User-Agents plus modernes
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36'
        ]
        
        # En-têtes améliorés pour éviter la détection de bot
        self.headers = {
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'TE': 'Trailers',
            'Referer': 'https://www.collinsdictionary.com/'
        }
    
    def download(self, word, pos="all"):
        """Download definitions from Collins dictionary.
        
        Args:
            word (str): The word to look up
            pos (str): Part of speech filter (default: "all")
            
        Returns:
            tuple: (definitions, url, error_msg)
                  - definitions: liste des définitions trouvées ou None si aucune
                  - url: URL consultée pour trouver les définitions ou None
                  - error_msg: Message d'erreur ou None si aucune erreur
        """
        URL = "https://www.collinsdictionary.com/dictionary/english/" + word
        print(f"Requesting URL: {URL}")

        if pos not in ["all", "adjective", "noun", "verb"]:
            pos = "all"

        try:
            html = self.get_html(URL)
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # Vérifier le titre de la page
            print(f"Titre de la page: {soup.title.string if soup.title else 'Pas de titre'}")
            
            # Chercher les entrées et définitions
            entries = soup.select('div.dictionary.Cob_Adv_Brit.dictentry')
            print(f"Nombre d'entrées trouvées: {len(entries)}")
            
            definitions = soup.select('div.def')
            print(f"Nombre de définitions trouvées: {len(definitions)}")
            
            # Si aucune définition n'est trouvée, essayer d'autres sélecteurs
            if not definitions:
                print("Essai de sélecteurs alternatifs:")
                selectors = [
                    '.def', 
                    '.hom .sense .def',
                    '.dictionary div',
                    '.dictionary .type-def'
                ]
                for selector in selectors:
                    elements = soup.select(selector)
                    print(f"Sélecteur '{selector}': {len(elements)} éléments trouvés")
                    if elements:
                        print(f"Premier élément trouvé: {elements[0].get_text().strip()}")
            
            # Extraire toutes les définitions
            cleaned_defs = []
            for def_element in definitions:
                text = def_element.get_text().strip()
                text = re.sub(r'\s+', ' ', text)
                cleaned_defs.append(text)

            if not cleaned_defs:
                return None, URL, f"No definition found for '{word}' in Collins dictionary"
                
            return cleaned_defs, None, None

        except HTTPError as e:
            error_msg = f"HTTP Error {e.code} for '{word}' in Collins dictionary"
            print(f"ERREUR HTTP: {error_msg}")
            return None, URL, error_msg
        except UnicodeDecodeError as e:
            error_msg = f"Unicode decode error for '{word}' in Collins dictionary: {str(e)}"
            return None, URL, error_msg
        except IndexError as e:
            error_msg = f"Index error for '{word}' in Collins dictionary: {str(e)}"
            return None, URL, error_msg
        except Exception as e:
            error_msg = f"Error for '{word}' in Collins dictionary: {str(e)}"
            print(f"\nERROR: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, URL, error_msg

# Instance to be imported by the downloader module
downloader = CollinsDownloader() 