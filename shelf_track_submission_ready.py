#!/usr/bin/env python3
"""
shelf_track.py
Bookstore inventory system using SQLite (ebookstore.db)

Submission improvements:
- Handles new authors dynamically
- Improved docstrings
- Parameterized SQL
- Context-managed SQLite connections
"""

import sqlite3
from typing import Optional, Tuple

DB_FILE = "ebookstore.db"


def validate_4digit_int(value: str, field_name: str) -> Optional[int]:
    """Validate that the value is a 4‑digit integer."""
    value = value.strip()
    try:
        n = int(value)
    except ValueError:
        print(f"{field_name} must be an integer.")
        return None

    if 1000 <= n <= 9999:
        return n

    print(f"{field_name} must be 4 digits.")
    return None


def validate_nonempty_text(value: str, field_name: str) -> Optional[str]:
    """Ensure text input is not empty."""
    value = value.strip()
    if not value:
        print(f"{field_name} cannot be empty.")
        return None
    return value


def validate_nonneg_int(value: str, field_name: str) -> Optional[int]:
    """Validate a non‑negative integer."""
    value = value.strip()
    try:
        n = int(value)
    except ValueError:
        print(f"{field_name} must be an integer.")
        return None

    if n < 0:
        print(f"{field_name} cannot be negative.")
        return None

    return n


def get_conn() -> sqlite3.Connection:
    """Create and return SQLite connection."""
    return sqlite3.connect(DB_FILE)


def init_db() -> None:
    """Create tables if not exist and seed starter data."""

    create_author = """
    CREATE TABLE IF NOT EXISTS author (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        country TEXT NOT NULL
    );
    """

    create_book = """
    CREATE TABLE IF NOT EXISTS book (
        id INTEGER PRIMARY KEY,
        title TEXT NOT NULL,
        authorID INTEGER NOT NULL,
        qty INTEGER NOT NULL
    );
    """

    starter_authors = [
        (1290, "Charles Dickens", "England"),
        (8937, "J.K. Rowling", "England"),
        (2356, "C.S. Lewis", "Ireland"),
        (6380, "J.R.R. Tolkien", "South Africa"),
        (5620, "Lewis Carroll", "England"),
    ]

    starter_books = [
        (3001, "A Tale of Two Cities", 1290, 30),
        (3002, "Harry Potter and the Philosopher's Stone", 8937, 40),
        (3003, "The Lion, the Witch and the Wardrobe", 2356, 25),
        (3004, "The Lord of the Rings", 6380, 37),
        (3005, "Alice’s Adventures in Wonderland", 5620, 12),
    ]

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(create_author)
        cur.execute(create_book)

        cur.execute("SELECT COUNT(*) FROM author")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO author (id,name,country) VALUES (?,?,?)",
                starter_authors,
            )

        cur.execute("SELECT COUNT(*) FROM book")
        if cur.fetchone()[0] == 0:
            cur.executemany(
                "INSERT INTO book (id,title,authorID,qty) VALUES (?,?,?,?)",
                starter_books,
            )


def print_menu():
    """Display program menu."""
    print("\nMenu")
    print("1. Enter book")
    print("2. Update book")
    print("3. Delete book")
    print("4. Search books")
    print("5. View all books")
    print("0. Exit")


def enter_book():
    """Add a book and create author if missing."""
    print("\nEnter new book")

    book_id = validate_4digit_int(input("Book ID: "), "Book ID")
    if book_id is None:
        return

    title = validate_nonempty_text(input("Title: "), "Title")
    if title is None:
        return

    author_id = validate_4digit_int(input("Author ID: "), "Author ID")
    if author_id is None:
        return

    qty = validate_nonneg_int(input("Quantity: "), "Quantity")
    if qty is None:
        return

    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute("SELECT 1 FROM author WHERE id=?", (author_id,))
        if cur.fetchone() is None:
            print("Author not found. Enter new author details.")

            name = validate_nonempty_text(
                input("Author name: "), "Author name")
            if name is None:
                return

            country = validate_nonempty_text(
                input("Author country: "), "Author country"
            )
            if country is None:
                return

            cur.execute(
                "INSERT INTO author (id,name,country) VALUES (?,?,?)",
                (author_id, name, country),
            )

        cur.execute(
            "INSERT INTO book (id,title,authorID,qty) VALUES (?,?,?,?)",
            (book_id, title, author_id, qty),
        )

        print("Book added successfully.")


def update_book():
    """Update title or quantity of a book."""

    while True:
        book_id = validate_4digit_int(input("Book ID to update: "), "Book ID")
        if book_id is not None:
            break

    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute("SELECT title, qty FROM book WHERE id=?", (book_id,))
        row = cur.fetchone()

        if row is None:
            print("Book not found.")
            return

        print("Current:", row)

        new_title = input("New title (enter to keep): ").strip()
        new_qty = input("New quantity (enter to keep): ").strip()

        if new_title:
            cur.execute("UPDATE book SET title=? WHERE id=?",
                        (new_title, book_id))

        if new_qty:
            qty = validate_nonneg_int(new_qty, "Quantity")
            if qty is None:
                return
            cur.execute("UPDATE book SET qty=? WHERE id=?", (qty, book_id))

        print("Update complete.")


def delete_book():
    """Delete a book by ID."""

    while True:
        book_id = validate_4digit_int(input("Book ID to delete: "), "Book ID")
        if book_id is not None:
            break

    with get_conn() as conn:
        cur = conn.cursor()

        cur.execute("DELETE FROM book WHERE id=?", (book_id,))

        if cur.rowcount:
            print("Book deleted.")
        else:
            print("Book not found.")


def search_books():
    """Search for books by ID or title."""

    print("1 Search by ID")
    print("2 Search by title")

    choice = input("Choice: ").strip()

    query = '''
    SELECT b.id,b.title,a.name,a.country,b.qty
    FROM book b
    JOIN author a ON b.authorID=a.id
    '''
    params: Tuple = ()

    if choice == "1":
        book_id = validate_4digit_int(input("Book ID: "), "Book ID")
        if book_id is None:
            return
        query += " WHERE b.id=?"
        params = (book_id,)

    elif choice == "2":
        keyword = input("Keyword: ").strip()
        query += " WHERE b.title LIKE ?"
        params = (f"%{keyword}%",)

    else:
        print("Invalid choice")
        return

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(query, params)

        rows = cur.fetchall()

        if not rows:
            print("No results found.")
            return

        for r in rows:
            print(r)


def view_all_books():
    """Display all books with author details."""

    query = '''
    SELECT b.id,b.title,a.name,a.country,b.qty
    FROM book b
    JOIN author a ON b.authorID=a.id
    ORDER BY b.id
    '''

    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute(query)

        rows = cur.fetchall()

        if not rows:
            print("No books found.")
            return

        for row in rows:
            print(row)


def main():
    """Main program loop."""

    init_db()

    while True:
        print_menu()

        choice = input("Choice: ").strip()

        if choice == "1":
            enter_book()

        elif choice == "2":
            update_book()

        elif choice == "3":
            delete_book()

        elif choice == "4":
            search_books()

        elif choice == "5":
            view_all_books()

        elif choice == "0":
            print("Goodbye")
            break

        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
