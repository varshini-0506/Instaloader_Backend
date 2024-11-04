import os
import json
from flask import Flask, request, jsonify
from instagrapi import Client
from flask_cors import CORS
import logging
from dotenv import load_dotenv
import time
from datetime import datetime
from models import db, Influencer

# Load environment variables from .env file
load_dotenv()

app = Flask(_name_)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(_name_)

# Configure database
NEON_DB_URL = os.getenv('NEON_DB_URL')
if not NEON_DB_URL:
    logger.error("NeonDB URL not set in environment variables.")
    raise ValueError("NEON_DB_URL is required.")

app.config['SQLALCHEMY_DATABASE_URI'] = NEON_DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db.init_app(app)

# Create database tables
with app.app_context():
    db.create_all()

# Initialize Instagrapi client
client = Client()

# Retrieve credentials and session JSON string from environment variables
USERNAME = os.getenv('INSTAGRAM_USERNAME')
PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
SESSION_JSON_STRING = os.getenv('INSTAGRAM_SESSION_JSON')  # Get session JSON string

if not SESSION_JSON_STRING:
    logger.error("Instagram session JSON is not set in environment variables.")
    raise ValueError("Instagram session JSON is not set in environment variables.")

# Load session from the JSON string
try:
    session_data = json.loads(SESSION_JSON_STRING)
    client.set_settings(session_data)
    logger.info("Session loaded successfully.")
    
    # Optionally, verify if the session is still valid
    if not client.user_id:
        logger.error("Invalid session. Please run create_session.py to regenerate the session.")
except json.JSONDecodeError as e:
    logger.error(f"Error decoding JSON: {str(e)}")
    raise
except Exception as e:
    logger.error(f"An error occurred during session loading: {str(e)}")
    raise

@app.route('/profile', methods=['GET'])
def get_profile():
    username = request.args.get('username')  # Get username from query parameters

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    try:
        # Load the profile
        profile = client.user_info_by_username(username)

        # Log the entire profile data for debugging
        logger.debug(f"Profile data for {username}: {profile.dict()}")

        # Prepare the profile data
        profile_data = {
            'username': profile.username,
            'full_name': profile.full_name,
            'bio': profile.biography,
            'followers': profile.follower_count,
            'following': profile.following_count,
            'posts': profile.media_count,
            'is_business': profile.is_business,
        }

        # Initialize fields
        public_email = "Not Available"
        public_phone_number = "Not Available"
        business_category_name = "Not Available"

        # Check if the account is a business account
        if profile.is_business:
            logger.debug(f"{username} is a business account.")

            # Attempt to access 'category_name' directly
            business_category_name = getattr(profile, 'category_name', "Not Available")

            # If 'category_name' is not available, check 'category_info'
            if business_category_name == "Not Available" and hasattr(profile, 'category_info') and profile.category_info:
                # 'category_info' might be a list or a single object
                if isinstance(profile.category_info, list) and len(profile.category_info) > 0:
                    # If it's a list, extract the first category's name
                    business_category_name = profile.category_info[0].get('name', "Not Available")
                elif isinstance(profile.category_info, dict):
                    # If it's a dict, get the 'name' key
                    business_category_name = profile.category_info.get('name', "Not Available")

            # Retrieve public email and phone number
            public_email = profile.public_email or "Not Available"
            public_phone_number = profile.public_phone_number or "Not Available"

            logger.debug(f"Retrieved business details for {username}: Email={public_email}, Phone={public_phone_number}, Category={business_category_name}")

        else:
            logger.debug(f"{username} is not a business account.")

        # Update profile data with business details
        profile_data.update({
            'public_email': public_email,
            'public_phone_number': public_phone_number,
            'business_category_name': business_category_name,
        })

        logger.debug(f"Final profile data for {username}: {profile_data}")

        return jsonify(profile_data), 200

    except instagrapi.exceptions.UserNotFound:
        logger.warning(f"User {username} not found.")
        return jsonify({'error': 'User not found.'}), 404
    except instagrapi.exceptions.ClientError as e:
        logger.error(f"Client error: {str(e)}")
        return jsonify({'error': 'A client error occurred.'}), 400
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_profile: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred.'}), 500

@app.route('/profile/stats', methods=['GET'])
def get_profile_stats():
    username = request.args.get('username')  # Get username from query parameters

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    try:
        # Load the profile
        profile = client.user_info_by_username(username)

        # Get recent media and calculate average likes
        total_likes = 0
        total_posts = 0
        max_posts = 10  # Limit to the most recent 10 posts

        media = client.user_medias(profile.pk, amount=max_posts)
        for post in media:
            total_likes += post.like_count
            total_posts += 1
            time.sleep(0.5)  # Delay to prevent rapid requests

        average_likes = total_likes / total_posts if total_posts > 0 else 0
        engagement_rate = (average_likes / profile.follower_count) * 100 if profile.follower_count > 0 else 0

        stats_data = {
            'average_likes': round(average_likes, 2),
            'engagement_rate': round(engagement_rate, 2),
        }

        logger.debug(f"Fetched stats for {username}: {stats_data}")

        return jsonify(stats_data), 200

    except Exception as e:
        logger.error(f"An unexpected error occurred in get_profile_stats: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred.'}), 500

if _name_ == '_main_':
    app.run(debug=True, port=5000)
