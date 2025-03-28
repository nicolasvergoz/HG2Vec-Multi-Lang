"""Collins dictionary configuration."""

# Base URL
URL = "https://www.collinsdictionary.com/dictionary/english/"

# CSS Selectors
SELECTORS = {
    "all": "div.content definitions cobr",
    "noun": "div.content definitions cobr[data-type='noun']",
    "verb": "div.content definitions cobr[data-type='verb']",
    "adjective": "div.content definitions cobr[data-type='adjective']"
}

# Language support
SUPPORTED_LANGUAGES = ["en"] 