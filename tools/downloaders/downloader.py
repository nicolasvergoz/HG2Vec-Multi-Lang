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

from urllib.error import HTTPError
import urllib.request
import re
from bs4 import BeautifulSoup
import string
import urllib.parse
import unicodedata

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

def download_cambridge(word, pos="all"):
    URL = "http://dictionary.cambridge.org/dictionary/english/" + word

    if pos not in ["all", "adjective", "noun", "verb"]:
        pos = "all"

    try:
        html = urllib.request.urlopen(URL).read().decode('utf-8')

        # definitions are in a <b> tag that has the class "def"
        defs_pat = re.compile('<b class="def">(.*?)</b>', re.I|re.S)

        # need to extract definitions only if it's a certain pos type
        if pos in ["adjective", "noun", "verb"]:

            # each type entry (adj, noun or verb) is in a "entry-body__el"
            # block. A word might have many blocks (if it is both a noun and a
            # verb, it will have 2 blocks). Moreover, there are also different
            # blocks for British or American language. I can't extract blocks
            # because there is no ending regex that works for every word, so I
            # consider a block to be between the indexes of 2 consecutive
            # block_pat matches. Last block goes to the end of html string.
            block_pat = re.compile('<div class="entry-body__el ', re.I|re.S)
            idx = [m.start() for m in block_pat.finditer(html)] + [len(html)]
            span = [(idx[i], idx[i+1]) for i in range(len(idx)-1)]

            # then for each block, I only extract the definitions if it matches
            # the pos argument
            pos_pat = re.compile('class="pos".*?>(.*?)</span>', re.I|re.S)
            defs = []

            for start, end in span:
                pos_extracted = re.search(pos_pat, html[start:end])

                # some words (like mice) do not have a pos info, so no pos
                # extracted
                if pos_extracted is None:
                    continue

                pos_extracted = pos_extracted.group(1)

                if pos_extracted != pos:
                    continue

                defs += re.findall(defs_pat, html[start:end])

        # otherwise extract all definitions available
        else:
            defs = re.findall(defs_pat, html)

        # need to clean definitions of <a> and <span> tags. Use cleaner to
        # replace these tags by empty string
        cleaner = re.compile('<.+?>', re.I|re.S)
        return [ re.sub(cleaner, '', x) for x in defs ]

    except HTTPError:
        return -1
    except UnicodeDecodeError:
        return -1
    except Exception as e:
        print("\nERROR: * timeout error.")
        print("       * retry Cambridge -", word)
        return -1

def download_dictionary(word, pos="all"):
    URL = "http://www.dictionary.com/browse/" + word

    if pos not in ["all", "adjective", "noun", "verb"]:
        pos = "all"

    try:
        html = urllib.request.urlopen(URL).read().decode('utf-8')

        # definitions are in <section> tags with class "css-171jvig". Each POS
        # type has its own <section>, so extract them all.
        block_pat = re.compile('<section class="css-171jvig(.*?)</section>',
                               re.I|re.S)
        blocks = re.findall(block_pat, html)

        # inside each block, definitions are in <span> tags with the class
        # "css-1e3ziqc". Sometimes there is another class, so use the un-greedy
        # regex pattern .+? to go until the closing '>' of the opening <span>
        # tag.
        defs_pat = re.compile('<span class=".+?css-1e3ziqc.+?>(.*?)</span>', re.I|re.S)

        # need to extract definitions only if it's a certain pos type
        if pos in ["adjective", "noun", "verb"]:

            # for each block, if the extracted POS matches the pos argument, add
            # the definitions in defs (.+ because class is either luna-pos or
            # pos)
            pos_pat = re.compile('class=.+pos">(.*?)</span>', re.I|re.S)
            defs = []

            for block in blocks:
                pos_extracted = re.search(pos_pat, block)

                # some words (like cia) do not have a pos info so no pos
                # extracted
                if pos_extracted is None:
                    continue

                pos_extracted = pos_extracted.group(1)

                if pos not in pos_extracted:
                    continue

                # remove possible sentence examples in definitions and possible
                # non informative labels (like "Archaic" in one of the
                # definition of "wick")
                defs += [ re.sub('<span class="luna-example.+$', '', x)
                          for x in re.findall(defs_pat, block)
                          if "luna-label" not in x ]

        # otherwise, concatenate all blocks and extract all definitions
        # available. Remove possible sentence examples in definitions and
        # possible non informative labels (like "Archaic" in one of the
        # definition of "wick")
        else:
            defs = re.findall(defs_pat, " ".join(blocks))
            defs = [ re.sub('<span class="luna-example.+$', '', x)
                     for x in defs if "luna-label" not in x]

        # need to clean definitions of <span> tags. Use cleaner to replace these
        # tags by empty string, Use .strip() to also clean some \r or \n.
        cleaner = re.compile('<.+?>', re.I|re.S)
        return [ re.sub(cleaner, '', x).strip() for x in defs ]

    except HTTPError:
        return -1
    except UnicodeDecodeError:
        return -1
    except IndexError:
        return -1
    except Exception as e:
        print("\nERROR: * timeout error.")
        print("       * retry dictionary.com -", word)
        return -1

