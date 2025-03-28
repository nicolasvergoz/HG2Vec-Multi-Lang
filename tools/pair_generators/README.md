# Pair Generators

This directory contains tools for generating word pairs based on dictionary definitions and word embeddings.

## Generate Pairs

The `generate_pairs.py` script generates strong and weak pairs of words based on their definitions. The script requires a file containing word definitions and optionally pre-trained word embeddings.

### Strong and Weak Pairs

- **Strong pairs**: Two words (A, B) are considered a strong pair if A appears in the definition of B AND B appears in the definition of A.
- **Weak pairs**: Two words (A, B) are considered a weak pair if A appears in the definition of B OR B appears in the definition of A (but not both).

### Artificial Strong Pairs

The script can generate artificial strong pairs using word embeddings. For each naturally occurring strong pair (A, B), the script can find K words that are semantically closest to B (using cosine similarity) and create additional strong pairs with A.

- When `K=0`: Only natural strong pairs are generated (recommended if you want only genuine bidirectional relationships). No word embeddings are needed in this case.
- When `K>0`: For each natural strong pair, K artificial pairs are generated using similar words from the embedding space. Word embeddings are required for this mode.

If you specify `K>0` but don't provide an embedding file, the script will automatically set K=0 and only generate natural strong pairs.

### Usage

```bash
python generate_pairs.py -d <definitions_file> [-e <embeddings_file>] [-sf <strong_file>] [-wf <weak_file>] [-K <num>]
```

#### Parameters

- `-d, --definitions`: File containing word definitions (required)
- `-e, --embedding`: File containing word embeddings (optional, required only if K > 0)
- `-sf, --strong-file`: Base filename where strong pairs will be saved (default: "strong-pairs")
- `-wf, --weak-file`: Base filename where weak pairs will be saved (default: "weak-pairs")
- `-K`: Number of artificially generated strong pairs for each natural strong pair (default: 5, set to 0 for only natural strong pairs)

#### Example

```bash
# Generate natural and artificial strong pairs (K=5)
python tools/pair_generators/generate_pairs.py \
  -d data/input/definitions.txt \
  -e data/input/wiki.fr.vec \
  -sf data/output/pairs/strong-pairs \
  -wf data/output/pairs/weak-pairs \
  -K 5

# Generate only natural strong pairs (no artificial pairs)
python tools/pair_generators/generate_pairs.py \
  -d data/input/definitions.txt \
  -sf data/output/pairs/strong-pairs \
  -wf data/output/pairs/weak-pairs \
  -K 0
```

### Output

The script generates two files:
- `<strong-file>-K<K>.txt`: Contains all strong pairs of words
- `<weak-file>-K<K>.txt`: Contains all weak pairs of words

## Word Embeddings

The script uses pre-trained word embeddings when generating artificial strong pairs (K > 0). You can download pre-trained word embeddings for multiple languages from:

[FastText Pre-trained Word Vectors](https://fasttext.cc/docs/en/pretrained-vectors.html)

These embeddings are trained on Wikipedia using the FastText model and are available for 294 languages. The embeddings come in both binary and text formats. Use the text format (`.vec`) files with this script.

### Embedding Format

Each file starts with a header line containing the number of vectors and their dimension. Each subsequent line contains a word followed by its vector representation.

Example of the first few lines from a `.vec` file:
```
1152449 300
</s> 0.28556 0.14918 -0.42066 ... (values continue)
, 0.018559 0.062629 -0.12698 ... (values continue)
...
```

## Definition File Format

The definition file should be a plain text file where each line contains a word followed by its definition. The word and its definition should be separated by spaces.

Example:
```
word definition word1 word2 word3
computer electronic device used for processing data
...
```

## References

If you use the FastText word vectors, please cite:
```
@article{bojanowski2017enriching,
  title={Enriching Word Vectors with Subword Information},
  author={Bojanowski, Piotr and Grave, Edouard and Joulin, Armand and Mikolov, Tomas},
  journal={Transactions of the Association for Computational Linguistics},
  volume={5},
  year={2017},
  issn={2307-387X},
  pages={135--146}
}
``` 