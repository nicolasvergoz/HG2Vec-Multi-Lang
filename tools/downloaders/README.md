# Dictionary Downloaders

This package contains modular dictionary downloaders for retrieving word definitions from various online dictionaries.

## Usage

To download definitions from dictionaries, use the `download_definitions.py` script:

```bash
python tools/downloaders/download_definitions.py data/input/test_words_fr.txt -lang fr -l 2 -s data/input/stopwords_fr.txt -i 2 -m 100
```

### Command Line Arguments

- `input_file`: Path to a file containing a list of words (one per line)
- `-lang`: Language code - 'en' for English or 'fr' for French (default: 'en')
- `-pos`: Part of speech - 'noun', 'verb', 'adjective' or 'all' (default: 'all')
- `-out`: Output directory for definition files (default: 'data/output/definitions')
- `-l` / `--min-length`: Minimum word length to keep in definitions (default: 1)
- `-s` / `--stopwords`: Path to a stopwords file for filtering (optional)
- `--no-stopwords`: Disable stopwords filtering
- `-i` / `--iterations`: Number of vocabulary expansion iterations (default: 1)
- `-m` / `--max-definitions`: Maximum number of definitions to download across all iterations (optional)

### Process Overview

The script follows these steps:
1. Reads the input file to get the initial vocabulary
2. Downloads definitions for each word from the selected dictionaries
3. Cleans and processes the definitions
4. Optionally extracts new words from definitions for additional iterations
5. Outputs a final file with all accumulated definitions

## Current Dictionaries

- **Cambridge** (`Cam`) - English definitions from Cambridge Dictionary
- **Dictionary.com** (`Dic`) - English definitions from Dictionary.com
- **Collins** (`Col`) - English definitions from Collins Dictionary
- **Le Robert** (`Rob`) - French definitions from Le Robert Dictionary
- **Larousse** (`Lar`) - French definitions from Larousse Dictionary

## How to Add a New Dictionary

To add a new dictionary downloader, follow these steps:

1. Create a new Python file in the `dictionaries` directory named after your dictionary (e.g., `merriam_webster.py`).

2. Import the base `DictionaryDownloader` class and any other required modules:

```python
from .base import DictionaryDownloader
import re
from urllib.error import HTTPError
# Import any other necessary modules
```

3. Create a new downloader class that inherits from `DictionaryDownloader`:

```python
class MerriamWebsterDownloader(DictionaryDownloader):
    """Merriam-Webster dictionary downloader."""
    
    def __init__(self):
        super().__init__()
        self.name = "Merriam-Webster"
        self.short_code = "MWeb"  # Short code for use in the system
        self.language = "en"      # Language code ("en" or "fr")
        
        # Optionally set custom headers if needed
        self.headers['Some-Header'] = 'Custom-Value'
    
    def download(self, word, pos="all"):
        """Download definitions from Merriam-Webster.
        
        Args:
            word (str): The word to look up
            pos (str): Part of speech filter (default: "all")
            
        Returns:
            tuple: (definitions, url, error_msg)
                  - definitions: list of definitions found or None if none
                  - url: URL consulted to find definitions or None
                  - error_msg: Error message or None if no error
        """
        URL = "https://www.merriam-webster.com/dictionary/" + word
        
        # Implement the dictionary-specific download logic here
        # Follow the pattern from other downloaders:
        # 1. Try to download the page
        # 2. Extract definitions based on part of speech
        # 3. Clean and return the definitions
        
        try:
            html = self.get_html(URL)
            
            # Extract definitions
            # ...
            
            return definitions, None, None
            
        except HTTPError as e:
            error_msg = f"HTTP error {e.code} for '{word}'"
            return None, URL, error_msg
        except Exception as e:
            error_msg = f"Error for '{word}': {str(e)}"
            return None, URL, error_msg
```

4. Add an instance of your downloader at the end of the file:

```python
# Instance to be imported by the downloader module
downloader = MerriamWebsterDownloader()
```

5. Update the `__init__.py` file to include your new downloader:

```python
# Import the new downloader
from .merriam_webster import downloader as merriam_webster_downloader

# Add to the dictionary of downloaders
DICTIONARY_DOWNLOADERS = {
    # Existing entries...
    "MWeb": merriam_webster_downloader,
    # Other entries...
}
```

That's it! Your new dictionary downloader will be automatically available for use with the `lang` parameter matching your downloader's language.

## Tips for Implementing a New Downloader

1. **Study the HTML structure** of the dictionary website to identify where the definitions are located.
2. **Use Chrome DevTools** to inspect elements and understand the structure of the page.
3. **Handle different part-of-speech cases** properly.
4. **Clean HTML tags** from the extracted definitions.
5. **Handle errors gracefully** and return appropriate error codes.
6. **Test thoroughly** with various words, including edge cases.
7. **Respect website terms of service** and consider rate limiting your requests.

## Return Values

Dictionary downloaders should return a tuple with three elements:
- `(definitions, url, error_msg)` where:
  - `definitions`: A list of definitions if found, or None if not found
  - `url`: The URL consulted (for error reporting) or None
  - `error_msg`: Error message if there was an error, or None 

# Extracting Vocabulary from Definitions

Once you have downloaded definitions, you can extract a vocabulary list (unique words) using the `extract_vocabulary.py` script:

```bash
python tools/downloaders/extract_vocabulary.py data/output/definitions/your_words-definitions.txt
```

### Command Line Arguments

- `input_file`: Path to the definitions file to process
- `--output-dir`: Optional custom directory to save the vocabulary file (default: 'data/temp/vocabulary/')

### Output

The script will:
- Extract all unique words from the definitions file
- Convert words to lowercase for better deduplication
- Sort words alphabetically
- Save the vocabulary as a text file with one word per line

### Using as a Module

You can also import and use the extract_vocabulary function in your own Python scripts:

```python
from tools.downloaders.extract_vocabulary import extract_vocabulary

# Extract vocabulary and get the path to the output file
output_file = extract_vocabulary('path/to/definitions_file.txt')
```
