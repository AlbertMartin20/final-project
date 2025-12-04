"""
db_utils.py
SQLite database utilities for Gutenberg word frequency tool.
Author: That Zin Aung
Date: 2025-12-03
"""

import sqlite3
from typing import List, Tuple, Optional

DB_NAME = "books.db"


def get_connection():
    """
    Opens a connection to the SQLite database.

    Returns:
        sqlite3.Connection: An open connection to the database.
    """
    return sqlite3.connect(DB_NAME)


def init_db():
    """
    Creates the required tables if they do not exist.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT UNIQUE NOT NULL,
                url TEXT
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS word_freqs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER NOT NULL,
                word TEXT NOT NULL,
                frequency INTEGER NOT NULL,
                UNIQUE(book_id, word),
                FOREIGN KEY(book_id) REFERENCES books(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
    finally:
        conn.close()


def get_book_by_title(title: str) -> Optional[Tuple[int, str, str]]:
    """
    Retrieves a book from the database by title (case-insensitive).

    Args:
        title: Title of the book to search for.

    Returns:
        A tuple (id, title, url) if found, otherwise None.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, url
            FROM books
            WHERE LOWER(title) = LOWER(?)
        """, (title,))
        row = cur.fetchone()
        return row
    finally:
        conn.close()


def get_word_frequencies(book_id: int) -> List[Tuple[str, int]]:
    """
    Retrieves the word frequencies for a given book.

    Args:
        book_id: ID of the book.

    Returns:
        List of (word, frequency) tuples sorted by frequency descending.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT word, frequency
            FROM word_freqs
            WHERE book_id = ?
            ORDER BY frequency DESC, word ASC
        """, (book_id,))
        return cur.fetchall()
    finally:
        conn.close()


def insert_or_update_book(title: str, url: str, word_freqs: List[Tuple[str, int]]):
    """
    Inserts or updates a book and its word frequencies.

    Args:
        title: Title of the book.
        url: URL where the text was obtained.
        word_freqs: List of (word, frequency) tuples to store.
    """
    conn = get_connection()
    try:
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO books (title, url)
            VALUES (?, ?)
            ON CONFLICT(title) DO UPDATE SET url = excluded.url
        """, (title, url))
        conn.commit()

        # Get the book id
        cur.execute("SELECT id FROM books WHERE title = ?", (title,))
        book_id_row = cur.fetchone()
        if book_id_row is None:
            return
        book_id = book_id_row[0]

        # Clear old word frequencies for this book
        cur.execute("DELETE FROM word_freqs WHERE book_id = ?", (book_id,))

        # Insert new word frequencies
        cur.executemany("""
            INSERT INTO word_freqs (book_id, word, frequency)
            VALUES (?, ?, ?)
        """, [(book_id, w, f) for w, f in word_freqs])

        conn.commit()
    finally:
        conn.close()
