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

import string
from dictionaries import get_downloader, DictionaryDownloader

# Load English stopwords
STOPWORDS_EN = set()
try:
    with open('dict-dl/stopwords_en.txt') as f:
        for line in f:
            STOPWORDS_EN.add(line.strip().lower())
except FileNotFoundError:
    print("WARNING: English stopwords file not found")

# Load French stopwords
STOPWORDS_FR = set()
try:
    with open('dict-dl/stopwords_fr.txt') as f:
        for line in f:
            STOPWORDS_FR.add(line.strip().lower())
except FileNotFoundError:
    print("WARNING: French stopwords file not found")

def download_word_definition(dict_name, word, pos="all", clean=True):
    """Download the definition(s) of WORD according to the part-of-speech POS
       from the dictionary DICT_NAME.

    Args:
        dict_name (str): name of the dictionary. Can be: 'cambridge', 'collins',
                         'dictionary', or 'robert'
        word (str): the word we want to download definition
        pos (str): part-of-speech of the wanted definition. Can be:
                   'all' (default), 'adjective', 'adverb', 'noun' or 'verb'
        clean (bool): whether to cleanup the word or not.
                      The cleanup consists in removing trailing ...
                      ... punctuations and making it lowercase.

    Returns:
        list: definitions of WORD according to POS
        tuple(None, str, str): if the word has no definition or error
    """
    try:
        # Get the appropriate downloader - use the name or short code
        downloader = get_downloader(dict_name)
                
        # cleanup the word
        original_word = word  # Keep the original word for error messages
        if clean:
            # remove trailing punctuation and make it lowercase
            for p in string.punctuation:
                word = word.replace(p, "")
            word = word.lower()
                
        # Get definitions - standardized format (definitions, url, error_msg)
        definitions, url, error_msg = downloader.download(word, pos)
        
        # If no definition is found, return the error tuple
        if definitions is None:
            return None, url, error_msg
        
        # If we got here, we have definitions
        words = []
        # Select the appropriate stopwords set based on the dictionary
        stopwords = STOPWORDS_EN
        if downloader.language == "fr":
            stopwords = STOPWORDS_FR
        
        for definition in definitions: # there can be more than one definition fetched
            # if no cleaning needed, add the whole definition
            if not clean:
                words.append(definition)
                continue

            # For French, handle apostrophes specially
            if downloader.language == "fr":
                # Pre-processing: replace apostrophes with space + word
                # Example: "l'une" becomes "l une" instead of "lune"
                processed_def = definition.replace("'", " ")
                processed_def = processed_def.replace("'", " ")  # Typographic apostrophe
                
                # Split definition into words using spaces
                for word in processed_def.split():
                    # Clean each word keeping accents but removing non-alphabetic characters
                    word = ''.join([c.lower() for c in word if c.isalpha()])
                    if word and word not in stopwords:
                        words.append(word)
            else:
                # For English, continue with existing processing
                for word in definition.split():
                    word = ''.join([c.lower() for c in word if c.isalpha() and ord(c) < 128])
                    if word and word not in stopwords:
                        words.append(word)

        return words
        
    except Exception as e:
        # All errors are considered non-fatal
        dict_name_display = dict_name
        try:
            # If we could get the downloader, use its full name
            dict_name_display = downloader.name
        except:
            pass
            
        error_msg = f"Error for '{original_word}' in {dict_name_display}: {str(e)}"
        print(f"\nWARNING: Error for '{original_word}' in {dict_name_display}: {str(e)}")
        
        return None, "", error_msg

if __name__ == '__main__':
    print("-- TEST : definitions of wick --")
    print("Cambridge")
    print(download_word_definition("cambridge", "wick", "all"))
    print("\ndictionary.com")
    print(download_word_definition("dictionary", "wick", "all"))
    print("\nCollins")
    print(download_word_definition("collins", "wick", "all"))
    print("\nLe Robert")
    print(download_word_definition("robert", "chat", "all"))

    # Test des méthodes de comparaison
    print("\n-- TEST : comparison of dictionary objects --")
    cambridge = get_downloader("cambridge")
    cam_code = get_downloader("Cam")
    print(f"cambridge == Cam: {cambridge == cam_code}")
    print(f"cambridge == 'cambridge': {cambridge == 'cambridge'}")
    print(f"cambridge == 'Cam': {cambridge == 'Cam'}")
    
    robert = get_downloader("robert")
    print(f"robert.language: {robert.language}")
    print(f"cambridge.language: {cambridge.language}")
    print(f"robert == cambridge: {robert == cambridge}")
    print(f"robert == 'Rob': {robert == 'Rob'}")
    print(f"robert == 'robert': {robert == 'robert'}")
