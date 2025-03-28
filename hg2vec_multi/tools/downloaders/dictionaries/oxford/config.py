"""Oxford dictionary configuration."""

# Base URL
URL = "https://www.oxfordlearnersdictionaries.com/definition/english/"

# CSS Selectors
SELECTORS = {
    "all": "div.def",
    "noun": "div.def[data-type='noun']",
    "verb": "div.def[data-type='verb']",
    "adjective": "div.def[data-type='adjective']"
}

# Language support
SUPPORTED_LANGUAGES = ["en"] 