# Notion Book Extension - PythonAnywhere Configuration

This file provides specific configuration for running the Notion Book Extension on PythonAnywhere.

## WSGI Configuration 

Add the following to your WSGI configuration file on PythonAnywhere:

```python
import sys
import os

# Add your project directory to the path
path = '/home/yourusername/notion-book-extension'
if path not in sys.path:
    sys.path.append(path)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(path, '.env'))

# Import the app as application
from app import app as application
```

## Virtual Environment

When setting up your virtual environment on PythonAnywhere, make sure to:

1. Create a virtual environment:
   ```
   python -m venv venv
   ```

2. Activate it:
   ```
   source venv/bin/activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Setting Up Scheduled Tasks

Add a task in PythonAnywhere's "Tasks" tab to run every hour (or your preferred interval):

```
cd /home/yourusername/notion-book-extension && python -c "import requests; requests.get('https://yourusername.pythonanywhere.com/fetch')"
```

This will trigger the application to check for new books at regular intervals.

## Checking Logs

To check logs and troubleshoot any issues:

1. View web app logs in the "Web" tab
2. View the custom application log:
   ```
   cat /home/yourusername/notion-book-extension/notion_book_extension.log
   ```

## Testing

After deployment, test the setup by adding a new entry to your Notion database with a title ending in semicolon.
