from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random
import smtplib
import base64
import time

db = SQLAlchemy()

class Influencer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    followers = db.Column(db.Integer, nullable=False)
    following = db.Column(db.Integer, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Influencer {self.username}>'

# Function to generate a 6-digit OTP
def generate_otp():
    return random.randint(100000, 999999)

# Function to send OTP via email
def send_otp_via_email(receiver_email, otp):
    sender_email = "your_email@example.com"  # Replace with your email
    sender_password = "your_password"  # Replace with your email password
    subject = "Your OTP Code"
    body = f"Your OTP code is {otp}. Please use it to verify your profile."

    message = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, message)
            print(f"OTP sent to {receiver_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

