from flask import Blueprint, render_template, session, redirect, url_for, flash
from app.models import UserData  # Make sure this is imported correctly
from app import db

gallery_bp = Blueprint("gallery", __name__)

@gallery_bp.route("/gallery")
def gallery():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to view your gallery.", "warning")
        return redirect(url_for("auth.login"))

    # Fetch all reels for the current user
    user_reels = UserData.query.filter_by(user_id=user_id).order_by(UserData.upload_time.desc()).all()
    return render_template("gallery.html", reels=user_reels)
