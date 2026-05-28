"""routes/auth.py"""
import uuid
import bcrypt
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db
from models import User, log_event
from config import Config
from datetime import datetime, timezone

auth_bp = Blueprint("auth", __name__)


def _client_ip():
    return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()


@auth_bp.post("/register")
def register():
    data = request.get_json() or {}
    name     = data.get("name", "").strip()
    email    = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role     = data.get("role", "student")
    teacher_code = data.get("teacherCode", "")

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400

    if role not in ("student", "teacher", "admin"):
        return jsonify({"error": "Invalid role"}), 400

    if role == "teacher" and teacher_code != Config.TEACHER_REGISTRATION_CODE:
        return jsonify({"error": "Invalid teacher registration code"}), 403

    # Admin registration is restricted to existing admins (open in dev mode).
    if role == "admin" and not Config.ALLOW_ADMIN_SELF_REGISTER:
        return jsonify({"error": "Admin accounts are created by another administrator"}), 403

    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    user = User(
        id=str(uuid.uuid4()),
        name=name,
        email=email,
        password_hash=hashed,
        role=role,
    )
    db.session.add(user)
    log_event(user, "User registered", level="success", ip=_client_ip(), detail=f"Role: {role}")
    db.session.commit()

    token = create_access_token(identity=user.id)
    return jsonify({"user": user.to_dict(), "token": token}), 201


@auth_bp.post("/login")
def login():
    data  = request.get_json() or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        # Log failed attempt (no user reference)
        log_event(None, "Failed login attempt", level="warning", ip=_client_ip(), detail=f"Email: {email}")
        db.session.commit()
        return jsonify({"error": "Invalid email or password"}), 401

    if not user.is_active:
        log_event(user, "Login blocked (account deactivated)", level="warning", ip=_client_ip())
        db.session.commit()
        return jsonify({"error": "Account is deactivated"}), 403

    user.last_login = datetime.now(timezone.utc)
    log_event(user, "User login", level="info", ip=_client_ip())
    db.session.commit()

    token = create_access_token(identity=user.id)
    return jsonify({"user": user.to_dict(), "token": token}), 200


@auth_bp.get("/me")
@jwt_required()
def me():
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify(user.to_dict()), 200


@auth_bp.patch("/me")
@jwt_required()
def update_me():
    user = User.query.get(get_jwt_identity())
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json() or {}

    if "name" in data:
        user.name = data["name"].strip()
    if "avatar" in data:
        user.avatar = data["avatar"]
    if "preferences" in data:
        prefs = user.preferences
        prefs.update(data["preferences"])
        user.preferences = prefs

    log_event(user, "Profile updated", level="info", ip=_client_ip())
    db.session.commit()
    return jsonify(user.to_dict()), 200


@auth_bp.post("/change-password")
@jwt_required()
def change_password():
    user = User.query.get(get_jwt_identity())
    data = request.get_json() or {}
    old_pw = data.get("oldPassword", "")
    new_pw = data.get("newPassword", "")

    if not bcrypt.checkpw(old_pw.encode(), user.password_hash.encode()):
        return jsonify({"error": "Current password is incorrect"}), 400

    if len(new_pw) < 6:
        return jsonify({"error": "New password must be at least 6 characters"}), 400

    user.password_hash = bcrypt.hashpw(new_pw.encode(), bcrypt.gensalt()).decode()
    log_event(user, "Password changed", level="success", ip=_client_ip())
    db.session.commit()
    return jsonify({"message": "Password updated"}), 200
