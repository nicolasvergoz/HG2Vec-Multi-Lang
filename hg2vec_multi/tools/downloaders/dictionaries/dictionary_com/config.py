"""Dictionary.com configuration."""

# Base URL
URL = "https://www.dictionary.com/browse/"

# CSS Selectors
SELECTORS = {
    "all": "div.def-content",
    "noun": "div.def-content[data-type='noun']",
    "verb": "div.def-content[data-type='verb']",
    "adjective": "div.def-content[data-type='adjective']"
}

# Language support
SUPPORTED_LANGUAGES = ["en"] 