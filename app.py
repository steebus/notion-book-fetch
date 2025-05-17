import os
import time
import json
import re
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Notion API configuration
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "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")
DATABASE_ID = os.getenv("DATABASE_ID", "9c847e888b7d4cf19630c770c08fce8c")
CHECK_INTERVAL = int(60)  # Default to 60 seconds

NOTION_API_URL = "https://api.notion.com/v1"
NOTION_VERSION = "2022-02-22"  # Updated to a version that supports page covers and icons

# Headers for Notion API
notion_headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION,
}

# Book API configurations
GOOGLE_BOOKS_API_URL = "https://www.googleapis.com/books/v1/volumes"
OPEN_LIBRARY_API_URL = "https://openlibrary.org/search.json"

# Property names in Notion database
PROPERTY_TITLE = "title"
PROPERTY_DESCRIPTION = "Description"
PROPERTY_AUTHORS = "Author(s)"
PROPERTY_RATING = "Rating"
PROPERTY_GENRES = "Genres"
PROPERTY_LINK = "Link"
PROPERTY_PAGES = "Pages"
PROPERTY_COVER = "Cover"
PROPERTY_SERIES = "Series"
PROPERTY_DATE_PUBLISHED = "DatePublished"
PROPERTY_NON_FICTION = "Non/Fiction"
PROPERTY_ISBN = "ISBN"
PROPERTY_SEARCH_TERM = "Search Term"  # Added Search Term property

def query_database():
    """Query the Notion database for all pages."""
    url = f"{NOTION_API_URL}/databases/{DATABASE_ID}/query"
    
    all_pages = []
    has_more = True
    start_cursor = None
    
    print("Fetching all pages from Notion database...")
    
    while has_more:
        payload = {}
        if start_cursor:
            payload["start_cursor"] = start_cursor
            
        response = requests.post(url, headers=notion_headers, json=payload)
        
        if response.status_code != 200:
            print(f"Error querying database: {response.status_code}")
            print(response.text)
            return []
        
        data = response.json()
        current_pages = data.get("results", [])
        all_pages.extend(current_pages)
        
        print(f"Fetched {len(current_pages)} pages, total so far: {len(all_pages)}")
        
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
        
        if has_more:
            print(f"More pages available, continuing with cursor: {start_cursor}")
    
    print(f"Total pages fetched: {len(all_pages)}")
    
    # Print titles of all pages
    semicolon_count = 0
    print("\nList of all page titles in the database:")
    for i, page in enumerate(all_pages, 1):
        # Get the title from the Title property
        properties = page.get("properties", {})
        title_property = properties.get("Title", {})  # Note: Capital "T" in "Title"
        
        if title_property and "title" in title_property:
            title_arr = title_property["title"]
            if title_arr and len(title_arr) > 0:
                title = "".join([text_obj.get("plain_text", "") for text_obj in title_arr])
                has_semicolon = title.endswith(";")
                if has_semicolon:
                    semicolon_count += 1
                    print(f"{i}. '{title}' [ENDS WITH SEMICOLON]")
                else:
                    print(f"{i}. '{title}'")
            else:
                print(f"{i}. [Empty title]")
        else:
            print(f"{i}. [No Title property found]")
    
    print(f"\nFound {semicolon_count} pages with titles ending in semicolons")
    return all_pages

def get_page_properties(page_id):
    """Get properties of a specific page."""
    url = f"{NOTION_API_URL}/pages/{page_id}"
    response = requests.get(url, headers=notion_headers)
    if response.status_code != 200:
        print(f"Error getting page properties: {response.status_code}")
        print(response.text)
        return None
    return response.json().get("properties", {})

