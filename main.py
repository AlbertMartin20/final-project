"""
main.py
Tkinter GUI for Project Gutenberg word frequency tool.
Author: That Zin Aung
Date: 2025-12-03
"""

import tkinter as tk
from tkinter import ttk, messagebox

import requests

from db_utils import (
    init_db,
    get_book_by_title,
    get_word_frequencies,
    insert_or_update_book,
)
from text_utils import (
    fetch_book_text,
    extract_title,
    compute_top_words,
    search_gutenberg_by_title,
)


class GutenbergApp:
    """
    Main application class that defines the Tkinter GUI and connects
    user actions to database and web-scraping logic.
    """

    def __init__(self, root: tk.Tk):
        """
        Initializes the GUI components.

        Args:
            root: Root Tk window.
        """
        self.root = root
        self.root.title("Project Gutenberg Word Frequency Tool")

        # --- Top frame: search by title ---
        frame_title = ttk.LabelFrame(root, text="Search by Book Title (Local DB + WWW API)")
        frame_title.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_title, text="Book Title:").pack(side="left", padx=5, pady=5)
        self.title_entry = ttk.Entry(frame_title, width=40)
        self.title_entry.pack(side="left", padx=5, pady=5)

        self.search_title_btn = ttk.Button(frame_title, text="Search", command=self.on_search_title)
        self.search_title_btn.pack(side="left", padx=5, pady=5)

        # --- Second frame: search by URL ---
        frame_url = ttk.LabelFrame(root, text="Fetch From Project Gutenberg URL")
        frame_url.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_url, text="Book URL:").pack(side="left", padx=5, pady=5)
        self.url_entry = ttk.Entry(frame_url, width=60)
        self.url_entry.pack(side="left", padx=5, pady=5)

        self.search_url_btn = ttk.Button(frame_url, text="Fetch & Update", command=self.on_search_url)
        self.search_url_btn.pack(side="left", padx=5, pady=5)

        # --- Results frame ---
        frame_results = ttk.LabelFrame(root, text="Top 10 Words")
        frame_results.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("word", "frequency")
        self.tree = ttk.Treeview(frame_results, columns=columns, show="headings", height=10)
        self.tree.heading("word", text="Word")
        self.tree.heading("frequency", text="Frequency")
        self.tree.column("word", width=200)
        self.tree.column("frequency", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Status label
        self.status_label = ttk.Label(root, text="Ready.")
        self.status_label.pack(fill="x", padx=10, pady=5)

    # ----------------- Event Handlers -----------------

    def on_search_title(self):
        """
        Handles clicking the 'Search' button for title search.
        """
        title = self.title_entry.get().strip()
        if not title:
            self.set_status("Please enter a book title.")
            return

        self.clear_results()

        try:
            # 1. Try local database
            book = get_book_by_title(title)
            if book is not None:
                book_id, stored_title, _url = book
                word_freqs = get_word_frequencies(book_id)
                if word_freqs:
                    self.show_results(word_freqs[:10])
                    self.set_status(f"Loaded '{stored_title}' from local database.")
                    return

            # 2. Not in DB or no word data → use WWW API
            text_url = search_gutenberg_by_title(title)
            if not text_url:
                self.set_status("Book was not found.")
                messagebox.showinfo("Info", "Book was not found.")
                return

            # 3. Fetch text, compute top words, store in DB
            text = fetch_book_text(text_url)
            book_title = extract_title(text)
            top_words = compute_top_words(text, n=10)

            insert_or_update_book(book_title, text_url, top_words)
            self.show_results(top_words)
            self.set_status(f"Retrieved '{book_title}' from the web and stored it.")

        except requests.RequestException as exc:
            self.set_status(f"Network error: {exc}")
            messagebox.showerror("Network Error", str(exc))
        except Exception as exc:
            self.set_status(f"Error: {exc}")
            messagebox.showerror("Error", str(exc))

    def on_search_url(self):
        """
        Handles clicking the 'Fetch & Update' button for URL search.
        """
        url = self.url_entry.get().strip()
        if not url:
            self.set_status("Please enter a Project Gutenberg URL.")
            return

        self.clear_results()

        try:
            text = fetch_book_text(url)
            book_title = extract_title(text)
            top_words = compute_top_words(text, n=10)

            insert_or_update_book(book_title, url, top_words)
            self.show_results(top_words)
            self.set_status(f"Stored/updated '{book_title}' from URL.")

        except requests.RequestException as exc:
            self.set_status(f"Network error: {exc}")
            messagebox.showerror("Network Error", str(exc))
        except Exception as exc:
            self.set_status(f"Error: {exc}")
            messagebox.showerror("Error", str(exc))

    # ----------------- Helper Methods -----------------

    def show_results(self, word_freqs):
        """
        Displays the list of word frequencies in the Treeview.

        Args:
            word_freqs: Iterable of (word, frequency) pairs.
        """
        self.clear_results()
        for word, freq in word_freqs:
            self.tree.insert("", "end", values=(word, freq))

    def clear_results(self):
        """Clears the Treeview results."""
        for item in self.tree.get_children():
            self.tree.delete(item)

    def set_status(self, text: str):
        """
        Sets the status label text.

        Args:
            text: Status message to display.
        """
        self.status_label.config(text=text)


def main():
    """
    Entry point for the application. Initializes the database
    and starts the Tkinter event loop.
    """
    init_db()

    root = tk.Tk()
    app = GutenbergApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
