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
        """Télécharge les définitions du mot depuis le dictionnaire Le Robert.
        
        Args:
            word (str): le mot dont on veut télécharger la définition
            pos (str): partie du discours. Si différent de 'all', ne retourne
                    que les définitions pour cette partie du discours.
                    
        Returns:
            tuple: (definitions, url, error_msg)
                  - definitions: liste des définitions trouvées ou None si aucune
                  - url: URL consultée pour trouver les définitions ou None
                  - error_msg: Message d'erreur ou None si aucune erreur
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

        # Le Robert a des catégories grammaticales en français
        if pos != "all" and pos not in ["nom", "verbe", "adjectif", "adverbe"]:
            pos = "all"

        try:
            # Try first with the normalized word (without diacritics)
            html = self.get_html(URL)
            
            # Utiliser BeautifulSoup pour parser le HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Vérifier si le mot existe
            if soup.find("section", class_="def") is None:
                # Si le mot n'existe pas avec version sans diacritiques, essayer avec la version originale
                if normalized_word != word:
                    print(f"\nINFO: Trying alternative URL with original spelling for '{word}'")
                    try:
                        html_fallback = self.get_html(fallback_url)
                        soup = BeautifulSoup(html_fallback, 'html.parser')
                        used_url = fallback_url
                        
                        if soup.find("section", class_="def") is None:
                            # Mot non trouvé - ce n'est pas une erreur fatale
                            error_msg = f"Mot '{word}' non trouvé dans Le Robert"
                            print(f"\nWARNING: '{word}' not found in Le Robert dictionary.")
                            return None, used_url, error_msg
                    except HTTPError as e:
                        # Mot non trouvé - ce n'est pas une erreur fatale
                        error_msg = f"HTTP Error {e.code} lors de l'accès à la page avec accents"
                        print(f"\nWARNING: '{word}' not found in Le Robert dictionary.")
                        return None, fallback_url, error_msg
                    except Exception as e:
                        # Toute autre erreur - ce n'est pas une erreur fatale
                        error_msg = f"Erreur lors de l'accès à la page avec accents: {str(e)}"
                        print(f"\nWARNING: Error for '{word}' in Le Robert: {str(e)}")
                        return None, fallback_url, error_msg
                else:
                    # Mot non trouvé - ce n'est pas une erreur fatale
                    error_msg = f"Mot '{word}' non trouvé dans Le Robert"
                    print(f"\nWARNING: '{word}' not found in Le Robert dictionary.")
                    return None, used_url, error_msg
                
            definitions = []
            
            # Extraire toutes les définitions
            if pos == "all":
                # Trouver toutes les sections de définition
                for section in soup.find_all("section", class_="def"):
                    # Pour chaque section, trouver toutes les définitions avec la classe d_dfn
                    for def_entry in section.find_all(class_="d_dfn"):
                        definition_text = def_entry.get_text().strip()
                        if definition_text:
                            definitions.append(definition_text)
                            
                    # Chercher également les définitions dans les éléments avec la classe d_gls
                    for gls_entry in section.find_all(class_="d_gls"):
                        gls_text = gls_entry.get_text().strip()
                        if gls_text:
                            definitions.append(gls_text)
            else:
                # Chercher uniquement les définitions correspondant à la partie du discours demandée
                for section in soup.find_all("section", class_="def"):
                    # Vérifier la partie du discours
                    pos_element = section.find(class_="cat")
                    if pos_element and pos.lower() in pos_element.get_text().lower():
                        # Chercher les définitions avec la classe d_dfn
                        for def_entry in section.find_all(class_="d_dfn"):
                            definition_text = def_entry.get_text().strip()
                            if definition_text:
                                definitions.append(definition_text)
                        
                        # Chercher également les définitions dans les éléments avec la classe d_gls
                        for gls_entry in section.find_all(class_="d_gls"):
                            gls_text = gls_entry.get_text().strip()
                            if gls_text:
                                definitions.append(gls_text)
            
            # Si aucune définition n'est trouvée
            if len(definitions) == 0:
                # Définition non trouvée - ce n'est pas une erreur fatale
                error_msg = f"Aucune définition trouvée pour '{word}'"
                if pos != "all":
                    error_msg += f" en tant que {pos}"
                error_msg += " dans Le Robert."
                
                warning_msg = f"No definition found for '{word}'"
                if pos != "all":
                    warning_msg += f" as {pos}"
                warning_msg += " in Le Robert."
                print(f"\nWARNING: {warning_msg}")
                return None, used_url, error_msg
                
            return definitions, None, None
            
        except HTTPError as e:
            # Toutes les erreurs HTTP sont considérées comme non fatales
            error_type = {
                404: "not found",
                504: "Gateway Timeout",
                502: "Bad Gateway",
                503: "Service Unavailable"
            }.get(e.code, f"HTTP error {e.code}")
            
            error_msg = f"Error {e.code}: {error_type} pour '{word}'"
            print(f"\nWARNING: HTTP error ({e.code}: {error_type}) for '{word}' in Le Robert.")
            return None, used_url, error_msg
            
        except UnicodeDecodeError as e:
            error_msg = f"Unicode decode error pour '{word}': {str(e)}"
            print(f"\nWARNING: Unicode decode error for '{word}' in Le Robert.")
            return None, used_url, error_msg
            
        except Exception as e:
            error_msg = f"Erreur technique pour '{word}': {str(e)}"
            print(f"\nWARNING: Error for '{word}' in Le Robert: {str(e)}")
            return None, used_url, error_msg

# Instance to be imported by the downloader module
downloader = RobertDownloader() 