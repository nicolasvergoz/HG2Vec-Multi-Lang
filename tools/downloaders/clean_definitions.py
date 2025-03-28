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

import sys
import argparse
import os.path
from collections import defaultdict


def flatten(l):
    """Convert list of list to a list"""
    return [ el for sub_l in l for el in sub_l ]

def load_vocabulary(fn):
    """Read the file fn and return a set containing all the words
    of the vocabulary."""
    vocabulary = set()
    with open(fn) as f:
        for line in f:
            vocabulary.add(line.strip())

    return vocabulary

def clean_defs(definitions, output_file, vocab="", min_word_length=1, stopwords_file=""):
    """Load fetched definitions and regroup words with all their definitions.
    
    Args:
        definitions (str): Path to the file containing the downloaded definitions
        output_file (str): Path where to write the cleaned definitions
        vocab (str): Path to a vocabulary file to filter words (optional)
        min_word_length (int): Minimum length for words to keep (default: 1)
        stopwords_file (str): Path to a file containing stopwords to remove (optional)
    """
    print(f"Cleaning definitions from {definitions}...")
    regouped_dictionary = defaultdict(list)

    with open(definitions) as f:
        for line in f:
            line = line.strip()
            ar = line.split()
            if len(ar) < 2:  # Skip empty lines or lines with just the dictionary name
                continue
                
            dictionary_name = ar[0]  # First token is the dictionary name
            word, defs = ar[1], ar[2:]  # Second token is the word, rest is definition
            regouped_dictionary[word].append(defs)

    # Load stopwords if a file is provided
    stopwords = set()
    if stopwords_file and os.path.isfile(stopwords_file):
        print(f"Loading stopwords from {stopwords_file}")
        stopwords = load_vocabulary(stopwords_file)
    else:
        if stopwords_file:
            print(f"WARNING: Stopwords file {stopwords_file} not found or not specified")

    # Regroup together all definitions of a word. Remove words
    # that are not in vocabulary or are too short or are stopwords.
    print(f"Writing cleaned definitions to {output_file}...")
    of = open(output_file, "w")
    word_count = 0

    if len(vocab) == 0:  # No vocabulary given so no words removed based on vocabulary
        for w in regouped_dictionary:
            definition = ' '.join([el for el in flatten(regouped_dictionary[w])
                                  if len(el) > min_word_length and el.lower() not in stopwords])
            if definition.strip():  # Only write if definition is not empty
                of.write("%s %s\n" % (w, definition))
                word_count += 1
    else:
        vocabulary = load_vocabulary(vocab)
        for w in regouped_dictionary:
            definition = ' '.join([el for el in flatten(regouped_dictionary[w])
                                  if len(el) > min_word_length and el.lower() not in stopwords and el in vocabulary])
            if definition.strip():  # Only write if definition is not empty
                of.write("%s %s\n" % (w, definition))
                word_count += 1

    of.close()
    print(f"Done. Cleaned definitions for {word_count} words.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean word definitions by filtering and regrouping")
    parser.add_argument('-d', '--definitions', help="File containing the definitions downloaded with download_definitions.py",
                        required=True)
    parser.add_argument("-v", "--vocab", help="File containing a list of words. The script will remove all words in definitions that are not in this vocab",
                        default="")
    parser.add_argument("-o", "--output", help="Output file name for cleaned definitions (default: based on input file)",
                        default="")
    parser.add_argument("-l", "--min-length", help="Minimum word length to keep (default: 1)",
                        type=int, default=1)
    parser.add_argument("-s", "--stopwords", help="File containing stopwords to remove from definitions",
                        default="")

    args = parser.parse_args()

    # If no output file is specified, create one based on the input file
    if not args.output:
        base_name = os.path.splitext(args.definitions)[0]
        dest_fn = f"{base_name}-cleaned.txt"
    else:
        dest_fn = args.output

    print(f"Writing the cleaned definitions to {dest_fn}")
    clean_defs(args.definitions, dest_fn, args.vocab, args.min_length, args.stopwords)
