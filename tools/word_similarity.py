#!/usr/bin/env python3

import sys
import os
import argparse
from processors.vector_processor.similarity import load_vectors, calculate_similarity


def main():
    """
    Tool for calculating similarity between two words using word vectors.
    """
    parser = argparse.ArgumentParser(
        description="Calculate similarity between two words using word vectors")
    
    # Optional arguments first
    parser.add_argument('--f', '--file', dest='vector_file', type=str, required=True,
                        help='Path to the word vector file')
    parser.add_argument('--top_n', '-n', type=int, default=0,
                        help='Find top N most similar words to word1 (if specified)')
    
    # Positional arguments for word1 and word2
    parser.add_argument('words', type=str, nargs='+', 
                        help='One or two words to compare')
    
    args = parser.parse_args()
    
    # Process word arguments
    word1 = args.words[0] if len(args.words) > 0 else None
    word2 = args.words[1] if len(args.words) > 1 else None
    
    # Check if vector file exists
    if not os.path.isfile(args.vector_file):
        print(f"Error: Vector file not found: {args.vector_file}")
        sys.exit(1)
    
    # Load vectors
    vectors = load_vectors(args.vector_file)
    
    # Calculate similarity between two words
    if word1 and word2:
        similarity = calculate_similarity(word1, word2, vectors)
        
        if similarity is not None:
            print(f"Similarity between '{word1}' and '{word2}': {similarity:.4f}")
        else:
            print("Could not calculate similarity")
    
    # Find top N similar words (either when explicitly requested or when word2 is not provided)
    if args.top_n > 0 or (word1 and not word2):
        top_n = args.top_n if args.top_n > 0 else 10  # Default to 10 if not specified
        if word1 in vectors:
            print(f"\nTop {top_n} words most similar to '{word1}':")
            find_most_similar(word1, vectors, top_n)


def find_most_similar(word, vectors, top_n):
    """
    Find the top N most similar words to the given word.
    """
    if word not in vectors:
        print(f"Word '{word}' not found in vectors")
        return
    
    target_vector = vectors[word]
    similarities = {}
    
    # Calculate similarity with all other words
    for other_word, vector in vectors.items():
        if other_word == word:
            continue
        
        similarity = calculate_similarity(word, other_word, vectors)
        if similarity is not None:
            similarities[other_word] = similarity
    
    # Sort by similarity (descending)
    sorted_similarities = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
    
    # Print top N
    for i, (similar_word, similarity) in enumerate(sorted_similarities[:top_n]):
        print(f"{i+1}. {similar_word}: {similarity:.4f}")


if __name__ == "__main__":
    main() 