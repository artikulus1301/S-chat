from flask_mail import Message
from flask import current_app, render_template
from app import mail

def send_verification_email(user):
    """Send email verification link"""
    try:
        msg = Message(
            subject='Verify your S-Chat account',
            recipients=[user.email],
            html=render_template('email_verification.html', 
                               user=user, 
                               verification_url=f"{current_app.config['BASE_URL']}/verify/{user.verification_token}")
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send verification email: {e}")
        return False

def send_password_reset_email(user, reset_token):
    """Send password reset email"""
    try:
        msg = Message(
            subject='Reset your S-Chat password',
            recipients=[user.email],
            html=render_template('password_reset.html',
                               user=user,
                               reset_url=f"{current_app.config['BASE_URL']}/reset-password/{reset_token}")
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send password reset email: {e}")
        return False

def send_notification_email(user, subject, message):
    """Send general notification email"""
    try:
        msg = Message(
            subject=subject,
            recipients=[user.email],
            html=render_template('notification.html',
                               user=user,
                               message=message)
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send notification email: {e}")
        return False