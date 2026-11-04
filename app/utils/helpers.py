import os
import uuid
from pathlib import Path
from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image
from app.extensions import db
from app.models import Activity, Notification

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_uploaded_image(file_storage, folder_name='covers', max_size=None):
    """
    Validates and saves an uploaded image file using a safe UUID filename.
    folder_name: 'covers', 'banners', or 'avatars'
    """
    if not file_storage or file_storage.filename == '':
        return None

    if not allowed_file(file_storage.filename):
        raise ValueError("Invalid file extension. Allowed formats: PNG, JPG, JPEG, WEBP, GIF.")

    # Validate image data using Pillow
    try:
        img = Image.open(file_storage.stream)
        img.verify()
        # Reset stream position after verify
        file_storage.stream.seek(0)
    except Exception:
        raise ValueError("The uploaded file is not a valid image.")

    # Determine destination folder
    base_upload_path = Path(current_app.config['UPLOAD_FOLDER']) / folder_name
    base_upload_path.mkdir(parents=True, exist_ok=True)

    # Secure new filename with UUID
    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4().hex}.{ext}"
    dest_path = base_upload_path / unique_filename

    # Save and optionally process image
    img = Image.open(file_storage.stream)
    
    # Convert RGBA to RGB for JPEG if needed
    if ext in ['jpg', 'jpeg'] and img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
        
    if max_size:
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
    img.save(dest_path)
    return unique_filename


def log_activity(user_id, activity_type, game_id, description):
    """Logs a user social action to their activity stream."""
    try:
        activity = Activity(
            user_id=user_id,
            activity_type=activity_type,
            game_id=game_id,
            description=description
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error logging activity: {e}")


def create_notification(user_id, actor_id, notif_type, message, link=None):
    """Sends an in-app notification to user_id."""
    # Don't notify oneself
    if user_id == actor_id:
        return
        
    try:
        notif = Notification(
            user_id=user_id,
            actor_id=actor_id,
            type=notif_type,
            message=message,
            link=link,
            is_read=False
        )
        db.session.add(notif)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating notification: {e}")

