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

app = Flask(__name__)
CORS(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

        # Prepare the profile data
        profile_data = {
            'username': profile.username,
            'followers': profile.follower_count,
            'following': profile.following_count,
            'updated_at': datetime.utcnow()  # Current timestamp for update
        }

        logger.debug(f"Retrieved profile data for {username}: {profile_data}")

        # Insert or update the profile data in the database
        influencer = Influencer.query.filter_by(username=username).first()
        if influencer:
            # Update existing record
            influencer.followers = profile.follower_count
            influencer.following = profile.following_count
            influencer.updated_at = datetime.utcnow()  # Update timestamp
        else:
            # Create a new record
            influencer = Influencer(
                username=profile.username,
                followers=profile.follower_count,
                following=profile.following_count,
                updated_at=datetime.utcnow()  # Set current timestamp
            )
            db.session.add(influencer)

        # Commit the changes to the database
        db.session.commit()
        logger.info(f"Profile data for {username} has been stored/updated in the database.")

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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
