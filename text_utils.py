"""
text_utils.py
Web requests and text analysis utilities for Gutenberg word frequency tool.
Author: That Zin Aung
Date: 2025-12-03
"""

import re
import collections
from typing import List, Tuple, Optional

import requests
from urllib.parse import quote_plus

# Simple stopword list – you can expand this if you want.
STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "in", "on", "at", "to",
    "of", "for", "with", "without", "from", "by",
    "i", "you", "he", "she", "it", "we", "they",
    "this", "that", "these", "those", "is", "are", "was", "were", "be",
    "as", "so", "than", "then", "there", "here",
}


def fetch_book_text(url: str) -> str:
    """
    Downloads the text from a Project Gutenberg URL.

    Args:
        url: The URL of the plain-text book.

    Returns:
        The text content as a string.

    Raises:
        requests.RequestException: If the HTTP request fails.
    """
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.text


def extract_title(text: str) -> str:
    """
    Attempts to extract a book title from the Project Gutenberg text.

    Args:
        text: The full text of the book.

    Returns:
        A best-guess title string.
    """
    lines = text.splitlines()
    for line in lines[:60]:
        line = line.strip()
        if line.upper().startswith("TITLE:"):
            return line[6:].strip()

    # fallback: first non-empty line
    for line in lines:
        if line.strip():
            return line.strip()
    return "Unknown Title"


def compute_top_words(text: str, n: int = 10) -> List[Tuple[str, int]]:
    """
    Computes the n most frequent non-stopword words in the provided text.

    Args:
        text: The book text.
        n: Number of top words to return.

    Returns:
        List of (word, frequency) tuples.
    """
    text = text.lower()
    tokens = re.findall(r"[a-z']+", text)
    filtered = [t for t in tokens if t not in STOPWORDS and len(t) > 1]

    counter = collections.Counter(filtered)
    return counter.most_common(n)


def search_gutenberg_by_title(title: str) -> Optional[str]:
    """
    Uses a WWW API (Gutendex) to search Project Gutenberg by title.

    Args:
        title: Book title to search.

    Returns:
        A plain-text URL if found, otherwise None.

    Raises:
        requests.RequestException: If the HTTP request fails.
    """
    if not title:
        return None

    query = quote_plus(title)
    url = f"https://gutendex.com/books?search={query}"

    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()

    results = data.get("results", [])
    if not results:
        return None

    first_book = results[0]
    formats = first_book.get("formats", {})

    # Prefer text/plain .txt
    for key, value in formats.items():
        if "text/plain" in key and value.endswith(".txt"):
            return value

    # Fallback: any text/plain
    for key, value in formats.items():
        if "text/plain" in key:
            return value

    return None
