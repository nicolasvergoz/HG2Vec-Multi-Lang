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
        """Télécharge les définitions du mot depuis le dictionnaire Larousse.
        
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
        encoded_word = urllib.parse.quote(word)
        
        URL = "https://www.larousse.fr/dictionnaires/francais/" + encoded_word
        used_url = URL

        # Larousse a des catégories grammaticales en français
        if pos != "all" and pos not in ["nom", "verbe", "adjectif", "adverbe"]:
            pos = "all"

        try:
            html = self.get_html(URL)
            
            # Utiliser BeautifulSoup pour parser le HTML
            soup = BeautifulSoup(html, 'html.parser')
            
            # Vérifier si le mot existe
            definitions_list = soup.select('ul.Definitions > li.DivisionDefinition')
            
            if not definitions_list:
                # Mot non trouvé - ce n'est pas une erreur fatale
                error_msg = f"Mot '{word}' non trouvé dans Larousse"
                print(f"\nWARNING: '{word}' not found in Larousse dictionary.")
                return None, used_url, error_msg
                
            definitions = []
            
            # Extraire toutes les définitions selon le sélecteur fourni
            for definition_element in definitions_list:
                # On doit extraire le texte mais ignorer le contenu des balises span
                # Approche: récupérer le texte complet puis nettoyer
                raw_text = definition_element.get_text()
                
                # Obtenir le texte brut de l'élément
                raw_text = definition_element.encode_contents().decode()
                
                # Nettoyer les balises span et leur contenu
                clean_text = re.sub(r'<span.*?</span>', '', raw_text)
                
                # Nettoyer les autres balises HTML mais conserver leur contenu
                clean_text = re.sub(r'<.*?>', '', clean_text)
                
                # Nettoyer les espaces superflus
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()
                
                # Pour une approche plus directe, on peut aussi parcourir les enfants directs
                alternative_text = ""
                for content in definition_element.contents:
                    # Ignorer les balises span
                    if content.name != 'span' and content.string:
                        alternative_text += content.string
                
                # Utiliser le texte alternatif s'il est plus propre
                if alternative_text.strip():
                    clean_text = alternative_text.strip()
                
                # Ajouter la définition nettoyée
                if clean_text:
                    definitions.append(clean_text)
            
            # Si aucune définition n'est trouvée
            if len(definitions) == 0:
                # Définition non trouvée - ce n'est pas une erreur fatale
                error_msg = f"Aucune définition trouvée pour '{word}'"
                if pos != "all":
                    error_msg += f" en tant que {pos}"
                error_msg += " dans Larousse."
                
                warning_msg = f"No definition found for '{word}'"
                if pos != "all":
                    warning_msg += f" as {pos}"
                warning_msg += " in Larousse."
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
            print(f"\nWARNING: HTTP error ({e.code}: {error_type}) for '{word}' in Larousse.")
            return None, used_url, error_msg
            
        except UnicodeDecodeError as e:
            error_msg = f"Unicode decode error pour '{word}': {str(e)}"
            print(f"\nWARNING: Unicode decode error for '{word}' in Larousse.")
            return None, used_url, error_msg
            
        except Exception as e:
            error_msg = f"Erreur technique pour '{word}': {str(e)}"
            print(f"\nWARNING: Error for '{word}' in Larousse: {str(e)}")
            return None, used_url, error_msg

# Instance to be imported by the downloader module
downloader = LarousseDownloader() 