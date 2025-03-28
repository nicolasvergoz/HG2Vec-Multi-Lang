# Dictionary Downloaders

This package contains modular dictionary downloaders for retrieving word definitions from various online dictionaries.

## Current Dictionaries

- **Cambridge** (`Cam`) - English definitions from Cambridge Dictionary
- **Dictionary.com** (`Dic`) - English definitions from Dictionary.com
- **Collins** (`Col`) - English definitions from Collins Dictionary
- **Le Robert** (`robert`) - French definitions from Le Robert Dictionary

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
            list: Definitions for the word
            -1: If word not found or error
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
            
            return definitions
            
        except HTTPError:
            return -1
        except Exception as e:
            print(f"\nERROR: * error when downloading from Merriam-Webster.")
            print(f"       * retry Merriam-Webster - {word}")
            return -1
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

Dictionary downloaders should return:

- A list of definitions if found
- `-1` for English dictionaries if the word is not found or an error occurs
- A tuple `(None, url, error_message)` for French dictionaries if the word is not found or an error occurs 