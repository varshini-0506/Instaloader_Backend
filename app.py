import os
import json
from flask import Flask, request, jsonify
from instagrapi import Client
from flask_cors import CORS
import logging
from dotenv import load_dotenv
import time
from datetime import datetime
from models import db, Influencer, generate_otp,send_otp_via_email
import re
import requests
import base64
import random
import smtplib

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
    username = request.args.get('username')

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    try:
        # Load the profile
        profile = client.user_info_by_username(username)

        # Prepare the profile data
        profile_data = {
            'username': profile.username,
            'full_name': profile.full_name,
            'bio': profile.biography,
            'followers': profile.follower_count,
            'following': profile.following_count,
            'posts': profile.media_count,
            'is_business': profile.is_business,
            'email': profile.public_email,
            'phone_number': profile.contact_phone_number,
            'category': profile.category,
        }

        # Fetch profile picture
        profile_pic_response = requests.get(profile.profile_pic_url)
        profile_pic_base64 = base64.b64encode(profile_pic_response.content).decode('utf-8')
        profile_data['profile_pic_base64'] = profile_pic_base64

        # Generate OTP
        otp = generate_otp()

        # Send OTP via DM
        user_id = profile.pk  # Primary key of the user
        dm_message = f"Hello {profile.full_name or profile.username}, your OTP is: {otp}"
        client.direct_send(dm_message, [user_id])

        profile_data['otp'] = otp
        profile_data['dm_sent'] = True
        profile_data['message'] = f"OTP sent via DM to {profile.username}"

        # Log and store profile data
        logger.debug(f"Retrieved profile data for {username}: {profile_data}")

        influencer = Influencer.query.filter_by(username=username).first()
        if influencer:
            influencer.followers = profile.follower_count
            influencer.following = profile.following_count
            influencer.updated_at = datetime.utcnow()
        else:
            influencer = Influencer(
                username=profile.username,
                followers=profile.follower_count,
                following=profile.following_count,
                updated_at=datetime.utcnow()
            )
            db.session.add(influencer)

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
    
#fetch recent post details
@app.route('/profile/post_interactions', methods=['GET'])
def get_post_interactions():
    username = request.args.get('username')  # Get username from query parameters

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    try:
        # Attempt to load the profile information
        profile = client.user_info_by_username(username)
        
        # Fetch the most recent post, if available
        media = client.user_medias(profile.pk, amount=1)
        
        if not media:
            return jsonify({'error': 'No posts found for this user.'}), 404

        recent_post = media[0]
        
        # Get likes for the recent post
        likers = client.media_likers(recent_post.pk)
        liker_usernames = [user.username for user in likers]

        # Get comments for the recent post
        comments = client.media_comments(recent_post.pk)
        commenter_usernames = [comment.user.username for comment in comments]
        
        # Get location if tagged
        #location = recent_post.location.name if recent_post.location else "No location tagged"

        # Construct the post URL using the shortcode
        post_url = f"https://www.instagram.com/p/{recent_post.code}/"  # `recent_post.code` gives the shortcode

        # Prepare the data for response
        post_interactions_data = {
            'post_id': recent_post.pk,
             'post_url': post_url,
            'like_count': recent_post.like_count,
            'comment_count': recent_post.comment_count,
            'likers': liker_usernames,
            'commenters': commenter_usernames,
            'caption': recent_post.caption_text,  # Caption of the post
            'media_type': 'Video' if recent_post.media_type == 2 else 'Image' if recent_post.media_type == 1 else 'Album',
            #'location': location
        }

        logger.debug(f"Retrieved post interactions for {username}: {post_interactions_data}")

        return jsonify(post_interactions_data), 200

    except Exception as e:
        logger.error(f"An unexpected error occurred in get_post_interactions: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred.', 'details': str(e)}), 500

@app.route('/post/details_by_url', methods=['GET'])
def get_post_details_by_url():
    post_url = request.args.get('post_url')  # Get the post URL from query parameters

    if not post_url:
        return jsonify({'error': 'Post URL is required'}), 400

    try:
        # Extract the shortcode from the URL
        match = re.search(r'/p/([^/]+)/', post_url)
        if not match:
            return jsonify({'error': 'Invalid post URL format'}), 400

        shortcode = match.group(1)
        
        #get  post_id from post url
        post_pk= client.media_pk_from_url(post_url)
        print("post pk:",post_pk)

        
        post = client.media_info(post_pk)
        print("post details:",post)
        
        # Prepare the data for response
        post_data = {
            'post_id': post_pk,
            'post_url': str(post_url),
            'like_count': post.like_count,
            'comment_count': post.comment_count,
            'caption': post.caption_text,
            'media_type': 'Video' if post.media_type == 2 else 'Image' if post.media_type == 1 else 'Album',
            'username': post.user.username,
            'full_name': post.user.full_name,
            'profile_pic_url': str(post.user.profile_pic_url),
            'location': post.location.name if post.location else "No location tagged"
        }

        # Fetch profile picture
        profile_pic_response = requests.get(post.user.profile_pic_url)
        profile_pic_base64 = base64.b64encode(profile_pic_response.content).decode('utf-8')
        post_data['profile_pic_base64'] = profile_pic_base64
        #to display the img---> src={`data:image/jpeg;base64,${postdata.profile_pic_base64}`}

        # Fetch the usernames of people who liked the post
        likers = client.media_likers(post_pk)
        post_data['likers'] = [user.username for user in likers]  # List of usernames of people who liked the post

        # Fetch the comments and the usernames of commenters
        comments = client.media_comments(post_pk)
        post_data['comments'] = [
            {'username': comment.user.username, 'text': comment.text}
            for comment in comments
        ]  # List of dictionaries with commenter usernames and comment text

        return jsonify(post_data), 200

    except Exception as e:
        logger.error(f"An unexpected error occurred in get_post_details_by_url: {str(e)}")
        return jsonify({'error': 'An unexpected error occurred.', 'details': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
