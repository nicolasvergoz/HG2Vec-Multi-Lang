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
import string
import unicodedata
import urllib.request
from urllib.error import HTTPError
from abc import ABC, abstractmethod

# Définition standard des codes courts et des noms
STANDARD_SHORT_CODES = {
    "cambridge": "Cam",
    "collins": "Col",
    "dictionary": "Dic",
    "robert": "Rob"
}

# Correspondance inverse pour la recherche par code court
STANDARD_NAMES = {v: k for k, v in STANDARD_SHORT_CODES.items()}

class DictionaryDownloader:
    """Base class for dictionary downloaders."""
    
    def __init__(self):
        self.name = "base"  # Override in subclasses
        self.short_code = "base"  # Override in subclasses
        self.language = "en"  # Override in subclasses with "en" or "fr"
        self.headers = {
            'User-Agent':
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like '
                'Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept':
                'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Encoding':
                'none',
            'Accept-Language':
                'en-US,en;q=0.8',
        }
    
    def __eq__(self, other):
        """Compare dictionnaires par leur short_code pour éviter les confusions.
        
        Args:
            other: L'autre objet à comparer
            
        Returns:
            bool: True si les two dictionnaires ont le même short_code, False sinon
        """
        if isinstance(other, DictionaryDownloader):
            return self.short_code == other.short_code
        # Comparaison avec un string (soit nom, soit code court)
        elif isinstance(other, str):
            return (self.short_code == other or 
                    self.name == other or 
                    (other in STANDARD_SHORT_CODES and self.short_code == STANDARD_SHORT_CODES[other]) or
                    (other in STANDARD_NAMES and self.name == STANDARD_NAMES[other]))
        return False
    
    def __hash__(self):
        """Hachage basé sur le short_code pour que l'objet soit utilisable comme clé de dictionnaire."""
        return hash(self.short_code)
    
    @abstractmethod
    def download(self, word, pos="all"):
        """Download definitions for the given word.
        
        Tous les dictionnaires doivent retourner le même format: un tuple (definitions, url, error_msg)
        - Si des définitions sont trouvées: (list_of_definitions, None, None)
        - Si aucune définition n'est trouvée: (None, url, error_msg)
        
        Args:
            word (str): The word to look up
            pos (str): Part of speech filter (default: "all")
            
        Returns:
            tuple: (definitions, url, error_msg)
                  - definitions: liste des définitions trouvées ou None si aucune
                  - url: URL consultée pour trouver les définitions ou None
                  - error_msg: Message d'erreur ou None si aucune erreur
        """
        pass
    
    def get_html(self, url):
        """Fetch HTML content from URL with proper headers.
        
        Args:
            url (str): URL to fetch
            
        Returns:
            str: HTML content
            
        Raises:
            HTTPError: If server returns an error
            UnicodeDecodeError: If content cannot be decoded
        """
        req = urllib.request.Request(url, headers=self.headers)
        return urllib.request.urlopen(req).read().decode('utf-8')
    
    def clean_html(self, html, pattern):
        """Clean HTML tags from text.
        
        Args:
            html (str): HTML content
            pattern (str): Regex pattern for HTML tags
            
        Returns:
            str: Cleaned text
        """
        cleaner = re.compile(pattern, re.I|re.S)
        return re.sub(cleaner, '', html)
    
    @staticmethod
    def get_standard_short_code(name_or_code):
        """Convertit un nom ou un code court en code court standard.
        
        Args:
            name_or_code (str): Nom du dictionnaire ou code court
            
        Returns:
            str: Code court standard
        """
        if name_or_code in STANDARD_SHORT_CODES:
            return STANDARD_SHORT_CODES[name_or_code]
        if name_or_code in STANDARD_NAMES:
            return name_or_code
        return name_or_code  # Si ni l'un ni l'autre, retourne la valeur d'origine
    
    @staticmethod
    def get_standard_name(name_or_code):
        """Convertit un nom ou un code court en nom standard.
        
        Args:
            name_or_code (str): Nom du dictionnaire ou code court
            
        Returns:
            str: Nom standard
        """
        if name_or_code in STANDARD_NAMES:
            return STANDARD_NAMES[name_or_code]
        if name_or_code in STANDARD_SHORT_CODES:
            return name_or_code
        return name_or_code  # Si ni l'un ni l'autre, retourne la valeur d'origine


def remove_diacritics(text):
    """
    Supprime les accents et autres caractères diacritiques d'un texte.
    Par exemple: 'été' -> 'ete', 'çà' -> 'ca', 'où' -> 'ou'
    
    Args:
        text (str): Texte avec diacritiques
        
    Returns:
        str: Texte sans diacritiques
    """
    # Normalise le texte: décompose les caractères accentués en caractère de base + accent
    normalized = unicodedata.normalize('NFKD', text)
    # Filtre tous les caractères qui ne sont pas des lettres ASCII, des chiffres ou des caractères spéciaux simples
    return ''.join([c for c in normalized if not unicodedata.combining(c)]) 