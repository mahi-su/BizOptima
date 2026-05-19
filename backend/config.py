"""
BizOptima - Configuration Settings
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'bizoptima-super-secret-key-2024-change-in-production')
    DEBUG = os.environ.get('DEBUG', 'True') == 'True'

    # Database - SQLite by default, PostgreSQL if DATABASE_URL is set
    DATABASE_URL = os.environ.get('DATABASE_URL', '')
    if DATABASE_URL and DATABASE_URL.startswith('postgresql'):
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    else:
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'database', 'bizoptima.db')}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
    }

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'bizoptima-jwt-secret-key-2026-local-development')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # ML Model paths
    ML_DIR = os.path.join(BASE_DIR, 'ml')
    MODEL_PATH = os.path.join(ML_DIR, 'saved_model.pkl')
    SCALER_PATH = os.path.join(ML_DIR, 'scaler.pkl')

    # Export paths
    EXPORT_DIR = os.path.join(BASE_DIR, 'exports')
    os.makedirs(EXPORT_DIR, exist_ok=True)
