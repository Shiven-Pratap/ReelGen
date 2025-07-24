from flask import Flask,render_template,request,session,redirect,url_for,Blueprint,flash
import re
from app import db
from models import User
from app.routes import upload

auth_bp=Blueprint('auth',__name__)


@auth_bp.route("/register",methods=["GET","POST"])
def register():
    if request.method=='POST':
        username=request.form.get('username')
        password=request.form.get('password')
        email=request.form.get('email')

        if not username or not email or not password:
            flash("All feilds are required","danger")
            return redirect(url_for("auth.register"))
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            flash("Invalid email format.", "danger")
            return redirect(url_for("auth.register"))
        
        existing_user=User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered", "danger")
            return redirect(url_for("auth.register"))
        
        if len(password)<6:
            flash("Password must be atleast 6 characters.","danger")
            return redirect(url_for("auth.register"))
        
        new_user=User(name=username,email=email,password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration Successfull.",'success')
        return redirect(url_for("auth.login"))
    return render_template("register.html")
    
    
@auth_bp.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get('email')
        password=request.form.get('password')

        if not email or not password:
            flash("All feilds are required","danger")
            return redirect(url_for("auth.login"))
        
        user=User.query.filter_by(email=email).first()
        if not user:
            flash("Invalid email or password", "danger")
            return redirect(url_for("auth.login"))
        
        if password != user.password:
            flash("Invalid email or password", "danger")
            return redirect(url_for("auth.login"))
        
        session['user_id']=user.id
        session['username']=user.name
        flash("Login successful!", "success")
        return redirect("upload.home")

@auth_bp.route("/logout",methods=["POST"])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for("auth.login"))



    

    




        

