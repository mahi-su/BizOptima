"""
BizOptima - Main Flask Application Entry Point
"""

import os
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import Config
from models.database import db, init_db
from routes.auth import auth_bp
from routes.predictions import predictions_bp
from routes.exports import exports_bp


def create_app(config_class=Config):
    """Application factory pattern"""
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), '../frontend/templates'),
        static_folder=os.path.join(os.path.dirname(__file__), '../frontend/static')
    )

    # Load config
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    JWTManager(app)
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(predictions_bp, url_prefix='/api/predictions')
    app.register_blueprint(exports_bp, url_prefix='/api/exports')

    # Create tables
    with app.app_context():
        init_db(app)

    # Serve frontend pages
    from flask import render_template

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login')
    def login_page():
        return render_template('login.html')

    @app.route('/register')
    def register_page():
        return render_template('register.html')

    @app.route('/dashboard')
    def dashboard_page():
        return render_template('dashboard.html')

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Resource not found"}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {"error": "Internal server error"}, 500

    return app


if __name__ == '__main__':
    app = create_app()
    print("=" * 50)
    print("  BizOptima Server Starting...")
    print("  Visit: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)
