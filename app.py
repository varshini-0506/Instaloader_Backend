import os
import base64
from flask import Flask, request, jsonify
import instaloader
from flask_cors import CORS
import logging
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Instaloader
loader = instaloader.Instaloader()

# Retrieve credentials from environment variables
USERNAME = os.getenv('INSTALOADER_USERNAME')
PASSWORD = os.getenv('INSTALOADER_PASSWORD')

if not USERNAME or not PASSWORD:
    logger.error("Instagram credentials are not set in environment variables.")
    raise ValueError("Instagram credentials are not set in environment variables.")

# Define custom session directory and file
script_dir = os.path.dirname(os.path.abspath(__file__))
session_dir = os.path.join(script_dir, 'sessions')
os.makedirs(session_dir, exist_ok=True)
session_file = os.path.join(session_dir, f'session-{USERNAME}')

# Load session from environment variable if available
session_data = os.getenv('INSTALOADER_SESSION')
if session_data:
    logger.info("Loading session from environment variable.")
    try:
        session_bytes = base64.b64decode(session_data)
        with open(session_file, 'wb') as f:
            f.write(session_bytes)
        loader.load_session_from_file(USERNAME, filename=session_file)
        logger.info("Session loaded successfully from environment variable.")
    except Exception as e:
        logger.error(f"Failed to load session: {e}")
        # Optionally, attempt to login again or handle the error appropriately
else:
    try:
        loader.login(USERNAME, PASSWORD)
        logger.info("Logged in to Instagram successfully.")

        # Save the session file locally
        loader.save_session_to_file(session_file)
        logger.info(f"Session saved successfully to {session_file}.")
    except instaloader.exceptions.BadCredentialsException:
        logger.error("Invalid credentials, please check your username and password.")
        raise
    except instaloader.exceptions.TwoFactorAuthRequiredException:
        logger.error("Two-factor authentication is required.")
        # Since Render is non-interactive, handle 2FA appropriately
        # Recommended: Use an account without 2FA for automated logins
        raise
    except instaloader.exceptions.ConnectionException as ce:
        logger.error(f"Connection error during login: {str(ce)}")
        raise
    except Exception as e:
        logger.error(f"An error occurred during login: {str(e)}")
        raise

@app.route('/profile', methods=['GET'])
def get_profile():
    username = request.args.get('username')  # Get username from query parameters

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    try:
        # Load the profile
        profile = instaloader.Profile.from_username(loader.context, username)

        # Prepare the profile data
        profile_data = {
            'username': profile.username,
            'full_name': profile.full_name,
            'bio': profile.biography,
            'followers': profile.followers,
            'following': profile.followees,
            'posts': profile.mediacount,
        }

        # Calculate average likes and engagement rate
        total_likes = 0
        total_posts = 0

        for post in profile.get_posts():
            total_likes += post.likes
            total_posts += 1
            # Optionally, add a delay here to prevent rapid requests
            time.sleep(0.5)

        average_likes = total_likes / total_posts if total_posts > 0 else 0
        engagement_rate = (average_likes / profile.followers) * 100 if profile.followers > 0 else 0

        profile_data['average_likes'] = round(average_likes, 2)
        profile_data['engagement_rate'] = round(engagement_rate, 2)

        logger.debug(f"Fetched data for {username}: {profile_data}")

        return jsonify(profile_data), 200

    except instaloader.exceptions.ProfileNotExistsException:
        logger.error(f"Profile '{username}' not found.")
        return jsonify({'error': 'Profile not found'}), 404

    except instaloader.exceptions.ConnectionException as ce:
        logger.error(f"Connection error while fetching profile '{username}': {str(ce)}")
        return jsonify({'error': 'Connection error. Please try again later.'}), 503

    except instaloader.exceptions.BadCredentialsException:
        logger.error("Invalid Instagram credentials.")
        return jsonify({'error': 'Invalid Instagram credentials.'}), 401

    except instaloader.exceptions.TwoFactorAuthRequiredException:
        logger.error("Two-factor authentication is required.")
        return jsonify({'error': 'Two-factor authentication is required.'}), 401

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred.'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
