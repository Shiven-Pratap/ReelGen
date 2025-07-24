from werkzeug.utils import secure_filename
from app.models import User, UserData
import os
from datetime import datetime
import shutil
from moviepy import *
from moviepy import *
from PIL import Image
import numpy as np
from flask import Flask, Blueprint, render_template, request, redirect, flash, url_for, session
from app import db
import requests
import tempfile

upload_bp = Blueprint("upload", __name__)

UPLOAD_FOLDER = 'app/static/uploads'
REEL_FOLDER = 'app/static/reels'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# ElevenLabs API Configuration - Replace with your actual API key
ELEVENLABS_API_KEY = "sk_7b791f26662f162706ff4e47bcb28c9e1f2829fa4afafcff"
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID (Rachel)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REEL_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_audio_from_text(text, output_path):
    """
    Generate audio from text using ElevenLabs API
    """
    if not text or not text.strip():
        print("No text provided for audio generation")
        return None
    
    print(f"Generating audio for text: {text[:50]}...")
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text.strip(),
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    try:
        print("Making request to ElevenLabs API...")
        response = requests.post(url, json=data, headers=headers)
        print(f"Response status code: {response.status_code}")
        
        if response.status_code != 200:
            print(f"API Error: {response.text}")
            return None
            
        response.raise_for_status()
        
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"Audio saved to: {output_path}")
        return output_path
    except requests.exceptions.RequestException as e:
        print(f"Error generating audio: {e}")
        return None

@upload_bp.route("/")
def home():
    return render_template("upload.html")

