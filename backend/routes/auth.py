"""
BizOptima - Authentication Routes
Handles user registration, login, logout, token refresh, and profile data.
"""

import re
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import db, User

auth_bp = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value):
    return (value or "").strip().lower()


def normalize_username(value):
    return (value or "").strip()


def token_response(user, message, status_code):
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))
    return jsonify({
        "message": message,
        "access_token": access_token,
        "refresh_token": refresh_token,
        "user": user.to_dict(),
    }), status_code


@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new user account."""
    try:
        data = request.get_json(silent=True) or {}
        username = normalize_username(data.get("username"))
        email = normalize_email(data.get("email"))
        password = data.get("password") or ""
        business_name = (data.get("business_name") or "").strip()

        if not username or not email or not password:
            return jsonify({"error": "Username, email, and password are required"}), 400
        if len(username) < 3:
            return jsonify({"error": "Username must be at least 3 characters"}), 400
        if not EMAIL_RE.match(email):
            return jsonify({"error": "Enter a valid email address"}), 400
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({"error": "Email already registered"}), 409
        if User.query.filter_by(username=username).first():
            return jsonify({"error": "Username already taken"}), 409

        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            business_name=business_name[:200],
        )
        db.session.add(new_user)
        db.session.commit()

        return token_response(new_user, "Registration successful", 201)

    except Exception:
        db.session.rollback()
        return jsonify({"error": "Registration failed. Please try again."}), 500


@auth_bp.route("/login", methods=["POST"])
def login():
    """Login with email and password."""
    try:
        data = request.get_json(silent=True) or {}
        email = normalize_email(data.get("email"))
        password = data.get("password") or ""

        if not email or not password:
            return jsonify({"error": "Email and password are required"}), 400

        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({"error": "Invalid email or password"}), 401
        if not user.is_active:
            return jsonify({"error": "Account is deactivated"}), 403

        return token_response(user, "Login successful", 200)

    except Exception:
        return jsonify({"error": "Login failed. Please try again."}), 500


@auth_bp.route("/profile", methods=["GET"])
@jwt_required()
def get_profile():
    """Get the current user's profile and account stats."""
    try:
        user_id = int(get_jwt_identity())
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404

        total_predictions = len(user.predictions)
        avg_health = 0
        if total_predictions:
            avg_health = sum(p.health_score for p in user.predictions) / total_predictions

        return jsonify({
            "user": user.to_dict(),
            "stats": {
                "total_predictions": total_predictions,
                "avg_health_score": round(avg_health, 1),
            },
        }), 200

    except Exception:
        return jsonify({"error": "Unable to load profile"}), 500


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh an access token."""
    user_id = get_jwt_identity()
    new_token = create_access_token(identity=user_id)
    return jsonify({"access_token": new_token}), 200


@auth_bp.route("/logout", methods=["POST"])
@jwt_required()
def logout_route():
    """Client-side logout endpoint for API completeness."""
    return jsonify({"message": "Logged out"}), 200
