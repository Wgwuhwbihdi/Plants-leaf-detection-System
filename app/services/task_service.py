import os
from pathlib import Path
from celery import Celery
from dotenv import load_dotenv
from typing import List, Dict, Any

import numpy as np
from .ml_utils import MLService

load_dotenv()

# Initialize Celery
redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
celery = Celery(__name__, broker=redis_url, backend=redis_url)

# Per-worker ML service instance
ml_service = MLService()


def init_worker() -> None:
    """Initialize ML resources for the worker."""
    app_dir = Path(__file__).resolve().parents[1]
    default_model_path = app_dir / "assets" / "models" / "plant_disease_recog_model_pwp.keras"
    default_disease_json = app_dir / "assets" / "plant_disease.json"
    model_path = os.environ.get("MODEL_PATH", str(default_model_path))
    disease_json_path = os.environ.get("PLANT_DISEASE_JSON", str(default_disease_json))
    ml_service.init_resources(
        model_path=model_path,
        plant_disease_json_path=disease_json_path,
    )


@celery.task(name="tasks.process_batch")
def process_batch(image_paths: List[str], thresholds: Dict[str, float]) -> List[Dict[str, Any]]:
    """
    Process a batch of images for disease prediction.

    Args:
        image_paths: List of paths to image files.
        thresholds: Confidence thresholds dict.

    Returns:
        List of prediction dictionaries.
    """
    init_worker()

    predictions: List[Dict[str, Any]] = []
    for image_path in image_paths:
        try:
            features = ml_service.extract_features(image_path)
            prediction = ml_service.model.predict(features, verbose=0)
            class_index = int(np.argmax(prediction, axis=1)[0])
            confidence = float(np.max(prediction, axis=1)[0])
            disease = ml_service.plant_disease[class_index]

            if confidence >= thresholds.get("high", 0.8):
                confidence_level = "high"
                uncertain = False
            elif confidence >= thresholds.get("medium", 0.6):
                confidence_level = "medium"
                uncertain = False
            elif confidence >= thresholds.get("low", 0.4):
                confidence_level = "low"
                uncertain = False
            else:
                confidence_level = "uncertain"
                uncertain = True

            result = {
                "name": disease.get("name", "Unknown disease"),
                "cause": disease.get("cause", "No cause information available."),
                "cure": disease.get("cure", "No cure information available."),
                "confidence": f"{confidence * 100:.1f}%",
                "confidence_value": confidence,
                "confidence_level": confidence_level,
                "uncertain": uncertain,
            }
            predictions.append(result)
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
            predictions.append({
                "name": "Processing Error",
                "cause": "Failed to analyze image.",
                "cure": "Please try again.",
                "confidence": "0.0%",
                "confidence_value": 0.0,
                "confidence_level": "uncertain",
                "uncertain": True,
            })

    return predictions
