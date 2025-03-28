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

class CollinsDownloader(DictionaryDownloader):
    """Collins dictionary downloader."""
    
    def __init__(self):
        super().__init__()
        self.name = "Collins"
        self.short_code = "Col"
        self.language = "en"
        # Collins has set some server restrictions. Need special headers
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

        if pos not in ["all", "adjective", "noun", "verb"]:
            pos = "all"

        try:
            html = self.get_html(URL)

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
            cleaned_defs = [self.clean_html(x, '<.+?>').replace('\n', ' ').strip() for x in defs]

            # Si aucune définition n'a été trouvée
            if not cleaned_defs:
                return None, URL, f"No definition found for '{word}' in Collins dictionary"
                
            return cleaned_defs, None, None

        except HTTPError as e:
            error_msg = f"HTTP Error {e.code} for '{word}' in Collins dictionary"
            return None, URL, error_msg
        except UnicodeDecodeError as e:
            error_msg = f"Unicode decode error for '{word}' in Collins dictionary: {str(e)}"
            return None, URL, error_msg
        except IndexError as e:
            error_msg = f"Index error for '{word}' in Collins dictionary: {str(e)}"
            return None, URL, error_msg
        except Exception as e:
            error_msg = f"Error for '{word}' in Collins dictionary: {str(e)}"
            print("\nERROR: * timeout error.")
            print("       * retry Collins -", word)
            return None, URL, error_msg

# Instance to be imported by the downloader module
downloader = CollinsDownloader() 