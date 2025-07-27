from werkzeug.utils import secure_filename
from app.models import User, UserData
import os
from datetime import datetime
import shutil
from moviepy import *
from PIL import Image
import numpy as np
from flask import Flask, Blueprint, render_template, request, redirect, flash, url_for, session
from app import db
import requests
import tempfile
from sarvamai import SarvamAI
from sarvamai.play import save

upload_bp = Blueprint("upload", __name__)

UPLOAD_FOLDER = 'app/static/uploads'
REEL_FOLDER = 'app/static/reels'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


USE_GOOGLE_TTS = True

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REEL_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_audio_from_text(text, output_path):

    if not text or not text.strip():
        print("No text provided for audio generation")
        return None
    
    print(f"Generating audio for text: {text[:50]}...")
    
    client = SarvamAI(
    api_subscription_key=os.getenv("SARVAM_API_KEY"),
    )

    try:
        audio = client.text_to_speech.convert(
            target_language_code="en-IN", 
            text=text.strip(),
            model="bulbul:v2",
            speaker="anushka"
        )
        save(audio, output_path)
        print(f"Audio saved to {output_path}")
        return output_path

    except Exception as e:
        print(f"Sarvam TTS failed: {e}")
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
    target_size = (720, 1280)  
    target_aspect_ratio = target_size[0] / target_size[1] 
    
    def smart_resize_image(img, target_size):
        original_width, original_height = img.size
        original_aspect_ratio = original_width / original_height
        target_width, target_height = target_size
        target_aspect_ratio = target_width / target_height
        
        if original_aspect_ratio > target_aspect_ratio:
            # Image is wider than target - use full width, crop height
            # Scale based on width to use the entire width
            scale_factor = target_width / original_width
            new_width = target_width
            new_height = int(original_height * scale_factor)
            
            # Resize to new dimensions
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # If the scaled height is greater than target, crop from center
            if new_height > target_height:
                top = (new_height - target_height) // 2
                bottom = top + target_height
                img_cropped = img_resized.crop((0, top, new_width, bottom))
                return img_cropped
            else:
                # If scaled height is less than target, add padding
                result = Image.new('RGB', target_size, (0, 0, 0))
                y_offset = (target_height - new_height) // 2
                result.paste(img_resized, (0, y_offset))
                return result
                
        elif original_aspect_ratio < target_aspect_ratio:
            # Image is taller than target - use full height, crop width
            # Scale based on height to use the entire height
            scale_factor = target_height / original_height
            new_width = int(original_width * scale_factor)
            new_height = target_height
            
            # Resize to new dimensions
            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # If the scaled width is greater than target, crop from center
            if new_width > target_width:
                left = (new_width - target_width) // 2
                right = left + target_width
                img_cropped = img_resized.crop((left, 0, right, new_height))
                return img_cropped
            else:
                # If scaled width is less than target, add padding
                result = Image.new('RGB', target_size, (0, 0, 0))
                x_offset = (target_width - new_width) // 2
                result.paste(img_resized, (x_offset, 0))
                return result
        else:
            # Perfect aspect ratio match - just resize
            return img.resize(target_size, Image.Resampling.LANCZOS)
    
    
    for file in uploaded_files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(user_upload_dir, filename)
            file.save(save_path)
            
            img = Image.open(save_path).convert("RGB")
            
            processed_img = smart_resize_image(img, target_size)
            
            
            image_arrays.append(np.array(processed_img))
    
    if not image_arrays:
        flash("No valid images uploaded.", "danger")
        return redirect(url_for("upload.home"))
    
    audio_path = None
    audio_duration = 0
    
    print(f"Audio text received: '{audio_text}'")
    
    if audio_text and audio_text.strip():
        print("Creating temporary audio file...")
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        audio_path = generate_audio_from_text(audio_text, temp_audio.name)
        temp_audio.close()
        
        if audio_path and os.path.exists(audio_path):
            print(f"Audio file created: {audio_path}")
            print(f"Audio file size: {os.path.getsize(audio_path)} bytes")
            
            try:
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
    
    reel_name = f"reel_{str(datetime.utcnow().timestamp()).replace('.', '_')}.mp4"
    reel_path = os.path.join(REEL_FOLDER, reel_name)
    
    if audio_duration > 0:
        print(f"Creating video with audio. Duration: {audio_duration}s, Images: {len(image_arrays)}")

        num_images = len(image_arrays)
        total_frames_needed = int(audio_duration)  
        
        looped_images = []
        for frame_index in range(total_frames_needed):
            image_index = frame_index % num_images 
            looped_images.append(image_arrays[image_index])
        
        print(f"Total frames needed: {total_frames_needed}")
        print(f"Images will loop {total_frames_needed // num_images} times with {total_frames_needed % num_images} extra frames")
        
        video_clip = ImageSequenceClip(looped_images, fps=1)
        
        video_clip = video_clip.with_duration(audio_duration)
        
        print("Adding audio to video...")
        audio_clip = AudioFileClip(audio_path)
        print(f"Audio clip duration: {audio_clip.duration}")
        final_clip = video_clip.with_audio(audio_clip)
        
        print("Writing final video file...")
        final_clip.write_videofile(
            reel_path, 
            codec='libx264',
            audio_codec='aac',
            fps=1
        )
        
        video_clip.close()
        audio_clip.close()
        final_clip.close()
        
        if os.path.exists(audio_path):
            os.unlink(audio_path)
            print("Cleaned up temporary audio file")
    else:
        print("No audio - creating video without sound")
        clip = ImageSequenceClip(image_arrays, fps=1)
        clip.write_videofile(reel_path, codec='libx264')
        clip.close()
    
    new_video = UserData(
        video_filename=reel_name,
        video_title=reel_title,
        user_id=user_id
    )
    db.session.add(new_video)
    db.session.commit()
    
    shutil.rmtree(user_upload_dir)
    
    flash("Reel generated successfully!", "success")
    return redirect(url_for("upload.home"))