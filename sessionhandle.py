import os
import json
import logging
from instagrapi import Client
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Retrieve credentials and session JSON string from environment variables
USERNAME = os.getenv('INSTAGRAM_USERNAME')
PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
SESSION_JSON_STRING = os.getenv('INSTAGRAM_SESSION_JSON')  # Get session JSON string

if not USERNAME or not SESSION_JSON_STRING:
    logger.error("Instagram username or session JSON is not set in environment variables.")
    raise ValueError("Instagram username or session JSON is not set in environment variables.")

# Initialize Instagrapi client
client = Client()

try:
    # Load existing session from JSON string
    session_data = json.loads(SESSION_JSON_STRING)
    client.set_settings(session_data)
    logger.info("Session loaded successfully.")

    # Verify if the session is still valid
    if not client.is_user_authenticated:
        logger.info("Session invalid. Logging in...")
        client.login(USERNAME, PASSWORD)
        # Dump updated session to environment variable if necessary (manual update needed)
        logger.info("Logged in and session saved.")
    else:
        logger.info("Session is already authenticated.")

except json.JSONDecodeError as e:
    logger.error(f"Error decoding JSON: {str(e)}")
    raise
except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    try:
        # If loading session fails, attempt to login
        logger.info("Attempting to log in...")
        client.login(USERNAME, PASSWORD)
        # Dump updated session to environment variable if necessary (manual update needed)
        logger.info("Logged in and session saved.")
    except Exception as login_error:
        logger.error(f"Failed to log in: {str(login_error)}")
        raise
