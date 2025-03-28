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
from .base import DictionaryDownloader

class OxfordDownloader(DictionaryDownloader):
    """Oxford dictionary downloader."""
    
    def __init__(self):
        super().__init__()
        self.name = "Oxford"
        self.short_code = "Oxf"
        self.language = "en"
    
    def download(self, word, pos="all"):
        """Download definitions from Oxford dictionary.
        
        Args:
            word (str): The word to look up
            pos (str): Part of speech filter (default: "all")
            
        Returns:
            tuple: (definitions, url, error_msg)
                  - definitions: liste des définitions trouvées ou None si aucune
                  - url: URL consultée pour trouver les définitions ou None
                  - error_msg: Message d'erreur ou None si aucune erreur
        """
        URL = "http://en.oxforddictionaries.com/definition/"+ word

        if pos not in ["all", "adjective", "noun", "verb"]:
            pos = "all"

        try:
            html = self.get_html(URL)

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
            cleaned_defs = [self.clean_html(x, '<.+?>') for x in defs]
            
            # Si aucune définition n'a été trouvée
            if not cleaned_defs:
                return None, URL, f"No definition found for '{word}' in Oxford dictionary"
                
            return cleaned_defs, None, None

        except HTTPError as e:
            error_msg = f"HTTP Error {e.code} for '{word}' in Oxford dictionary"
            return None, URL, error_msg
        except UnicodeDecodeError as e:
            error_msg = f"Unicode decode error for '{word}' in Oxford dictionary: {str(e)}"
            return None, URL, error_msg
        except IndexError as e:
            error_msg = f"Index error for '{word}' in Oxford dictionary: {str(e)}"
            return None, URL, error_msg
        except Exception as e:
            error_msg = f"Error for '{word}' in Oxford dictionary: {str(e)}"
            print("\nERROR: * timeout error.")
            print("       * retry Oxford -", word)
            return None, URL, error_msg

# Instance to be imported by the downloader module
downloader = OxfordDownloader()