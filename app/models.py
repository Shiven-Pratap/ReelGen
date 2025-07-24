from app import db
from flask_sqlalchemy import SQLAlchemy


class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    name=db.Column(db.String(25),nullable=False)
    email=db.Column(db.String(25),nullable=False,unique=True)
    password=db.Column(db.String(25),nullable=False)

    items = db.relationship('UserData', backref='owner', lazy=True)

class UserData(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    video_filename = db.Column(db.String(100), nullable=False)
    video_title = db.Column(db.String(100), nullable=False)
    upload_time = db.Column(db.DateTime, nullable=False, default=db.func.now())

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