def find_books_with_semicolon():
    """Find books with titles ending in semicolon."""
    pages = query_database()
    semicolon_books = []
    
    for page in pages:
        properties = page.get("properties", {})
        title_property = properties.get("Title", {})  # Note: Capital "T" in "Title"
        
        if title_property and "title" in title_property:
            title_content = title_property["title"]
            if title_content and len(title_content) > 0:
                title = "".join([text_obj.get("plain_text", "") for text_obj in title_content])
                if title.endswith(";"):
                    search_query = title[:-1].strip()  # Remove semicolon and whitespace
                    
                    # Check if this is likely an ISBN
                    is_isbn = False
                    # Remove any non-digit and non-X characters for ISBN check
                    isbn_candidate = re.sub(r'[^0-9X]', '', search_query)
                    
                    # Check if the remaining string could be an ISBN (10 or 13 digits)
                    if len(isbn_candidate) in [10, 13] and isbn_candidate.isdigit() or (
                            len(isbn_candidate) == 10 and isbn_candidate[:-1].isdigit() and 
                            isbn_candidate[-1] in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'X']):
                        is_isbn = True
                        search_query = f"isbn:{isbn_candidate}"
                    
                    semicolon_books.append({
                        "id": page["id"],
                        "title": title,
                        "search_query": search_query,
                        "is_isbn": is_isbn
                    })
    
    return semicolon_books

def search_google_books(query):
    """Search for book information using Google Books API."""
    params = {"q": query, "maxResults": 1}
    response = requests.get(GOOGLE_BOOKS_API_URL, params=params)
    
    if response.status_code != 200:
        print(f"Error searching Google Books: {response.status_code}")
        return None
    
    data = response.json()
    items = data.get("items", [])
    
    if not items:
        return None
    
    volume_info = items[0].get("volumeInfo", {})
    
    # Get ISBN from industry identifiers
    isbn = None
    if "industryIdentifiers" in volume_info:
        for identifier in volume_info["industryIdentifiers"]:
            if identifier["type"] in ["ISBN_13", "ISBN_10"]:
                isbn = identifier["identifier"]
                break
    
    # Get published date
    published_date = None
    if "publishedDate" in volume_info:
        date_str = volume_info.get("publishedDate", "")
        # Handle different date formats (YYYY, YYYY-MM, YYYY-MM-DD)
        if len(date_str) >= 4:  # At least has year
            try:
                if len(date_str) == 4:  # Only year
                    published_date = {"start": f"{date_str}-01-01"}
                elif len(date_str) == 7:  # Year and month
                    published_date = {"start": f"{date_str}-01"}
                else:  # Full date
                    published_date = {"start": date_str}
            except ValueError:
                published_date = None
    
    # Determine fiction/non-fiction status based on categories
    categories = volume_info.get("categories", [])
    fiction_status = None
    non_fiction_keywords = ["non-fiction", "nonfiction", "biography", "history", 
                           "science", "self-help", "business", "psychology", 
                           "philosophy", "politics"]
    
    fiction_keywords = ["fiction", "novel", "fantasy", "sci-fi", "science fiction", 
                       "thriller", "mystery", "romance"]
    
    # Check categories for non-fiction or fiction keywords
    for category in categories:
        category_lower = category.lower()
        
        # Check for explicit non-fiction
        if any(keyword in category_lower for keyword in non_fiction_keywords):
            fiction_status = "Nonfiction"
            break
            
        # Check for fiction
        if any(keyword in category_lower for keyword in fiction_keywords):
            fiction_status = "Fiction"
            break
    
    # If still not determined, make a guess based on other factors
    if fiction_status is None:
        if "fiction" in query.lower():
            fiction_status = "Fiction"
        elif "non-fiction" in query.lower() or "nonfiction" in query.lower():
            fiction_status = "Nonfiction"
        else:
            # Default to fiction if unknown
            fiction_status = "Fiction"
    
    # Extract series information from title or subtitle
    series_name = None
    title = volume_info.get("title", "")
    subtitle = volume_info.get("subtitle", "")
    
    # Common series patterns in titles
    series_patterns = [
        r"(?:^|\s)(?:The\s)?(.*?)\s+Series(?:\s|$)",
        r"(?:^|\s)(?:The\s)?(.*?)\s+Trilogy(?:\s|$)",
        r"(?:^|\s)(?:The\s)?(.*?)\s+Saga(?:\s|$)",
        r"(?:^|\s)(?:The\s)?(.*?)\s+Chronicles(?:\s|$)",
        r"(?:^|\s)(?:The\s)?(.*?)\s+Sequence(?:\s|$)",
        r"(?:^|\s)(?:The\s)?(.*?)\s+Duology(?:\s|$)",
        r"(?:^|\s)(?:The\s)?(.*?)\s+Quartet(?:\s|$)",
        r"Book\s+\d+\s+of\s+(?:the\s+)?(.*?)(?:\s|$)",
        r"Volume\s+\d+\s+of\s+(?:the\s+)?(.*?)(?:\s|$)",
        r"\((?:The\s+)?(.*?)\s+(?:Series|Book|#)\s*\d*\)",
        r"\[(?:The\s+)?(.*?)\s+(?:Series|Book|#)\s*\d*\]",
    ]
    
    # Check title and subtitle for series information
    for pattern in series_patterns:
        # Check in title
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            series_name = match.group(1).strip()
            break
            
        # Check in subtitle if available
        if subtitle:
            match = re.search(pattern, subtitle, re.IGNORECASE)
            if match:
                series_name = match.group(1).strip()
                break
    
    # Get a better quality cover image if available
    image_link = ""
    if "imageLinks" in volume_info:
        image_links = volume_info.get("imageLinks", {})
        # Try to get the best quality image available
        for img_type in ["extraLarge", "large", "medium", "small", "thumbnail"]:
            if img_type in image_links:
                image_link = image_links[img_type]
                break
    
    return {
        "title": title,
        "authors": volume_info.get("authors", []),
        "description": volume_info.get("description", ""),
        "categories": volume_info.get("categories", []),
        "rating": volume_info.get("averageRating", 0),
        "page_count": volume_info.get("pageCount", 0),
        "info_link": volume_info.get("infoLink", ""),
        "image_link": image_link,
        "published_date": published_date,
        "fiction_status": fiction_status,
        "series_name": series_name,
        "isbn": isbn  # Added ISBN to return data
    }

