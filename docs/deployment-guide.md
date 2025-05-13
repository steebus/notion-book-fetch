# Deployment Guide for Notion Book Extension

This guide will walk you through deploying your Notion Book Extension using PythonAnywhere, a free hosting platform specifically designed for Python applications.

## Prerequisites

1. A Notion account with your book database (already set up)
2. Your Notion API integration key (already created: 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)
3. A PythonAnywhere account (free tier is sufficient)

## Step 1: Set Up a PythonAnywhere Account

1. Create an account on [PythonAnywhere](https://www.pythonanywhere.com) if you don't have one.
2. Once logged in, go to the Dashboard.
3. Click on "Files" in the navigation bar to access your file system.

## Step 2: Upload Your Code

1. Create a new directory for your project:
   ```
   $ mkdir notion-book-extension
   ```
2. Navigate to that directory:
   ```
   $ cd notion-book-extension
   ```
3. Create a new file called `app.py` and paste the full code from the "Notion Book Search Extension" artifact.
4. Create a new file called `requirements.txt` with the following contents:
   ```
   flask==2.3.3
   requests==2.31.0
   python-dotenv==1.0.0
   gunicorn==21.2.0
   ```
5. Create a `.env` file with these variables:
   ```
   NOTION_API_KEY=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
   DATABASE_ID=9c847e888b7d4cf19630c770c08fce8c
   WEBHOOK_SECRET=choose_a_secure_random_string
   CHECK_INTERVAL=300
   WEB_SERVER_MODE=true
   ```

## Step 3: Set Up a Web App on PythonAnywhere

1. Go to the "Web" tab on the PythonAnywhere dashboard.
2. Click "Add a new web app".
3. Choose a domain name (you'll get a subdomain like yourusername.pythonanywhere.com).
4. Select "Manual configuration" (not Flask).
5. Choose Python 3.9 or later.

## Step 4: Configure the Web App

1. In the "Code" section, set the path to your working directory:
   ```
   /home/yourusername/notion-book-extension
   ```
2. Set the path to your WSGI configuration file - this should be pre-filled.
3. Click on the WSGI configuration file link to edit it.
4. Replace the content with the following (adjust your username):
   ```python
   import sys
   import os
   
   path = '/home/yourusername/notion-book-extension'
   if path not in sys.path:
       sys.path.append(path)
   
   # Load environment variables
   from dotenv import load_dotenv
   load_dotenv(os.path.join(path, '.env'))
   
   from app import app as application
   ```

## Step 5: Create a Virtual Environment and Install Dependencies

1. Go back to the "Consoles" tab and start a new Bash console.
2. Navigate to your project directory:
   ```
   $ cd notion-book-extension
   ```
3. Create a virtual environment:
   ```
   $ python -m venv venv
   ```
4. Activate the virtual environment:
   ```
   $ source venv/bin/activate
   ```
5. Install the dependencies:
   ```
   $ pip install -r requirements.txt
   ```

## Step 6: Configure Web App to Use Your Virtual Environment

1. Go back to the "Web" tab.
2. In the "Virtualenv" section, enter the path to your virtual environment:
   ```
   /home/yourusername/notion-book-extension/venv
   ```
3. Click the "Reload" button for your web app.

## Step 7: Set Up a Scheduled Task for Polling

PythonAnywhere free accounts have restrictions on long-running background tasks, so let's set up a scheduled task instead:

1. Go to the "Tasks" tab.
2. Add a new scheduled task that runs every hour (or your preferred interval).
3. Enter this command (adjust your username):
   ```
   cd /home/yourusername/notion-book-extension && python -c "import requests; requests.get('https://yourusername.pythonanywhere.com/fetch')"
   ```

## Step 8: Test Your Setup

1. Make sure your web app is reloaded and running.
2. Add a new entry to your Notion database with a title ending in semicolon (e.g., "The Hobbit;").
3. Wait for the scheduled task to run, or trigger it manually by visiting your `/fetch` endpoint.
4. Check your Notion database to see if the entry was updated with book information.

## Using ISBN Numbers

For more accurate book lookups, you can use ISBN numbers:
1. Add a new entry with the title format: "9780547928227;" (the ISBN followed by a semicolon)
2. The system will detect this as an ISBN and perform a more accurate search

## Troubleshooting

- Check the error logs in the "Web" tab if your app is not working.
- Ensure your Notion integration has access to your database.
- Verify your environment variables are correctly set.
- Check that your virtual environment has all the required packages installed.

## Setting Up External Triggering (Optional)

If you want to have your script run more frequently without manual intervention, you can use an external service like [cron-job.org](https://cron-job.org) to ping your `/fetch` endpoint at regular intervals.

1. Sign up for a free account on cron-job.org.
2. Create a new cronjob that makes a GET request to `https://yourusername.pythonanywhere.com/fetch`.
3. Set the execution schedule (e.g., every 5 minutes).

