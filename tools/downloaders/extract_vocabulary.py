#!/usr/bin/env python3

import os
import sys
import re
import argparse

def extract_vocabulary(input_file, output_dir=None):
    """
    Extract unique words from a definitions file and save them to a vocabulary file.
    
    Args:
        input_file (str): Path to the definitions file
        output_dir (str, optional): Directory to save the vocabulary file. 
                                   Defaults to data/temp/vocabulary/
    
    Returns:
        str: Path to the output file or None if an error occurred
    """
    try:
        # Read the input file
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split content into words
        words = re.findall(r'\b\w+\b', content.lower())
        
        # Get unique words
        unique_words = sorted(set(words))
        
        # Set default output directory if not provided
        if output_dir is None:
            output_dir = os.path.join('data', 'temp', 'vocabulary')
        
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create output filename based on input filename
        input_basename = os.path.basename(input_file)
        output_basename = input_basename.replace('-definitions.txt', '-vocabulary.txt')
        if output_basename == input_basename:
            output_basename = f"{os.path.splitext(input_basename)[0]}-vocabulary.txt"
        
        output_file = os.path.join(output_dir, output_basename)
        
        # Write unique words to output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(unique_words))
        
        print(f"Extracted {len(unique_words)} unique words from {input_file}")
        print(f"Saved vocabulary to {output_file}")
        
        return output_file
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Extract vocabulary from definitions file')
    parser.add_argument('input_file', help='Path to the definitions file')
    parser.add_argument('--output-dir', help='Directory to save the vocabulary file')
    
    args = parser.parse_args()
    
    result = extract_vocabulary(args.input_file, args.output_dir)
    return 0 if result else 1

if __name__ == "__main__":
    sys.exit(main()) 