#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate synonym pairs and antonym pairs from a vocabulary and Wiktionary data.
This script processes a vocabulary list (one word per line) and a jsonl file of
Wiktionary extracts to create pairs of synonyms and antonyms.
"""

import json
import argparse
import os
import re
from typing import List, Dict, Set, Tuple


def load_vocabulary(filename: str) -> List[str]:
    """
    Load a vocabulary file containing one word per line.
    
    Args:
        filename: Path to the vocabulary file
    
    Returns:
        List of words from the vocabulary
    """
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def is_valid_word(word: str) -> bool:
    """
    Check if a word is valid (not a single character, no spaces, no emoji/special characters).
    
    Args:
        word: The word to check
    
    Returns:
        True if valid, False otherwise
    """
    # Skip words with spaces
    if " " in word:
        return False
    
    # Skip single character words
    if len(word) <= 1:
        return False
    
    # Check if the word contains only standard alphanumeric characters and common accents
    # This will filter out emoji and other special characters
    pattern = re.compile(r'^[a-zA-ZÀ-ÖØ-öø-ÿ0-9\-\']+$')
    return bool(pattern.match(word))


def extract_related_words(entry: Dict, relation_keys: List[str]) -> List[str]:
    """
    Extract related words (like synonyms, antonyms, etc.) from a Wiktionary entry.
    
    Args:
        entry: Dictionary containing Wiktionary entry data
        relation_keys: List of keys to look for (e.g., ["synonyms", "hyponyms", "forms"])
    
    Returns:
        List of related words extracted from the specified keys
    """
    related_words = []
    
    # Process each relation key
    for key in relation_keys:
        if key in entry:
            # Each relation can be an array of objects or just strings
            for item in entry[key]:
                if isinstance(item, dict) and "word" in item:
                    related_word = item["word"]
                    # Check if the word is valid
                    if is_valid_word(related_word):
                        related_words.append(related_word)
                elif isinstance(item, str):
                    # Check if the word is valid
                    if is_valid_word(item):
                        related_words.append(item)
    
    return related_words


def generate_pairs(vocabulary_fn: str, wiktionary_fn: str) -> Tuple[int, int]:
    """
    Generate synonym and antonym pairs from vocabulary and Wiktionary data.
    
    Args:
        vocabulary_fn: Path to the vocabulary file (one word per line)
        wiktionary_fn: Path to the Wiktionary jsonl file
    
    Returns:
        Tuple containing the count of synonym pairs and antonym pairs generated
    """
    # Define fixed output paths
    output_dir = "data/output/pairs"
    synonyms_fn = os.path.join(output_dir, "syn-pairs.txt")
    antonyms_fn = os.path.join(output_dir, "ant-pairs.txt")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Load vocabulary
    print(f"Loading vocabulary from {vocabulary_fn}...")
    vocabulary = load_vocabulary(vocabulary_fn)
    print(f"Loaded {len(vocabulary)} words from vocabulary.")
    
    # Set up relation keys to extract
    synonym_keys = ["synonyms", "hyponyms", "forms"]
    antonym_keys = ["antonyms"]
    
    # Set up counters for pairs
    synonym_count = 0
    antonym_count = 0
    
    # Open output files
    with open(synonyms_fn, 'w', encoding='utf-8') as syn_file, \
         open(antonyms_fn, 'w', encoding='utf-8') as ant_file, \
         open(wiktionary_fn, 'r', encoding='utf-8') as wiki_file:
        
        print(f"Processing Wiktionary data from {wiktionary_fn}...")
        
        # Process each line in the jsonl file
        for line_num, line in enumerate(wiki_file, 1):
            if line_num % 10000 == 0:
                print(f"Processed {line_num} entries...")
            
            try:
                entry = json.loads(line)
                
                # Check if the word is in our vocabulary
                if "word" in entry and entry["word"] in vocabulary:
                    word = entry["word"]
                    
                    # Extract synonyms (and related words)
                    synonyms = extract_related_words(entry, synonym_keys)
                    
                    # Extract antonyms
                    antonyms = extract_related_words(entry, antonym_keys)
                    
                    # Write synonym pairs
                    for synonym in synonyms:
                        syn_file.write(f"{word}\t{synonym}\n")
                        synonym_count += 1
                    
                    # Write antonym pairs
                    for antonym in antonyms:
                        ant_file.write(f"{word}\t{antonym}\n")
                        antonym_count += 1
            
            except json.JSONDecodeError:
                print(f"Warning: Could not parse JSON on line {line_num}, skipping...")
                continue
    
    print(f"Generated {synonym_count} synonym pairs in {synonyms_fn}")
    print(f"Generated {antonym_count} antonym pairs in {antonyms_fn}")
    
    return synonym_count, antonym_count


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Synonym and antonym pairs generator from Wiktionary data.",
    )
    
    parser.add_argument('-v', '--vocabulary', 
                        help="File containing vocabulary words, one per line.",
                        required=True)
    parser.add_argument('-w', '--wiktionary', 
                        help="JSONL file containing Wiktionary extracts.",
                        required=True)
    
    args = parser.parse_args()
    
    generate_pairs(args.vocabulary, args.wiktionary) 