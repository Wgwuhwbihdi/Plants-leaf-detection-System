import os
import json
import logging
import hashlib
from typing import Optional, Dict, Any
from flask import current_app

from .ml_utils import get_ml_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Legacy globals for backward compatibility (deprecated)
model = None
plant_disease = None
gemini_client = None


def init_ml() -> None:
    """
    Legacy initialization function.
    Deprecated: Use get_ml_service().init_resources() instead.
    """
    global model, plant_disease, gemini_client
    ml_service = get_ml_service()
    ml_service.init_resources()
    model = ml_service.model
    plant_disease = ml_service.plant_disease
    gemini_client = ml_service.gemini_client


def extract_features(image_path: str) -> Any:
    """
    Legacy wrapper for feature extraction.
    Deprecated: Use get_ml_service().extract_features() instead.
    """
    return get_ml_service().extract_features(image_path)


def gemini_vision_fallback(image_path: str) -> Optional[Dict[str, Any]]:
    """
    Legacy wrapper for Gemini vision fallback.
    Deprecated: Use get_ml_service().gemini_vision_fallback() instead.
    """
    return get_ml_service().gemini_vision_fallback(image_path)


def gemini_enrich_encyclopedia(disease_name: str) -> Optional[Dict[str, Any]]:
    """
    Legacy wrapper for encyclopedia enrichment.
    Deprecated: Use get_ml_service().gemini_enrich_encyclopedia() instead.
    """
    return get_ml_service().gemini_enrich_encyclopedia(disease_name)


def model_predict(image_path: str, cache_redis=None, thresholds: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """
    Predicts plant disease from image using the ML service.

    Args:
        image_path: Path to the image file.
        cache_redis: Optional Redis client for caching.
        thresholds: Confidence thresholds (defaults loaded from settings).

    Returns:
        Dict with prediction details.
    """
    if thresholds is None:
        from app.utils import load_settings
        thresholds = load_settings().get("confidence_thresholds", {"high": 0.8, "medium": 0.6, "low": 0.4})

    return get_ml_service().predict_disease(image_path, thresholds, cache_redis)
