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

# Chargement des stopwords anglais
STOPWORDS_EN = set()
try:
    with open('dict-dl/stopwords_en.txt') as f:
        for line in f:
            STOPWORDS_EN.add(line.strip().lower())
except FileNotFoundError:
    print("WARNING: English stopwords file not found")

# Chargement des stopwords français
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
        tuple(None, str, str): si le mot n'a pas de définition ou erreur
    """
    try:
        # Get the appropriate downloader - on utilise le nom ou le code court
        downloader = get_downloader(dict_name)
                
        # cleanup the word
        original_word = word  # Garder le mot original pour les messages d'erreur
        if clean:
            # remove trailing punctuation and make it lowercase
            for p in string.punctuation:
                word = word.replace(p, "")
            word = word.lower()
                
        # Obtenir les définitions - format standardisé (definitions, url, error_msg)
        definitions, url, error_msg = downloader.download(word, pos)
        
        # Si aucune définition n'est trouvée, on retourne le tuple d'erreur
        if definitions is None:
            return None, url, error_msg
        
        # Si on est arrivé ici, c'est qu'on a des définitions
        words = []
        # Sélectionner le set de stopwords approprié selon le dictionnaire
        stopwords = STOPWORDS_EN
        if downloader.language == "fr":
            stopwords = STOPWORDS_FR
        
        for definition in definitions: # there can be more than one definition fetched
            # if no cleaning needed, add the whole definition
            if not clean:
                words.append(definition)
                continue

            # Pour le français, traiter spécialement les apostrophes
            if downloader.language == "fr":
                # Pré-traitement: remplacer les apostrophes par un espace + le mot
                # Exemple: "l'une" devient "l une" au lieu de "lune"
                processed_def = definition.replace("'", " ")
                processed_def = processed_def.replace("'", " ")  # Apostrophe typographique
                
                # Découper la définition en mots en utilisant les espaces
                for word in processed_def.split():
                    # Nettoyer chaque mot en gardant les accents mais en retirant les caractères non-alphabétiques
                    word = ''.join([c.lower() for c in word if c.isalpha()])
                    if word and word not in stopwords:
                        words.append(word)
            else:
                # Pour l'anglais, continuer avec le traitement existant
                for word in definition.split():
                    word = ''.join([c.lower() for c in word if c.isalpha() and ord(c) < 128])
                    if word and word not in stopwords:
                        words.append(word)

        return words
        
    except Exception as e:
        # Toutes les erreurs sont considérées comme non fatales
        dict_name_display = dict_name
        try:
            # Si on a pu obtenir le downloader, utiliser son nom complet
            dict_name_display = downloader.name
        except:
            pass
            
        error_msg = f"Erreur pour '{original_word}' dans {dict_name_display}: {str(e)}"
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

    print("\n\n-- TEST : definitions according to POS of alert --")
    print("dictionary.com -- alert [ADJECTIVE]")
    print(download_word_definition("dictionary", "alert", "adjective"))
    print()
    print("dictionary.com -- alert [NOUN]")
    print(download_word_definition("dictionary", "alert", "noun"))
    print()
    print("dictionary.com -- alert [VERB]")
    print(download_word_definition("dictionary", "alert", "verb"))
    print()
    print("dictionary.com -- alert [ALL]")
    print(download_word_definition("dictionary", "alert", "all"))
    print()
    print("Le Robert -- chat [nom]")
    print(download_word_definition("robert", "chat", "nom"))
    print()

    # Test des méthodes de comparaison
    print("\n-- TEST : comparaison des objets dictionnaires --")
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
