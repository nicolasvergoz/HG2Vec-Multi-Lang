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
import gzip
import io
from urllib.error import HTTPError
from abc import ABC, abstractmethod

# Définition standard des codes courts et des noms
STANDARD_SHORT_CODES = {
    "cambridge": "Cam",
    "collins": "Col",
    "dictionary": "Dic",
    "robert": "Rob",
    "larousse": "Lar"
}

# Standard definition of short codes and names
STANDARD_SHORT_CODES = {
    "cambridge": "Cam",
    "collins": "Col",
    "dictionary": "Dic",
    "robert": "Rob",
    "larousse": "Lar"
}

# Reverse mapping for lookup by short code
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
        """Compare dictionaries by their short_code to avoid confusion.
        
        Args:
            other: The other object to compare with
            
        Returns:
            bool: True if the two dictionaries have the same short_code, False otherwise
        """
        if isinstance(other, DictionaryDownloader):
            return self.short_code == other.short_code
        # Comparison with a string (either name or short code)
        elif isinstance(other, str):
            return (self.short_code == other or 
                    self.name == other or 
                    (other in STANDARD_SHORT_CODES and self.short_code == STANDARD_SHORT_CODES[other]) or
                    (other in STANDARD_NAMES and self.name == STANDARD_NAMES[other]))
        return False
    
    def __hash__(self):
        """Hash based on short_code so the object can be used as a dictionary key."""
        return hash(self.short_code)
    
    @abstractmethod
    def download(self, word, pos="all"):
        """Download definitions for the given word.
        
        All dictionaries must return the same format: a tuple (definitions, url, error_msg)
        - If definitions are found: (list_of_definitions, None, None)
        - If no definition is found: (None, url, error_msg)
        
        Args:
            word (str): The word to look up
            pos (str): Part of speech filter (default: "all")
            
        Returns:
            tuple: (definitions, url, error_msg)
                  - definitions: list of definitions found or None if none
                  - url: URL consulted to find definitions or None
                  - error_msg: Error message or None if no error
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
        response = urllib.request.urlopen(req)
        
        # Check if the response is compressed with gzip
        if response.info().get('Content-Encoding') == 'gzip':
            content = gzip.decompress(response.read())
        else:
            content = response.read()
        
        # Try utf-8 encoding first (most common case)
        try:
            return content.decode('utf-8')
        except UnicodeDecodeError:
            # If utf-8 fails, try other common encodings
            for encoding in ['latin-1', 'iso-8859-1', 'windows-1252']:
                try:
                    return content.decode(encoding)
                except UnicodeDecodeError:
                    continue
            
            # As a last resort, use utf-8 with replacement of invalid characters
            return content.decode('utf-8', errors='replace')
    
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
        """Convert a name or short code to a standard short code.
        
        Args:
            name_or_code (str): Dictionary name or short code
            
        Returns:
            str: Standard short code
        """
        if name_or_code in STANDARD_SHORT_CODES:
            return STANDARD_SHORT_CODES[name_or_code]
        if name_or_code in STANDARD_NAMES:
            return name_or_code
        return name_or_code  # If neither, return the original value
    
    @staticmethod
    def get_standard_name(name_or_code):
        """Convert a name or short code to a standard name.
        
        Args:
            name_or_code (str): Dictionary name or short code
            
        Returns:
            str: Standard name
        """
        if name_or_code in STANDARD_NAMES:
            return STANDARD_NAMES[name_or_code]
        if name_or_code in STANDARD_SHORT_CODES:
            return name_or_code
        return name_or_code  # If neither, return the original value


def remove_diacritics(text):
    """
    Removes accents and other diacritical marks from text.
    For example: 'été' -> 'ete', 'çà' -> 'ca', 'où' -> 'ou'
    
    Args:
        text (str): Text with diacritics
        
    Returns:
        str: Text without diacritics
    """
    # Normalize the text: decompose accented characters into base character + accent
    normalized = unicodedata.normalize('NFKD', text)
    # Filter out all characters that are not ASCII letters, numbers, or simple special characters
    return ''.join([c for c in normalized if not unicodedata.combining(c)]) 