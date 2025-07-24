from flask import Flask,render_template,request,session,redirect,url_for,Blueprint,flash
from app.routes import auth
from app import db
from models import User

upload_bp=Blueprint("upload",__name__)


@upload_bp.route("/home")
def home():
    return render_template("upload.html")

@upload_bp.route("/generate_reel",methods=["POST"])
def generate_reel():
    uploaded_files = request.files.getlist("images[]")
    user_id = session.get('user_id')

    if not user_id:
        flash("Please login","danger")
        redirect(url_for("auth.login"))

    pass