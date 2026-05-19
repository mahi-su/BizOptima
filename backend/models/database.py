"""
BizOptima - Database Models (SQLAlchemy)
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


def init_db(app):
    """Initialize database and create all tables"""
    import os
    # Create database directory if using SQLite
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if 'sqlite' in db_uri:
        db_path = db_uri.replace('sqlite:///', '')
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    db.create_all()


class User(db.Model):
    """User accounts table"""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    business_name = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    # Relationship
    predictions = db.relationship('Prediction', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'business_name': self.business_name,
            'created_at': self.created_at.isoformat()
        }


class Prediction(db.Model):
    """Prediction history table"""
    __tablename__ = 'predictions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Input features
    revenue = db.Column(db.Float, nullable=False)
    expenses = db.Column(db.Float, nullable=False)
    marketing_spend = db.Column(db.Float, nullable=False)
    employee_count = db.Column(db.Integer, nullable=False)
    operational_cost = db.Column(db.Float, nullable=False)

    # ML Outputs
    predicted_profit = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.String(20), nullable=False)
    health_score = db.Column(db.Float, nullable=False)
    suggestions = db.Column(db.Text, nullable=True)   # JSON string

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    report_name = db.Column(db.String(200), nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'revenue': self.revenue,
            'expenses': self.expenses,
            'marketing_spend': self.marketing_spend,
            'employee_count': self.employee_count,
            'operational_cost': self.operational_cost,
            'predicted_profit': round(self.predicted_profit, 2),
            'risk_level': self.risk_level,
            'health_score': round(self.health_score, 1),
            'suggestions': json.loads(self.suggestions) if self.suggestions else [],
            'created_at': self.created_at.isoformat(),
            'report_name': self.report_name
        }


class Report(db.Model):
    """Generated reports table"""
    __tablename__ = 'reports'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    prediction_id = db.Column(db.Integer, db.ForeignKey('predictions.id'), nullable=True)
    report_type = db.Column(db.String(10), nullable=False)  # 'PDF' or 'CSV'
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'report_type': self.report_type,
            'filename': self.filename,
            'created_at': self.created_at.isoformat()
        }
