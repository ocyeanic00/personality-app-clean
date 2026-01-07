# backend/routes/auth.py
from __future__ import annotations
import os
from datetime import datetime

from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from authlib.integrations.flask_client import OAuth
from database.db import db
from models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# =========================
# GOOGLE OAUTH CONFIG
# =========================
oauth = OAuth()
google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v2/",
    client_kwargs={"scope": "email profile"},
)


# =========================
# GOOGLE LOGIN (REDIRECT)
# =========================
@auth_bp.get("/google/login")
def google_login():
    redirect_uri = os.getenv("GOOGLE_REDIRECT_URI")
    return google.authorize_redirect(redirect_uri) # type: ignore


# =========================
# GOOGLE CALLBACK
# =========================
@auth_bp.get("/google/callback")
def google_callback():
    token = google.authorize_access_token() # type: ignore
    userinfo = google.get("userinfo").json() # type: ignore

    email = userinfo["email"]
    first_name = userinfo.get("given_name", "")
    last_name = userinfo.get("family_name", "")

    user = User.query.filter_by(email=email).first()

    # create user if not exists
    if not user:
        user = User(
            first_name=first_name, # type: ignore
            last_name=last_name, # type: ignore
            email=email, # type: ignore
        )
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=user.id)

    return jsonify({
        "access_token": access_token,
        "user": user.to_dict()
    }), 200


# =========================
# REGISTER
# =========================
@auth_bp.post("/register")
def register():
    data = request.get_json() or {}

    first_name = (data.get("first_name") or "").strip()
    last_name = (data.get("last_name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    birthday_str = data.get("birthday")

    if not all([first_name, last_name, email, password]):
        return jsonify({"error": "Missing required fields"}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered."}), 409

    user = User(
        first_name=first_name, # type: ignore
        last_name=last_name, # type: ignore
        email=email, # type: ignore
    )

    if birthday_str:
        parsed = None
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y"):
            try:
                parsed = datetime.strptime(birthday_str, fmt).date()
                break
            except ValueError:
                continue

        if parsed is None:
            try:
                from dateutil.parser import parse as dateparse
                parsed = dateparse(birthday_str).date()
            except Exception:
                return jsonify({"error": "Invalid birthday format"}), 400

        user.birthday = parsed

    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({"user": user.to_dict()}), 201


# =========================
# PASSWORD LOGIN
# =========================
@auth_bp.post("/login")
def login():
    data = request.get_json() or {}

    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"error": "Missing email or password"}), 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return jsonify({"error": "Invalid email or password"}), 401

    access_token = create_access_token(identity=user.id)

    return jsonify({
        "access_token": access_token,
        "user": user.to_dict()
    }), 200
