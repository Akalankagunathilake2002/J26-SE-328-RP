import unicodedata


def normalize_name(value: str) -> str:
    """Standardize text by normalizing unicode, lowercasing, and collapsing whitespace."""
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())