def search_open_library(query):
    """Search for book information using Open Library API."""
    params = {"q": query, "limit": 1}
    response = requests.get(OPEN_LIBRARY_API_URL, params=params)
    
    if response.status_code != 200:
        print(f"Error searching Open Library: {response.status_code}")
        return None
    
    data = response.json()
    docs = data.get("docs", [])
    
    if not docs:
        return None
    
    book = docs[0]
    
    # Get ISBN from Open Library data
    isbn = None
    if "isbn" in book:
        isbn_list = book.get("isbn", [])
        if isbn_list:
            # Prefer ISBN-13 if available
            for isbn_candidate in isbn_list:
                if len(isbn_candidate) == 13:
                    isbn = isbn_candidate
                    break
            # If no ISBN-13, use the first ISBN
            if not isbn and isbn_list:
                isbn = isbn_list[0]
    
    # Get published date
    published_date = None
    if "first_publish_year" in book:
        year = book.get("first_publish_year")
        if year:
            published_date = {"start": f"{year}-01-01"}
    
    # Determine fiction/non-fiction status based on subjects
    subjects = book.get("subject", [])
    fiction_status = None
    
    non_fiction_keywords = ["non-fiction", "nonfiction", "biography", "history", 
                           "science", "self-help", "business", "psychology", 
                           "philosophy", "politics"]
    
    fiction_keywords = ["fiction", "novel", "fantasy", "sci-fi", "science fiction", 
                       "thriller", "mystery", "romance"]
    
    # Check subjects for non-fiction or fiction keywords
    for subject in subjects:
        subject_lower = subject.lower()
        
        # Check for explicit non-fiction
        if any(keyword in subject_lower for keyword in non_fiction_keywords):
            fiction_status = "Nonfiction"
            break
            
        # Check for fiction
        if any(keyword in subject_lower for keyword in fiction_keywords):
            fiction_status = "Fiction"
            break
    
    # If still not determined, make a guess based on other factors
    if fiction_status is None:
        if "fiction" in query.lower():
            fiction_status = "Fiction"
        elif "non-fiction" in query.lower() or "nonfiction" in query.lower():
            fiction_status = "Nonfiction"
        else:
            # Default to fiction if unknown
            fiction_status = "Fiction"
    
    # Extract series information
    series_name = None
    title = book.get("title", "")
    
    # Check if series information is in the title
    series_patterns = [
        r"(?:^|\s)(?:The\s)?(.*?)\s+Series(?:\s|$)",
        r"(?:^|\s)(?:The\s)?(.*?)\s+Trilogy(?:\s|$)",
        r"(?:^|\s)(?:The\s)?(.*?)\s+Saga(?:\s|$)",
        r"(?:^|\s)(?:The\s)?(.*?)\s+Chronicles(?:\s|$)",
        r"(?:^|\s)(?:The\s)?(.*?)\s+Sequence(?:\s|$)",
        r"(?:^|\s)(?:The\s)?(.*?)\s+Duology(?:\s|$)",
        r"(?:^|\s)(?:The\s)?(.*?)\s+Quartet(?:\s|$)",
        r"Book\s+\d+\s+of\s+(?:the\s+)?(.*?)(?:\s|$)",
        r"Volume\s+\d+\s+of\s+(?:the\s+)?(.*?)(?:\s|$)",
        r"\((?:The\s+)?(.*?)\s+(?:Series|Book|#)\s*\d*\)",
        r"\[(?:The\s+)?(.*?)\s+(?:Series|Book|#)\s*\d*\]",
    ]
    
    # Check title for series information
    for pattern in series_patterns:
        match = re.search(pattern, title, re.IGNORECASE)
        if match:
            series_name = match.group(1).strip()
            break
    
    # If not in title, check if there's a series field
    if not series_name and "series" in book:
        series_list = book.get("series", [])
        if series_list and len(series_list) > 0:
            series_name = series_list[0]
    
    return {
        "title": title,
        "authors": book.get("author_name", []),
        "description": book.get("description", ""),
        "categories": book.get("subject", []),
        "rating": 0,
        "page_count": book.get("number_of_pages_median", 0),
        "info_link": f"https://openlibrary.org{book.get('key', '')}" if "key" in book else "",
        "image_link": f"https://covers.openlibrary.org/b/id/{book.get('cover_i', '')}-L.jpg" if "cover_i" in book else "",
        "published_date": published_date,
        "fiction_status": fiction_status,
        "series_name": series_name,
        "isbn": isbn  # Added ISBN to return data
    }