@upload_bp.route("/generate_reel", methods=["POST"])
def generate_reel():
    uploaded_files = request.files.getlist("images[]")
    reel_title = request.form.get('Reel-title', 'Generated Reel')
    audio_text = request.form.get('audio', '')
    
    user_id = session.get('user_id')
    if not user_id:
        flash("Please login", "danger")
        return redirect(url_for("auth.login"))
    
    user_upload_dir = os.path.join(UPLOAD_FOLDER, str(user_id))
    os.makedirs(user_upload_dir, exist_ok=True)
    image_arrays = []
    target_size = (720, 1280)  # width, height
    target_aspect_ratio = target_size[0] / target_size[1]  # 0.5625
    
    def smart_resize_image(img, target_size):
        """
        Smart resize that maintains aspect ratio and crops intelligently
        """
        original_width, original_height = img.size
        original_aspect_ratio = original_width / original_height
        target_width, target_height = target_size
        
        if original_aspect_ratio > target_aspect_ratio:
            # Image is wider than target - crop width (center crop)
            # Scale based on height
            scale_factor = target_height / original_height
            new_width = int(original_width * scale_factor)
            new_height = target_height
            
            # Resize maintaining aspect ratio
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Center crop to target width
            left = (new_width - target_width) // 2
            right = left + target_width
            img_cropped = img_resized.crop((left, 0, right, new_height))
            
            return img_cropped
            
        elif original_aspect_ratio < target_aspect_ratio:
            # Image is taller than target - crop height (center crop)
            # Scale based on width
            scale_factor = target_width / original_width
            new_width = target_width
            new_height = int(original_height * scale_factor)
            
            # Resize maintaining aspect ratio
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Center crop to target height
            top = (new_height - target_height) // 2
            bottom = top + target_height
            img_cropped = img_resized.crop((0, top, new_width, bottom))
            
            return img_cropped
            
        else:
            # Perfect aspect ratio match - just resize
            return img.resize(target_size, Image.Resampling.LANCZOS)
    
    def fit_resize_with_padding(img, target_size, bg_color=(0, 0, 0)):
        """
        Alternative: Resize to fit within target size and add padding
        """
        original_width, original_height = img.size
        target_width, target_height = target_size
        
        # Calculate scale factor to fit image within target size
        scale_factor = min(target_width / original_width, target_height / original_height)
        
        # Calculate new dimensions
        new_width = int(original_width * scale_factor)
        new_height = int(original_height * scale_factor)
        
        # Resize image
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Create new image with target size and background color
        result = Image.new('RGB', target_size, bg_color)
        
        # Calculate position to center the resized image
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        
        # Paste resized image onto the background
        result.paste(img_resized, (x_offset, y_offset))
        
        return result
    
    # Process uploaded images
    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(user_upload_dir, filename)
            file.save(save_path)
            
            # Load and process image
            img = Image.open(save_path).convert("RGB")
            
            # Option 1: Fit entire image with padding (preserves full image)
            processed_img = fit_resize_with_padding(img, target_size, bg_color=(0, 0, 0))
            
            # Option 2: Smart crop (uncomment to use instead if you prefer cropping)
            # processed_img = smart_resize_image(img, target_size)
            
            image_arrays.append(np.array(processed_img))
    
    if not image_arrays:
        flash("No valid images uploaded.", "danger")
        return redirect(url_for("upload.home"))
    
    # Create temporary audio file
    audio_path = None
    audio_duration = 0
    
    print(f"Audio text received: '{audio_text}'")
    
    if audio_text and audio_text.strip():
        print("Creating temporary audio file...")
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        audio_path = generate_audio_from_text(audio_text, temp_audio.name)
        temp_audio.close()
        
        if audio_path and os.path.exists(audio_path):
            print(f"Audio file created: {audio_path}")
            print(f"Audio file size: {os.path.getsize(audio_path)} bytes")
            
            try:
                # Get audio duration
                audio_clip = AudioFileClip(audio_path)
                audio_duration = audio_clip.duration
                print(f"Audio duration: {audio_duration} seconds")
                audio_clip.close()
            except Exception as e:
                print(f"Error reading audio file: {e}")
                audio_duration = 0
        else:
            print("Failed to create audio file")
            flash("Failed to generate audio. Creating video without sound.", "warning")
    else:
        print("No audio text provided")
    
    # Generate video filename
    reel_name = f"reel_{str(datetime.utcnow().timestamp()).replace('.', '_')}.mp4"
    reel_path = os.path.join(REEL_FOLDER, reel_name)
    
    if audio_duration > 0:
        print(f"Creating video with audio. Duration: {audio_duration}s, Images: {len(image_arrays)}")
        # Calculate how long each image should be displayed
        num_images = len(image_arrays)
        image_duration = audio_duration / num_images
        print(f"Each image will show for: {image_duration} seconds")
        
        # Create video clips for each image
        clips = []
        for i, img_array in enumerate(image_arrays):
            clip = ImageClip(img_array, duration=image_duration)
            clips.append(clip)
            print(f"Created clip {i+1}/{num_images}")
        
        # Concatenate all image clips and set FPS
        print("Concatenating video clips...")
        video_clip = concatenate_videoclips(clips, method="compose")
        video_clip = video_clip.with_fps(24)  # Set FPS for the video
        
        # Add audio to the video
        print("Adding audio to video...")
        audio_clip = AudioFileClip(audio_path)
        print(f"Audio clip duration: {audio_clip.duration}")
        final_clip = video_clip.with_audio(audio_clip)
        
        # Write the final video with audio
        print("Writing final video file...")
        final_clip.write_videofile(
            reel_path, 
            codec='libx264',
            audio_codec='aac',
            fps=24,
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            verbose=True,
            logger='bar'
        )
        
        # Close clips to free memory
        video_clip.close()
        audio_clip.close()
        final_clip.close()
        
        # Clean up temporary audio file
        if os.path.exists(audio_path):
            os.unlink(audio_path)
            print("Cleaned up temporary audio file")
    else:
        print("No audio - creating video without sound")
        # No audio - create video with images at 1 FPS (original behavior)
        clip = ImageSequenceClip(image_arrays, fps=1)
        clip.write_videofile(reel_path, codec='libx264')
        clip.close()
    
    # Save to database
    new_video = UserData(
        video_filename=reel_name,
        video_title=reel_title,
        user_id=user_id
    )
    db.session.add(new_video)
    db.session.commit()
    
    # Clean up uploaded files
    shutil.rmtree(user_upload_dir)
    
    flash("Reel generated successfully!", "success")
    return redirect(url_for("upload.home"))