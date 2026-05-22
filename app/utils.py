import json
import filetype
from typing import Optional, Dict, Any, Tuple
from flask import current_app
from app.models import db, AppSetting


def allowed_file(filename: str, stream_bytes: Optional[bytes] = None) -> bool:
    """
    Check if the uploaded file is allowed based on extension and content.

    Args:
        filename: The name of the file.
        stream_bytes: Optional bytes from the file stream for content validation.

    Returns:
        True if file is allowed, False otherwise.
    """
    if (
        "." not in filename
        or filename.rsplit(".", 1)[1].lower()
        not in current_app.config["ALLOWED_EXTENSIONS"]
    ):
        return False
    if stream_bytes:
        res = filetype.guess(stream_bytes)
        if res is None or res.extension not in current_app.config["ALLOWED_EXTENSIONS"]:
            return False
    return True


def load_settings() -> Dict[str, Any]:
    """
    Load application settings from database, with config defaults as fallback.

    Returns:
        Dict containing settings like confidence thresholds.
    """
    s = AppSetting.query.get("global")
    if s:
        try:
            return json.loads(s.value)
        except:
            pass
    # Use config defaults if no settings saved
    from flask import current_app
    return {
        "confidence_thresholds": {
            "high": current_app.config.get("CONFIDENCE_HIGH", 0.8),
            "medium": current_app.config.get("CONFIDENCE_MEDIUM", 0.6),
            "low": current_app.config.get("CONFIDENCE_LOW", 0.4)
        },
        "require_expert_review": True,
    }


def save_settings(settings: Dict[str, Any]) -> None:
    """
    Save application settings to database.

    Args:
        settings: Dict of settings to save.
    """
    s = AppSetting.query.get("global")
    if not s:
        s = AppSetting(key="global")
    s.value = json.dumps(settings)
    db.session.add(s)
    db.session.commit()
