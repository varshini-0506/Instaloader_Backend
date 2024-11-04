import os
<<<<<<< HEAD
=======
import json
>>>>>>> 7f09d57ca3f54b64083f223910b23cd53e54f8ec
from flask import Flask, request, jsonify
from flask_cors import CORS
from instagrapi import Client
from dotenv import load_dotenv
import logging
import time
from datetime import datetime
from models import db, Influencer

# Load environment variables
load_dotenv()

# Initialize Flask app
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

<<<<<<< HEAD
# Retrieve Instagram credentials
USERNAME = os.getenv('INSTAGRAM_USERNAME')
PASSWORD = os.getenv('INSTAGRAM_PASSWORD')
SESSION_PATH = os.getenv('INSTAGRAM_SESSION_PATH')  

if not USERNAME or not SESSION_PATH:
    logger.error("Instagram username or session path is not set in environment variables.")
    raise ValueError("Instagram username or session path is not set in environment variables.")

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

<<<<<<< HEAD
        # Check if the account is a business account
        if profile.is_business:
            # Attempt to access 'category_name' directly
            business_category_name = getattr(profile, 'category_name', None)

            # If 'category_name' is not available, check 'category_info'
            if not business_category_name and hasattr(profile, 'category_info') and profile.category_info:
=======
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
>>>>>>> 7f09d57ca3f54b64083f223910b23cd53e54f8ec
                # 'category_info' might be a list or a single object
                if isinstance(profile.category_info, list) and len(profile.category_info) > 0:
                    # If it's a list, extract the first category's name
                    business_category_name = profile.category_info[0].get('name', "Not Available")
                elif isinstance(profile.category_info, dict):
                    # If it's a dict, get the 'name' key
                    business_category_name = profile.category_info.get('name', "Not Available")
<<<<<<< HEAD
                else:
                    # Fallback if the structure is unexpected
                    business_category_name = "Not Available"

            # Final fallback
            business_category_name = business_category_name or "Not Available"

            profile_data.update({
                'public_email': profile.public_email or "Not Available",
                'public_phone_number': profile.public_phone_number or "Not Available",
                'business_category_name': business_category_name,
            })
        else:
            profile_data.update({
                'public_email': "Not a business account",
                'public_phone_number': "Not a business account",
                'business_category_name': "Not a business account",
            })

        logger.debug(f"Fetched profile data for {username}: {profile_data}")

        # Store or update the influencer data in NeonDB
        influencer = Influencer.query.filter_by(username=username).first()
        if influencer:
            influencer.followers = profile.follower_count
            influencer.following = profile.following_count
            influencer.updated_at = datetime.utcnow()
            logger.info(f"Updated influencer data for {username}")
        else:
            influencer = Influencer(
                username=username,
                followers=profile.follower_count,
                following=profile.following_count
            )
            db.session.add(influencer)
            logger.info(f"Added new influencer data for {username}")

        db.session.commit()
=======

        return jsonify(profile_data), 200

    except instagrapi.exceptions.UserNotFound:
<<<<<<< HEAD
=======
        logger.warning(f"User {username} not found.")
>>>>>>> 7f09d57ca3f54b64083f223910b23cd53e54f8ec
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

    except instagrapi.exceptions.UserNotFound:
        return jsonify({'error': 'User not found.'}), 404
    except instagrapi.exceptions.ClientError as e:
        logger.error(f"Client error: {str(e)}")
        return jsonify({'error': 'A client error occurred.'}), 400
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_profile_stats: {str(e)}")
<<<<<<< HEAD
        return jsonify({'error': 'An unexpected error occurred.'}), 500

@app.route('/influencer/<username>', methods=['GET'])
def get_stored_influencer(username):
    influencer = Influencer.query.filter_by(username=username).first()
    if influencer:
        influencer_data = {
            'username': influencer.username,
            'followers': influencer.followers,
            'following': influencer.following,
            'updated_at': influencer.updated_at
        }
        return jsonify(influencer_data), 200
    else:
        return jsonify({'error': 'Influencer not found in the database.'}), 404
    
@app.route('/profile/followers', methods=['GET'])
def get_followers():
    username = request.args.get('username')  # Get username from query parameters

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    try:
        # Load the profile
        profile = client.user_info_by_username(username)

        # Fetch followers' usernames
        followers = client.user_followers(profile.pk)
        followers_usernames = [f.username for f in followers.values()]

        logger.debug(f"Fetched followers for {username}: {followers_usernames}")

        return jsonify({'followers': followers_usernames}), 200

    except instagrapi.exceptions.UserNotFound:
        return jsonify({'error': 'User not found.'}), 404
    except instagrapi.exceptions.ClientError as e:
        logger.error(f"Client error: {str(e)}")
        return jsonify({'error': 'A client error occurred.'}), 400
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_followers: {str(e)}")
=======
>>>>>>> 7f09d57ca3f54b64083f223910b23cd53e54f8ec
        return jsonify({'error': 'An unexpected error occurred.'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
