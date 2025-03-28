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

class DictionaryDotComDownloader(DictionaryDownloader):
    """Dictionary.com dictionary downloader."""
    
    def __init__(self):
        super().__init__()
        self.name = "Dictionary.com"
        self.short_code = "Dic"
        self.language = "en"
    
    def download(self, word, pos="all"):
        """Download definitions from Dictionary.com.
        
        Args:
            word (str): The word to look up
            pos (str): Part of speech filter (default: "all")
            
        Returns:
            list: Definitions for the word
            -1: If word not found or error
        """
        URL = "http://www.dictionary.com/browse/" + word

        if pos not in ["all", "adjective", "noun", "verb"]:
            pos = "all"

        try:
            html = self.get_html(URL)

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
            return [self.clean_html(x, '<.+?>').strip() for x in defs]

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

# Instance to be imported by the downloader module
downloader = DictionaryDotComDownloader() 