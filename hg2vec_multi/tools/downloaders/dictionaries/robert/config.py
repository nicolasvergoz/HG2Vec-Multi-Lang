"""Robert dictionary configuration."""

# Base URL
URL = "https://dictionnaire.lerobert.com/definition/"

# CSS Selectors
SELECTORS = {
    "all": "div.definition",
    "noun": "div.definition[data-type='nom']",
    "verb": "div.definition[data-type='verbe']",
    "adjective": "div.definition[data-type='adjectif']"
}

# Language support
SUPPORTED_LANGUAGES = ["fr"] 