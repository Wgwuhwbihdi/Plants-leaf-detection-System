import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # SECRET_KEY must be a persistent environment variable in production.
    # We provide a random fallback ONLY for quick local dev, but warn loudly if missing in prod.
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY") or os.urandom(24)

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///data.sqlite")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Uploads
    UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "uploadimages"
    )
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

    # Storage (Cloudinary)
    CLOUD_STORAGE_ENABLED = os.environ.get(
        "CLOUD_STORAGE_ENABLED", "False"
    ).lower() in ("true", "1", "t")
    CLOUD_NAME = os.environ.get("CLOUD_NAME", "")
    CLOUD_API_KEY = os.environ.get("CLOUD_API_KEY", "")
    CLOUD_API_SECRET = os.environ.get("CLOUD_API_SECRET", "")

    # Redis (For Celery & Rate Limiting)
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/1")
    CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
    CELERY_RESULT_BACKEND = os.environ.get(
        "CELERY_RESULT_BACKEND", "redis://localhost:6379/0"
    )

    # AI models
    ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
    MODEL_PATH = os.environ.get(
        "MODEL_PATH",
        os.path.join(ASSETS_DIR, "models", "plant_disease_recog_model_pwp.keras"),
    )
    PLANT_DISEASE_JSON = os.environ.get(
        "PLANT_DISEASE_JSON", os.path.join(ASSETS_DIR, "plant_disease.json")
    )

    # Confidence thresholds (configurable via env)
    CONFIDENCE_HIGH = float(os.environ.get("CONFIDENCE_HIGH", "0.8"))
    CONFIDENCE_MEDIUM = float(os.environ.get("CONFIDENCE_MEDIUM", "0.6"))
    CONFIDENCE_LOW = float(os.environ.get("CONFIDENCE_LOW", "0.4"))
