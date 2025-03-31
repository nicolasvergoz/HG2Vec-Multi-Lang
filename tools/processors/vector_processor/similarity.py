#!/usr/bin/env python3

import os
import sys
import argparse
import numpy as np
from numpy.linalg import norm


def cosineSim(v1, v2):
    """Return the cosine similarity between v1 and v2 (numpy arrays)"""
    dotProd = np.dot(v1, v2)
    return dotProd / (np.linalg.norm(v1) * np.linalg.norm(v2))


def load_vectors(vector_file):
    """
    Load word vectors from the specified file.
    Returns a dictionary mapping words to their vectors.
    """
    print(f"Loading vectors from {vector_file}...")
    word_vectors = {}
    
    try:
        with open(vector_file, 'r', encoding='utf-8') as f:
            # Read first line to get dimensions
            first_line = f.readline().split()
            if len(first_line) == 2:
                # First line contains metadata (count, dimensions)
                nb_vectors = int(first_line[0])
                vector_dim = int(first_line[1])
                print(f"Found {nb_vectors} vectors of dimension {vector_dim}")
            else:
                # First line already contains a vector
                vector_dim = len(first_line) - 1
                word = first_line[0]
                vector = np.array([float(val) for val in first_line[1:]])
                word_vectors[word] = vector
                
            # Process remaining lines
            for line in f:
                parts = line.strip().split()
                if len(parts) < vector_dim + 1:
                    continue  # Skip invalid lines
                    
                word = parts[0]
                try:
                    vector = np.array([float(val) for val in parts[1:]])
                    word_vectors[word] = vector
                except ValueError:
                    continue  # Skip lines with non-numeric values
                    
    except Exception as e:
        print(f"Error loading vectors: {str(e)}")
        sys.exit(1)
        
    print(f"Successfully loaded {len(word_vectors)} word vectors")
    return word_vectors


def calculate_similarity(word1, word2, vectors):
    """
    Calculate similarity between two words using their vectors.
    """
    if word1 not in vectors:
        print(f"Word '{word1}' not found in vectors")
        return None
        
    if word2 not in vectors:
        print(f"Word '{word2}' not found in vectors")
        return None
        
    v1 = vectors[word1]
    v2 = vectors[word2]
    
    return cosineSim(v1, v2)


def main():
    parser = argparse.ArgumentParser(description="Calculate similarity between two words using word vectors")
    parser.add_argument('--vector_file', type=str, required=True, 
                        help='Path to the word vector file')
    parser.add_argument('--word1', type=str, required=True,
                        help='First word to compare')
    parser.add_argument('--word2', type=str, required=True,
                        help='Second word to compare')
    
    args = parser.parse_args()
    
    # Load vectors
    vectors = load_vectors(args.vector_file)
    
    # Calculate similarity
    similarity = calculate_similarity(args.word1, args.word2, vectors)
    
    if similarity is not None:
        print(f"Similarity between '{args.word1}' and '{args.word2}': {similarity:.4f}")
    else:
        print("Could not calculate similarity")


if __name__ == "__main__":
    main() 