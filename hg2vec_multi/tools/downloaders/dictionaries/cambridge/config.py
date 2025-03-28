"""Cambridge dictionary configuration."""

# Base URL
URL = "https://dictionary.cambridge.org/dictionary/english/"

# CSS Selectors
SELECTORS = {
    "all": "div.def-block > div.def",
    "noun": "div.def-block[data-type='Noun'] > div.def",
    "verb": "div.def-block[data-type='Verb'] > div.def",
    "adjective": "div.def-block[data-type='Adjective'] > div.def"
}

# Language support
SUPPORTED_LANGUAGES = ["en"] 