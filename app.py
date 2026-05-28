"""
app.py — Main Flask application entry point
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from extensions import db
from config import Config

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Extensions
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    db.init_app(app)
    JWTManager(app)

    # Register blueprints
    from routes.auth       import auth_bp
    from routes.assessment import assessment_bp
    from routes.results    import results_bp
    from routes.recommendations import recommendations_bp
    from routes.users      import users_bp
    from routes.admin      import admin_bp
    from routes.teacher    import teacher_bp
    from routes.notifications import notifications_bp

    app.register_blueprint(auth_bp,            url_prefix="/api/auth")
    app.register_blueprint(assessment_bp,      url_prefix="/api/assessment")
    app.register_blueprint(results_bp,         url_prefix="/api/results")
    app.register_blueprint(recommendations_bp, url_prefix="/api/recommendations")
    app.register_blueprint(users_bp,           url_prefix="/api/users")
    app.register_blueprint(admin_bp,           url_prefix="/api/admin")
    app.register_blueprint(teacher_bp,         url_prefix="/api/teacher")
    app.register_blueprint(notifications_bp,   url_prefix="/api/notifications")

    # Create tables
    with app.app_context():
        db.create_all()
        from utils.seed import seed_if_empty
        seed_if_empty()

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
