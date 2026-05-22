from flask import Flask, render_template
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from redis import Redis
import os
import logging
import sys
from typing import Optional

from .config import Config
from .models import db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log', mode='a')  # Optional: log to file
    ]
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)
cache_redis: Optional[Redis] = None


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Init DB
    db.init_app(app)

    # Init extensions
    global cache_redis
    try:
        temp_redis = Redis.from_url(app.config["REDIS_URL"])
        temp_redis.ping()
        cache_redis = temp_redis
        app.config["RATELIMIT_STORAGE_URI"] = app.config["REDIS_URL"]
    except Exception as e:
        logger.warning(
            f"[*] Redis unavailable: {e}. Running without Redis cache and falling back to memory rate limiting."
        )
        cache_redis = None
        app.config["RATELIMIT_STORAGE_URI"] = "memory://"

    limiter.init_app(app)

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template("500.html"), 500

    @app.errorhandler(413)
    def too_large_error(error):
        return "Payload Too Large. Max size is 16MB.", 413

    # Inject variables for templates (Translations)
    from .services.translation_service import (
        get_locale,
        translate,
        LANGUAGES,
        LANGUAGE_ORDER,
    )

    @app.context_processor
    def inject_global_variables():
        return {
            "current_language": get_locale(),
            "available_languages": LANGUAGES,
            "language_order": [code for code in LANGUAGE_ORDER if code in LANGUAGES],
            "t": translate,
        }

    # Security: Enforce HTTPS & secure headers in production
    # CSP is complex for dynamic apps (CDN tailwind), so we relax it slightly for this app
    # but keep HTTPS enforcement. We only enforce HTTPS if not in debug.
    from flask_talisman import Talisman

    Talisman(app, content_security_policy=None, force_https=not app.debug)

    # Auth: Flask-Login setup
    from flask_login import LoginManager
    from .models import User

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register blueprints safely
    with app.app_context():
        from .controllers.main_controller import main_bp
        from .controllers.upload_controller import upload_bp
        from .controllers.batch_controller import batch_bp
        from .controllers.history_controller import history_bp
        from .controllers.settings_controller import settings_bp
        from .controllers.auth_controller import auth_bp

        app.register_blueprint(main_bp)
        app.register_blueprint(upload_bp)
        app.register_blueprint(batch_bp)
        app.register_blueprint(history_bp)
        app.register_blueprint(settings_bp)
        app.register_blueprint(auth_bp)

        # Ensure upload folder exists early on
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        db.create_all()

    return app
