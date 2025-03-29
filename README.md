# HG2VecMulti - Multi-Language Word Embeddings

A Python project that learns word embeddings using only dictionaries and thesauri. Based on [Dict2Vec](https://github.com/tca19/dict2vec) and extends [HG2Vec](https://github.com/Qitong-Wang/HG2Vec) to support multiple languages.

## Overview

HG2VecMulti learns word embeddings without requiring large text corpora by utilizing dictionary definitions and thesaurus relationships. The model achieves state-of-the-art results on word similarity and relatedness benchmarks.

## Inspiration and References

- Based on [Dict2Vec](https://github.com/tca19/dict2vec)
- Extended from [HG2Vec](https://github.com/Qitong-Wang/HG2Vec) by Qitong Wang
- HG2Vec paper: "HG2Vec: Improved Word Embeddings from Dictionary and Thesaurus Based Heterogeneous Graph" ([COLING 2022](https://aclanthology.org/2022.coling-1.279/))
- French evaluation datasets from [Similarity-Association-Benchmarks](https://github.com/nicolasying/Similarity-Association-Benchmarks/) including translated and adapted versions of SimLex-999 and WordSimilarity-353

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"
```

## Usage Pipeline

Follow these steps in order to run the complete pipeline:

### 1. Download Definitions
```bash
python tools/downloaders/download_definitions.py data/input/init_vocabulary_fr.txt -lang fr -l 2 -s data/input/stopwords_fr.txt -i 5 -m 1000000 --ignore-warnings
```
This downloads definitions for the words in your vocabulary file from online dictionaries:
- `-lang fr`: Use French dictionaries (Larousse, Le Robert)
- `-l 2`: Minimum word length to keep in definitions
- `-s data/input/stopwords_fr.txt`: Stopwords file for filtering
- `-i 5`: Run 5 vocabulary expansion iterations
- `-m 1000000`: Maximum number of definitions to download
- `--ignore-warnings`: Skip words with errors instead of adding to not-found list

### 2. Generate Strong/Weak Pairs
```bash
python tools/pair_generators/generate_weak_strong_pairs.py -d data/output/definitions/init_vocabulary_fr-definitions.txt -K 0
```
This creates strong and weak word pairs based on dictionary definitions:
- Strong pairs: Words that appear in each other's definitions
- Weak pairs: Words where one appears in the other's definition
- `-K 0`: Generate only natural strong pairs (no artificial pairs)

For artificial strong pairs (optional), you can use pre-trained word vectors:
```bash
python tools/pair_generators/generate_weak_strong_pairs.py -d data/output/definitions/init_vocabulary_fr-definitions.txt -e data/input/wiki.fr.vec -K 5
```
Pre-trained vectors can be downloaded from [FastText](https://fasttext.cc/docs/en/pretrained-vectors.html).

### 3. Extract Vocabulary
```bash
python tools/downloaders/extract_vocabulary.py data/output/definitions/init_vocabulary_fr-definitions.txt
```
This extracts all unique words from the definitions into a vocabulary file, which will be saved in `data/temp/vocabulary/init_vocabulary_fr-vocabulary.txt`.

### 4. Generate Synonym/Antonym Pairs
```bash
python tools/pair_generators/generate_syn_ant_pairs.py -v data/temp/vocabulary/init_vocabulary_fr-vocabulary.txt -w data/input/wiktionary_fr.jsonl
```
This creates synonym and antonym pairs from Wiktionary data:
- `-v`: Your vocabulary file
- `-w`: Wiktionary JSONL file

The Wiktionary JSONL file can be downloaded from [Kaikki.org](https://kaikki.org/):
- French Wiktionary: [https://kaikki.org/dictionary/French/](https://kaikki.org/dictionary/French/)
- English Wiktionary: [https://kaikki.org/dictionary/English/](https://kaikki.org/dictionary/English/)

### 5. Preprocess Data
```bash
./tools/processors/preprocessor/data_prepossessing.sh
```
This script prepares the data for training by:
- Converting word pairs into numerical IDs
- Generating graph edges for the model
- Creating necessary input files for training

### 6. Train the Model
```bash
./tools/processors/vector_processor/trainer.sh --lang fr
```
This trains the HG2Vec model using the French dataset with default parameters. You can customize parameters:
- `-p`: beta_pos (positive sampling)
- `-n`: beta_neg (negative sampling)
- `-s`: beta_strong (strong pairs)
- `-w`: beta_weak (weak pairs)
- `-y`: beta_syn (synonym pairs)
- `-a`: beta_ant (antonym pairs)
- `-l`: learning rate
- `-g`: language (fr for French)

## Project Structure

The project is organized into several components:
- **Downloaders**: Tools to retrieve word definitions from online dictionaries - [Downloaders README](https://github.com/nicolasvergoz/HG2VecMulti/blob/main/tools/downloaders/README.md)
- **Pair Generators**: Scripts to create word pairs based on definitions and relationships - [Pair Generators README](https://github.com/nicolasvergoz/HG2VecMulti/blob/main/tools/pair_generators/README.md)
- **Processors**: Tools to preprocess data and train the model - [Processors README](https://github.com/nicolasvergoz/HG2VecMulti/blob/main/tools/processors/README.md)

For detailed documentation on each component, please refer to the respective README files.

## Evaluation

The model is evaluated using the French word similarity and semantic association benchmarks from [Similarity-Association-Benchmarks](https://github.com/nicolasying/Similarity-Association-Benchmarks/), which include:

- French SimLex-999: Modified translation with corrected duplicates and adjustments for pronominal verbs
- French WS-Relatedness: Translation of the WordSimilarity-353 (WS-353) dataset

These datasets provide gold standards for evaluating both semantic similarity and association in French.

## Possible Improvements
- French Larousse: Do not concatenate composed words like "moi-même" into "moimeme", it should be "moi-meme"
- Vector file for composed words might have wrong dimension count since it should be "word vec1 vec2" etc. but composed words are "moi-même" maybe it's a problem