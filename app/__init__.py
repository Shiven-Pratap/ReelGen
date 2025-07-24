from flask import Flask
from flask_sqlalchemy import SQLAlchemy


db=SQLAlchemy()

def create_app():
    app=Flask(__name__)
    app.config["SECRET_KEY"]='very-secret-key'
    app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///ReelGenerator.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

    db.__init__(app)

    from app.routes.auth import auth_bp
    from app.routes.gallery import gallery_bp
    from app.routes.upload import upload_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(gallery_bp)
    app.register_blueprint(upload_bp)

    return app