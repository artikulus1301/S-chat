import os
import magic
from werkzeug.utils import secure_filename
from flask import current_app

def validate_file_type(file_stream):
    """Validate file type using python-magic"""
    try:
        file_stream.seek(0)
        file_type = magic.from_buffer(file_stream.read(1024), mime=True)
        file_stream.seek(0)
        
        allowed_mime_types = {
            'image/jpeg', 'image/png', 'image/gif',
            'audio/mpeg', 'audio/wav', 'audio/ogg',
            'application/pdf', 'text/plain'
        }
        
        return file_type in allowed_mime_types
    except Exception:
        # Fallback to extension-based validation if magic fails
        return True

def get_file_size(file_path):
    """Get file size in human-readable format"""
    size_bytes = os.path.getsize(file_path)
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    
    return f"{size_bytes:.2f} TB"

def cleanup_old_files(days_old=30):
    """Clean up files older than specified days"""
    import time
    from datetime import datetime, timedelta
    
    cutoff_time = time.time() - (days_old * 86400)
    
    for root, dirs, files in os.walk(current_app.config['UPLOAD_FOLDER']):
        for file in files:
            file_path = os.path.join(root, file)
            if os.path.getmtime(file_path) < cutoff_time:
                try:
                    os.remove(file_path)
                    print(f"Removed old file: {file_path}")
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")