# Notion Book Search Extension

A Python extension that automatically fills in book details in your Notion reading list database when you add entries with titles ending in semicolons.

## How It Works

This application monitors your Notion BookList database for new entries with titles ending in a semicolon (;) and uses that title as a search term to fetch book metadata from Google Books API and Open Library. It then updates the Notion page with the retrieved information such as:

- Title
- Author(s)
- Description
- Rating
- Genres
- Page count
- Cover image
- Link to more information
- Publication date
- Fiction/Non-fiction status
- Series information

## Features

- 🔄 Automatically monitors your Notion database for new entries
- 📚 Searches for book information using Google Books and Open Library APIs
- 🔍 Handles both title searches and ISBN searches (for more accurate results)
- 🕒 Can run on a schedule or be triggered via webhooks
- 🔧 Easy to deploy on PythonAnywhere (free tier)

## Using the Extension

### Adding Books to Your Database

There are two ways to use this extension:

1. **Title Search:**
   - Add a new entry in your Notion database
   - Set the title to the book title followed by a semicolon (e.g., "The Hobbit;")
   - The extension will search for the book by title and update the entry

2. **ISBN Search (more accurate):**
   - Add a new entry in your Notion database
   - Set the title to the ISBN followed by a semicolon (e.g., "9780547928227;")
   - The extension will search for the book by ISBN and update the entry

### Fields that Get Updated

When a book is found, the following fields will be updated:

- Title (cleaned from the search)
- Description
- Author(s)
- Rating (from Google Books)
- Genres (based on categories)
- Pages (page count)
- Cover (URL to the book cover)
- Link (to Google Books or Open Library)
- DatePublished (publication date)
- Non/Fiction (determined from categories or subjects)
- Series (if found in the title or metadata)

## Deployment

For detailed deployment instructions, see the [Deployment Guide](deployment-guide.md).

## Requirements

- Python 3.9 or later
- Flask and other dependencies (see requirements.txt)
- A Notion account with the BookList database
- A Notion API integration key (already set up)

## Files in this Repository

- `app.py` - The main application code
- `wsgi.py` - Entry point for WSGI servers (used by PythonAnywhere)
- `test.py` - Simple test script to verify your setup
- `requirements.txt` - Required Python dependencies
- `.env` - Environment variables (API keys, etc.)

## Acknowledgements

This project was inspired by:
- [Notion Reading List by shaunakg](https://srg.id.au/notion-reading-list/)
- [NWatchlist Guide](https://nwatchlist.notion.site/Guide-d3e0cc0c1949463bbef2df40f0f515c5)

## License

This project is licensed under the MIT License.