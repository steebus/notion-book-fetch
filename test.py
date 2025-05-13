#!/usr/bin/env python
"""
Test script to check if the Notion Book Extension is working properly.
This will search for entries in your Notion database with titles ending in semicolons
and attempt to fetch book metadata for them.

Run this locally to verify your setup before deploying.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Check if API key and database ID are set
if not os.getenv("NOTION_API_KEY"):
    print("Error: NOTION_API_KEY not set in .env file")
    sys.exit(1)

if not os.getenv("DATABASE_ID"):
    print("Error: DATABASE_ID not set in .env file")
    sys.exit(1)

# Import the processing function from the main app
from app import process_books, find_books_with_semicolon

if __name__ == "__main__":
    print("Finding books with semicolons in your Notion database...")
    
    # Find books with semicolons in the title
    semicolon_books = find_books_with_semicolon()
    
    if not semicolon_books:
        print("No books found with titles ending in semicolons.")
        print("Add a book with a title like 'The Hobbit;' to your Notion database and try again.")
        sys.exit(0)
    
    print(f"Found {len(semicolon_books)} books with semicolons in the title:")
    for book in semicolon_books:
        print(f"- {book['title']}")
    
    # Ask if the user wants to process the books
    user_input = input("\nDo you want to process these books and fetch metadata? (y/n): ")
    
    if user_input.lower() == 'y':
        print("\nProcessing books...")
        process_books()
        print("\nDone! Check your Notion database to see the results.")
    else:
        print("\nSkipping processing. No changes were made to your Notion database.")