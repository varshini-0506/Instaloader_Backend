import os
import logging
from instagrapi import Client
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

# Retrieve credentials and session path from environment variables
USERNAME = os.getenv('INSTAGRAM_USERNAME')
PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
SESSION_PATH = os.getenv('INSTAGRAM_SESSION_PATH')  # Path to session file

if not USERNAME or not SESSION_PATH:
    logger.error("Instagram username or session path is not set in environment variables.")
    raise ValueError("Instagram username or session path is not set in environment variables.")

# Initialize Instagrapi client
client = Client()

try:
    # Attempt to load existing session
    client.load_settings(SESSION_PATH)
    logger.info("Session loaded successfully.")

    # Verify if the session is still valid
    if not client.is_user_authenticated:
        logger.info("Session invalid. Logging in...")
        client.login(USERNAME, PASSWORD)
        client.dump_settings(SESSION_PATH)
        logger.info("Logged in and session saved.")
    else:
        logger.info("Session is already authenticated.")

except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    try:
        # If loading session fails, attempt to login
        logger.info("Attempting to log in...")
        client.login(USERNAME, PASSWORD)
        client.dump_settings(SESSION_PATH)
        logger.info("Logged in and session saved.")
    except Exception as login_error:
        logger.error(f"Failed to log in: {str(login_error)}")
        raise
