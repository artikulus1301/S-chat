from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid

uploads_bp = Blueprint('uploads', __name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_file_type(filename):
    """Determine file type from extension"""
    image_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    audio_extensions = {'mp3', 'wav', 'ogg'}
    filename_lower = filename.lower()
    
    ext = filename_lower.rsplit('.', 1)[1] if '.' in filename_lower else ''
    
    if ext in image_extensions:
        return 'image'
    elif ext in audio_extensions:
        return 'audio'
    else:
        return 'file'

@uploads_bp.route('/upload', methods=['POST'])
def upload_file():
    """Handle file uploads for messages"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        user_id = request.form.get('user_id')
        chat_id = request.form.get('chat_id')
        
        if not user_id or not chat_id:
            return jsonify({'error': 'User ID and Chat ID are required'}), 400
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            # Generate unique filename
            original_filename = secure_filename(file.filename)
            file_extension = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
            
            # Create user-specific directory
            user_upload_dir = os.path.join(
                current_app.config['UPLOAD_FOLDER'], 
                f"user_{user_id}"
            )
            os.makedirs(user_upload_dir, exist_ok=True)
            
            # Save file
            file_path = os.path.join(user_upload_dir, unique_filename)
            file.save(file_path)
            
            # Determine file type
            file_type = get_file_type(original_filename)
            
            return jsonify({
                'message': 'File uploaded successfully',
                'file_path': f"user_{user_id}/{unique_filename}",
                'original_filename': original_filename,
                'file_type': file_type,
                'file_size': os.path.getsize(file_path)
            }), 200
        else:
            return jsonify({'error': 'File type not allowed'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@uploads_bp.route('/upload/audio', methods=['POST'])
def upload_audio():
    """Handle voice message uploads"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        user_id = request.form.get('user_id')
        chat_id = request.form.get('chat_id')
        
        if not user_id or not chat_id:
            return jsonify({'error': 'User ID and Chat ID are required'}), 400
        
        if audio_file.filename == '':
            return jsonify({'error': 'No audio file selected'}), 400
        
        # Check if it's an audio file
        if audio_file and audio_file.content_type.startswith('audio/'):
            # Generate unique filename
            unique_filename = f"voice_{uuid.uuid4().hex}.webm"  # WebM for browser recordings
            
            # Create user-specific directory
            user_upload_dir = os.path.join(
                current_app.config['UPLOAD_FOLDER'], 
                f"user_{user_id}"
            )
            os.makedirs(user_upload_dir, exist_ok=True)
            
            # Save audio file
            file_path = os.path.join(user_upload_dir, unique_filename)
            audio_file.save(file_path)
            
            return jsonify({
                'message': 'Voice message uploaded successfully',
                'file_path': f"user_{user_id}/{unique_filename}",
                'file_type': 'audio',
                'file_size': os.path.getsize(file_path),
                'duration': request.form.get('duration', 0)  # Duration in seconds
            }), 200
        else:
            return jsonify({'error': 'Invalid audio file'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@uploads_bp.route('/files/<path:filename>', methods=['GET'])
def get_file(filename):
    """Serve uploaded files"""
    try:
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        # In production, use proper file serving (nginx, CDN, etc.)
        from flask import send_from_directory
        
        directory = os.path.dirname(file_path)
        file_name = os.path.basename(file_path)
        
        return send_from_directory(directory, file_name)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500