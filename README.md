# hg2vec-fr

A Python project based on [Dict2Vec](https://github.com/tca19/dict2vec) and [HG2Vec](https://github.com/Qitong-Wang/HG2Vec).

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

# Possible improvments
- French Larousse: Do not concatenate composed words like "moi-même" into "moimeme", it should be "moi-meme"
- Vector file for composed words might have wrong dimension count since it should be "word vec1 vec2" etc. but composed words are "moi-même" maybe it's a problem