def download_collins(word, pos="all"):
    URL = "https://www.collinsdictionary.com/dictionary/english/" + word

    # Collins has set some server restrictions. Need to spoof the HTTP headers
    headers = {
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
    req = urllib.request.Request(URL, headers=headers)

    if pos not in ["all", "adjective", "noun", "verb"]:
        pos = "all"

    try:
        html = urllib.request.urlopen(req).read().decode('utf-8')

        # definitions are in big blocks <div class="content definitions [...] >
        # Use the next <div> with "copyright" for ending regex. Regroup all
        # blocks.
        block_p = re.compile('<div class="content definitions.+?"(.*?)'
                             '<div class="div copyright', re.I|re.S)
        blocks = " ".join(re.findall(block_p, html))

        # inside this block, definitions are in <div class="def">...</div>
        defs_pat = re.compile('<div class="def">(.+?)</div>', re.I|re.S)

        # need to extract definitions only if it's a certain pos type
        if pos in ["adjective", "noun", "verb"]:

            # each sense of the word is inside a <div class="hom">. Get all the
            # starting and ending indexes of these blocks
            sense_pat = re.compile('<div class="hom">', re.I| re.S)
            idx = [m.start() for m in sense_pat.finditer(blocks)]
            idx.append(len(blocks))
            span = [(idx[i], idx[i+1]) for i in range(len(idx)-1)]

            # then for each sense, I only extract the definitions if it matches
            # the pos argument
            pos_pat = re.compile('class="pos">(.*?)</span>', re.I|re.S)
            defs = []

            for start, end in span:
                pos_extracted = re.search(pos_pat, blocks[start:end])
                # sometimes, sense is just a sentence or an idiom, so no pos
                # extracted
                if pos_extracted is None:
                    continue

                # noun is sometimes written as "countable noun". "verb" as
                # "verb transitive". Use the `in` trick to match these 2
                # categories with either "noun" or "verb"
                pos_extracted = pos_extracted.group(1)

                if pos not in pos_extracted:
                    continue

                defs += re.findall(defs_pat, blocks[start:end])

        # otherwise extract all definitions available
        else:
            defs = re.findall(defs_pat, blocks)

        # need to clean definitions of <a> and <span> tags. Use cleaner to
        # replace these tags by empty string, Use .strip() to also clean some
        # \r or \n, and replace because sometimes there are \n inside a sentence
        cleaner = re.compile('<.+?>', re.I|re.S)
        return [re.sub(cleaner, '', x).replace('\n', ' ').strip() for x in defs]

    except HTTPError:
        return -1
    except UnicodeDecodeError:
        return -1
    except IndexError:
        return -1
    except Exception as e:
        print("\nERROR: * timeout error.")
        print("       * retry Collins -", word)
        return -1

def download_oxford(word, pos="all"):
    URL = "http://en.oxforddictionaries.com/definition/"+ word

    if pos not in ["all", "adjective", "noun", "verb"]:
        pos = "all"

    try:
        html = urllib.request.urlopen(URL).read().decode('utf-8')

        # extract blocks containing POS type and definitions. For example, if
        # word is both a noun and a verb, there is one <section class="gramb">
        # block for the noun definitions, and another for the verb definitions
        block_p = re.compile('<section class="gramb">(.*?)</section>', re.I|re.S)
        blocks  = re.findall(block_p, html)

        # inside these blocks, definitions are in <span class="ind">
        defs_pat = re.compile('<span class="ind">(.*?)</span>', re.I|re.S)

        # need to extract definitions only if it's a certain pos type
        if pos in ["adjective", "noun", "verb"]:

            # for each block, I only extract the definitions if it matches the
            # pos argument
            pos_pat = re.compile('class="pos">(.*?)</span>', re.I|re.S)
            defs = []

            for block in blocks:
                pos_extracted = re.search(pos_pat, block).group(1)

                if pos_extracted != pos:
                    continue

                defs += re.findall(defs_pat, block)

        # otherwise extract all definitions available
        else:
            defs = re.findall(defs_pat, "".join(blocks))

        # need to clean definitions of <a> and <span> tags. Use cleaner to
        # replace these tags by empty string
        cleaner = re.compile('<.+?>', re.I|re.S)
        return [ re.sub(cleaner, '', x) for x in defs ]

    except HTTPError:
        return -1
    except UnicodeDecodeError:
        return -1
    except IndexError:
        return -1
    except Exception as e:
        print("\nERROR: * timeout error.")
        print("       * retry Oxford -", word)
        return -1

def download_robert(word, pos="all"):
    """Télécharge les définitions du mot depuis le dictionnaire Le Robert.
    
    Args:
        word (str): le mot dont on veut télécharger la définition
        pos (str): partie du discours. Si différent de 'all', ne retourne
                   que les définitions pour cette partie du discours.
                   
    Returns:
        tuple(list, None, None): liste des définitions si trouvées
        tuple(None, str, str): si le mot n'a pas de définition ou en cas d'erreur,
                               retourne (None, URL, message d'erreur)
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

    # Le Robert peut nécessiter des en-têtes spécifiques
    headers = {
        'User-Agent':
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like '
            'Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept':
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Encoding':
            'none',
        'Accept-Language':
            'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7',
    }
    
    try:
        # Try first with the normalized word (without diacritics)
        req = urllib.request.Request(URL, headers=headers)
        html = urllib.request.urlopen(req).read().decode('utf-8')
        
        # Utiliser BeautifulSoup pour parser le HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Vérifier si le mot existe
        if soup.find("section", class_="def") is None:
            # Si le mot n'existe pas avec version sans diacritiques, essayer avec la version originale
            if normalized_word != word:
                print(f"\nINFO: Trying alternative URL with original spelling for '{word}'")
                try:
                    req_fallback = urllib.request.Request(fallback_url, headers=headers)
                    html_fallback = urllib.request.urlopen(req_fallback).read().decode('utf-8')
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

MAP_DICT = {
    "Cam": download_cambridge,
    "Dic": download_dictionary,
    "Col": download_collins,
    "Oxf": download_oxford,
    "Rob": download_robert
}

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
                         'dictionary', 'oxford', or 'robert'
        word (str): the word we want to download definition
        pos (str): part-of-speech of the wanted definition. Can be:
                   'all' (default), 'adjective', 'adverb', 'noun' or 'verb'
        clean (bool): whether to cleanup the word or not.
                      The cleanup consists in removing trailing ...
                      ... punctuations and making it lowercase.

    Returns:
        list: definitions of WORD according to POS
        tuple(None, str, str): si le mot n'a pas de définition ou erreur (pour 'robert')
        None: si le mot n'a pas de définition (pour les autres dictionnaires)

    """
    dictionary = dict_name.lower()

    # check the validity of the params
    valid_dict = ["cambridge", "collins", "dictionary", "oxford", "robert"]
    if dictionary not in valid_dict:
        msg = "Expected a dictionary name in {0}, got '{1}'"
        raise ValueError(msg.format(valid_dict, dict_name))

    # get the function used to download this specific dictionary
    function = globals()["download_" + dictionary]

    # cleanup the word
    original_word = word  # Garder le mot original pour les messages d'erreur
    if clean:
        # remove trailing punctuation and make it lowercase
        for p in string.punctuation:
            word = word.replace(p, "")
        word = word.lower()

    try:
        # Obtenir les définitions
        result = function(word, pos)
        
        # Cas spécial pour le dictionnaire Le Robert qui retourne un tuple (definitions, url, error_msg)
        if dictionary == "robert":
            if isinstance(result, tuple):
                if len(result) == 3:  # Nouveau format avec message d'erreur
                    definitions, url, error_msg = result
                    if definitions is None:
                        return None, url, error_msg
                    # Sinon, on continue avec les définitions
                    result = definitions
                elif len(result) == 2:  # Ancien format sans message d'erreur
                    definitions, url = result
                    if definitions is None:
                        return None, url, "Mot non trouvé (raison inconnue)"
                    # Sinon, on continue avec les définitions
                    result = definitions
        
        # Pour les autres dictionnaires
        # Si le résultat est None, mot non trouvé
        if result is None:
            if dictionary == "robert":
                return None, "", f"Mot '{original_word}' non trouvé dans {dictionary}"
            return None
            
        # Harmonisation des codes d'erreur pour les autres dictionnaires
        if result == -1: # Ancien format d'erreur (pas de définition)
            if dictionary == "robert":
                return None, "", f"Mot '{original_word}' non trouvé dans {dictionary}"
            return None
            
        words = []
        # Sélectionner le set de stopwords approprié selon le dictionnaire
        stopwords = STOPWORDS_EN
        if dictionary == "robert":
            stopwords = STOPWORDS_FR
        
        for definition in result: # there can be more than one definition fetched
            # if no cleaning needed, add the whole definition
            if not clean:
                words.append(definition)
                continue

            # Pour le français, traiter spécialement les apostrophes
            if dictionary == "robert":
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
        error_msg = f"Erreur pour '{original_word}' dans {dictionary}: {str(e)}"
        print(f"\nWARNING: Error for '{original_word}' in {dictionary}: {str(e)}")
        if dictionary == "robert":
            return None, "", error_msg
        return None

if __name__ == '__main__':
    print("-- TEST : definitions of wick --")
    print("Cambridge")
    print(download_cambridge("wick", "all"))
    print("\ndictionary.com")
    print(download_dictionary("wick", "all"))
    print("\nCollins")
    print(download_collins("wick", "all"))
    print("\nOxford")
    print(download_oxford("wick", "all"))
    print("\nLe Robert")
    print(download_robert("chat", "all"))

    print("\n\n-- TEST : definitions according to POS of alert --")
    print("dictionary.com -- alert [ADJECTIVE]")
    print(download_dictionary("alert", "adjective"))
    print()
    print("dictionary.com -- alert [NOUN]")
    print(download_dictionary("alert", "noun"))
    print()
    print("dictionary.com -- alert [VERB]")
    print(download_dictionary("alert", "verb"))
    print()
    print("dictionary.com -- alert [ALL]")
    print(download_dictionary("alert", "all"))
    print()
    print("Le Robert -- chat [nom]")
    print(download_robert("chat", "nom"))
    print()
