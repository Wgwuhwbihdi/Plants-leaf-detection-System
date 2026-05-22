import json
from app.utils import allowed_file, load_settings


def test_allowed_file_accepts_valid_png_bytes(app):
    valid_png = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    with app.app_context():
        assert allowed_file("test.png", valid_png) is True


def test_allowed_file_rejects_invalid_data(app):
    invalid_bytes = b"not-an-image"
    with app.app_context():
        assert allowed_file("test.png", invalid_bytes) is False


def test_load_settings_uses_config_defaults(app):
    with app.app_context():
        settings = load_settings()
        assert isinstance(settings, dict)
        assert settings["confidence_thresholds"]["high"] == app.config.get("CONFIDENCE_HIGH", 0.8)
        assert settings["confidence_thresholds"]["medium"] == app.config.get("CONFIDENCE_MEDIUM", 0.6)
        assert settings["confidence_thresholds"]["low"] == app.config.get("CONFIDENCE_LOW", 0.4)
        assert settings["require_expert_review"] is True
