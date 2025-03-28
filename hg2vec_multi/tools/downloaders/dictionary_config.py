"""Common dictionary configurations."""

# Error codes
ERROR_CODES = {
    "not_found": "Word not found",
    "timeout": "Request timed out",
    "bad_gateway": "Server error",
    "unknown_error": "Unknown error occurred"
}

# HTTP error mapping
HTTP_ERROR_MAPPING = {
    404: ERROR_CODES["not_found"],
    408: ERROR_CODES["timeout"],
    502: ERROR_CODES["bad_gateway"]
}

# User agents for requests
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59"
]

# Language to dictionary mapping
LANGUAGE_DICTIONARIES = {
    "en": ["cambridge", "oxford", "dictionary", "collins", "robert"],
    "fr": ["robert"]
}