def update_notion_page(page_id, book_data, original_title):
    """Update a Notion page with book information."""
    url = f"{NOTION_API_URL}/pages/{page_id}"
    
    # Prepare authors property - checking if authors exist in the database options
    authors_property = {
        "multi_select": [{"name": author} for author in book_data.get("authors", [])]
    }
    
    # Prepare categories/genres property
    genres_property = {
        "multi_select": [{"name": category} for category in book_data.get("categories", [])][:10]  # Notion has limits
    }
    
    # Prepare properties update
    properties = {
        PROPERTY_TITLE: {
            "title": [
                {
                    "text": {
                        "content": book_data.get("title", "")
                    }
                }
            ]
        },
        PROPERTY_DESCRIPTION: {
            "rich_text": [
                {
                    "text": {
                        "content": book_data.get("description", "")[:2000] if book_data.get("description") else ""
                    }
                }
            ]
        },
        PROPERTY_AUTHORS: authors_property,
        PROPERTY_GENRES: genres_property,
        PROPERTY_LINK: {
            "url": book_data.get("info_link", "")
        },
        PROPERTY_SEARCH_TERM: {
            "rich_text": [
                {
                    "text": {
                        "content": original_title
                    }
                }
            ]
        }
    }
    
    # Add cover image URL if available
    if book_data.get("image_link"):
        print("Adding cover image URL to properties...")
        properties[PROPERTY_COVER] = {
            "url": book_data.get("image_link", "")
        }
    
    # Add rating if available
    if book_data.get("rating", 0) > 0:
        properties[PROPERTY_RATING] = {
            "number": book_data.get("rating", 0)
        }
    
    # Add page count if available
    if book_data.get("page_count", 0) > 0:
        properties[PROPERTY_PAGES] = {
            "number": book_data.get("page_count", 0)
        }
    
    # Add published date if available
    if book_data.get("published_date"):
        properties[PROPERTY_DATE_PUBLISHED] = {
            "date": book_data.get("published_date")
        }
    
    # Add fiction/non-fiction status if available
    if book_data.get("fiction_status"):
        properties[PROPERTY_NON_FICTION] = {
            "select": {
                "name": book_data.get("fiction_status")
            }
        }
    
    # Add series if available
    if book_data.get("series_name"):
        properties[PROPERTY_SERIES] = {
            "multi_select": [{"name": book_data.get("series_name")}]
        }
    
    # Add ISBN if available
    if book_data.get("isbn"):
        print("Adding ISBN to properties...")
        properties[PROPERTY_ISBN] = {
            "rich_text": [
                {
                    "text": {
                        "content": book_data.get("isbn", "")
                    }
                }
            ]
        }
    
    # Prepare the update data
    data = {
        "properties": properties
    }
    
    # Add cover and icon if image is available
    if book_data.get("image_link"):
        print("Setting page cover and icon...")
        print(f"Using image URL: {book_data.get('image_link')}")
        data["cover"] = {
            "type": "external",
            "external": {
                "url": book_data.get("image_link")
            }
        }
        data["icon"] = {
            "type": "external",
            "external": {
                "url": book_data.get("image_link")
            }
        }
        print("Page cover and icon set successfully")
    
    print("Sending update request to Notion...")
    print(f"Request URL: {url}")
    print(f"Request headers: {notion_headers}")
    print(f"Request data: {json.dumps(data, indent=2)}")
    
    response = requests.patch(url, headers=notion_headers, json=data)
    if response.status_code != 200:
        print(f"Error updating page: {response.status_code}")
        print(f"Error response: {response.text}")
        print(f"Request data that failed: {json.dumps(data, indent=2)}")
        return False
    
    print("Page updated successfully")
    return True

