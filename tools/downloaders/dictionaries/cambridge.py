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

class CambridgeDownloader(DictionaryDownloader):
    """Cambridge dictionary downloader."""
    
    def __init__(self):
        super().__init__()
        self.name = "Cambridge"
        self.short_code = "Cam"
        self.language = "en"
    
    def download(self, word, pos="all"):
        """Download definitions from Cambridge dictionary.
        
        Args:
            word (str): The word to look up
            pos (str): Part of speech filter (default: "all")
            
        Returns:
            list: Definitions for the word
            -1: If word not found or error
        """
        URL = "http://dictionary.cambridge.org/dictionary/english/" + word

        if pos not in ["all", "adjective", "noun", "verb"]:
            pos = "all"

        try:
            html = self.get_html(URL)

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
            return [self.clean_html(x, '<.+?>') for x in defs]

        except HTTPError:
            return -1
        except UnicodeDecodeError:
            return -1
        except Exception as e:
            print("\nERROR: * timeout error.")
            print("       * retry Cambridge -", word)
            return -1

# Instance to be imported by the downloader module
downloader = CambridgeDownloader() 