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

<<<<<<< HEAD
# Retrieve credentials from environment variables
USERNAME = os.getenv('INSTAGRAM_USERNAME')
PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
SESSION_FILE = 'session.json'  # Define the session file name
=======
# Retrieve credentials and session JSON string from environment variables
USERNAME = os.getenv('INSTAGRAM_USERNAME')
PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
SESSION_JSON_STRING = os.getenv('INSTAGRAM_SESSION_JSON')  # Get session JSON string

if not USERNAME or not SESSION_JSON_STRING:
    logger.error("Instagram username or session JSON is not set in environment variables.")
    raise ValueError("Instagram username or session JSON is not set in environment variables.")
>>>>>>> 7f09d57ca3f54b64083f223910b23cd53e54f8ec

# Initialize Instagrapi client
client = Client()

def save_session_to_file(session_data):
    """Saves session data to a JSON file."""
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(session_data, f)
        logger.info("Session saved to session.json")
    except Exception as e:
        logger.error(f"Failed to save session to file: {str(e)}")
        raise

def load_session_from_file():
    """Loads session data from the session.json file if it exists and is valid."""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.warning("session.json is corrupted or empty. It will be recreated.")
        except Exception as e:
            logger.error(f"Error loading session from file: {str(e)}")
    return None

try:
<<<<<<< HEAD
    # First, try to load session from the file
    session_data = load_session_from_file()

    if session_data:
        client.set_settings(session_data)
        logger.info("Session loaded successfully from session.json.")
    else:
        logger.info("No valid session found, attempting login...")
=======
    # Load existing session from JSON string
    session_data = json.loads(SESSION_JSON_STRING)
    client.set_settings(session_data)
    logger.info("Session loaded successfully.")
>>>>>>> 7f09d57ca3f54b64083f223910b23cd53e54f8ec

    # Verify if the session is still valid
    if not client.user_id:
        logger.info("Session invalid or not found. Logging in...")
        client.login(USERNAME, PASSWORD)
<<<<<<< HEAD

        # Save the new session to a file
        save_session_to_file(client.get_settings())
        logger.info("Logged in and session saved to session.json.")
=======
        # Dump updated session to environment variable if necessary (manual update needed)
        logger.info("Logged in and session saved.")
>>>>>>> 7f09d57ca3f54b64083f223910b23cd53e54f8ec
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
<<<<<<< HEAD

        # Save the session after logging in
        save_session_to_file(client.get_settings())
        logger.info("Logged in and session saved to session.json.")
        
=======
        # Dump updated session to environment variable if necessary (manual update needed)
        logger.info("Logged in and session saved.")
>>>>>>> 7f09d57ca3f54b64083f223910b23cd53e54f8ec
    except Exception as login_error:
        logger.error(f"Failed to log in: {str(login_error)}")
        raise