def process_books():
    """Find books with semicolons and update them with metadata."""
    print("Starting to process books with semicolons in their titles")
    books = find_books_with_semicolon()
    
    if not books:
        print("No books found with titles ending in semicolons")
        return []
    
    print(f"Found {len(books)} books with semicolon titles to process")
    
    for book in books:
        print(f"Processing book: {book['search_query']}")
        book_data = None
        
        # If it's an ISBN, try a direct ISBN search first
        if book.get("is_isbn", False):
            # Try Google Books with ISBN search
            print(f"Searching by ISBN: {book['search_query']}")
            book_data = search_google_books(book["search_query"])
            
            # If Google Books fails, try Open Library with ISBN
            if not book_data:
                print("No results from Google Books for ISBN, trying Open Library...")
                book_data = search_open_library(book["search_query"])
        else:
            # Try Google Books first for title search
            print(f"Searching by title: {book['search_query']}")
            book_data = search_google_books(book["search_query"])
            
            # If Google Books fails, try Open Library
            if not book_data:
                print("No results from Google Books, trying Open Library...")
                book_data = search_open_library(book["search_query"])
            
            # If both fail, try adding 'book' to the search query
            if not book_data:
                modified_query = f"{book['search_query']} book"
                print(f"No results, trying with 'book' keyword added: {modified_query}")
                book_data = search_google_books(modified_query)
                
                if not book_data:
                    print("Still no results from Google Books with modified query, trying Open Library...")
                    book_data = search_open_library(modified_query)
        
        # If we found book data, update the Notion page
        if book_data:
            print(f"Found book info for '{book_data['title']}', updating Notion...")
            success = update_notion_page(book["id"], book_data, book["title"])
            if success:
                print("Successfully updated Notion page")
            else:
                print("Failed to update Notion page")
        else:
            print(f"No book information found for '{book['search_query']}'")
    
    return books

@app.route('/webhook', methods=['POST'])
def webhook_handler():
    """Handle Notion webhook requests."""
    # Basic security check (you might want to implement more robust security)
    token = request.headers.get('X-Notion-Token')
    if not token or token != os.getenv("WEBHOOK_SECRET"):
        return jsonify({"error": "Unauthorized"}), 401
    
    # Process the books immediately when triggered by a webhook
    process_books()
    return jsonify({"success": True})

@app.route('/fetch', methods=['GET'])
def fetch_handler():
    """Endpoint for scheduled triggers (e.g. from cron-job.org)."""
    process_books()
    return jsonify({"success": True})

def start_polling():
    """Start polling the database at regular intervals."""
    while True:
        try:
            print(f"Checking for new books ending with semicolons...")
            process_books()
        except Exception as e:
            print(f"Error during processing: {e}")
        
        print(f"Sleeping for {CHECK_INTERVAL} seconds...")
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    # Check if running in web server mode or polling mode
    if os.getenv("WEB_SERVER_MODE", "true").lower() == "true":
        # Start Flask web server
        port = int(os.getenv("PORT", 5000))
        app.run(host='0.0.0.0', port=port)
    else:
        # Start polling loop
        start_polling()