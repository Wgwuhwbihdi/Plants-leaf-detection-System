"""
Shared utilities for machine learning operations.
Provides common functions for model loading, feature extraction, and AI integrations.
"""

import os
import json
import logging
from typing import Optional, Dict, Any
import numpy as np
from flask import current_app, has_app_context

logger = logging.getLogger(__name__)


def _import_tf():
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise ImportError(
            "TensorFlow is required for ML operations. Install it before using MLService."
        ) from exc
    return tf


class MLService:
    """
    Encapsulates ML model and related resources to avoid global state.
    Use as a singleton or per-request instance.
    """

    def __init__(self):
        self.model = None
        self.plant_disease: Optional[Dict[str, Any]] = None
        self.gemini_client = None
        self._initialized = False

    def init_resources(
        self,
        model_path: Optional[str] = None,
        plant_disease_json_path: Optional[str] = None,
    ) -> None:
        """Lazy initialization of ML resources."""
        if self._initialized:
            return

        try:
            tf = _import_tf()
            if has_app_context():
                model_path = model_path or current_app.config["MODEL_PATH"]
                plant_disease_json_path = (
                    plant_disease_json_path or current_app.config["PLANT_DISEASE_JSON"]
                )
            else:
                if not model_path or not plant_disease_json_path:
                    raise ValueError(
                        "MLService.init_resources requires explicit model/json paths "
                        "when called outside Flask app context."
                    )

            self.model = tf.keras.models.load_model(model_path)
            logger.info("ML model loaded successfully.")

            with open(plant_disease_json_path, "r", encoding="utf-8") as file:
                self.plant_disease = json.load(file)
            logger.info("Plant disease data loaded successfully.")

            try:
                from google import genai
                self.gemini_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
                logger.info("Gemini client initialized.")
            except Exception as e:
                logger.warning(f"Gemini client initialization failed: {e}")
                self.gemini_client = None

            self._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize ML resources: {e}")
            raise

    def extract_features(self, image_path: str) -> np.ndarray:
        """
        Preprocesses the image for the neural network.

        Args:
            image_path: Path to the image file.

        Returns:
            Numpy array of features ready for model prediction.

        Raises:
            FileNotFoundError: If image file doesn't exist.
            ValueError: If image cannot be processed.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        try:
            tf = _import_tf()
            image = tf.keras.utils.load_img(image_path, target_size=(160, 160))
            feature = tf.keras.utils.img_to_array(image)
            return np.array([feature], dtype=np.float32)
        except Exception as e:
            logger.error(f"Failed to extract features from {image_path}: {e}")
            raise ValueError(f"Image processing failed: {e}") from e

    def gemini_vision_fallback(self, image_path: str) -> Optional[Dict[str, Any]]:
        """
        Uses Gemini AI for vision-based disease diagnosis as fallback.

        Args:
            image_path: Path to the image file.

        Returns:
            Dict with prediction details or None if failed.
        """
        if not self.gemini_client:
            return None

        try:
            import PIL.Image
            from app.models import Disease

            diseases = Disease.query.all()
            disease_names = [d.name for d in diseases]

            img = PIL.Image.open(image_path)
            prompt = (
                f"You are an expert plant pathologist. Analyze this image of a plant/leaf. "
                f"Re-diagnose the disease. You must classify it as one of the following exact "
                f"disease names from our database: {', '.join(disease_names)}. "
                "Return ONLY a valid JSON object with exactly three keys: 'name' (the exact matched "
                "disease name from the list), 'cause' (a 2-3 sentence scientific explanation), "
                "and 'cure' (actionable treatment). If the image is absolutely not a plant or blank, "
                "return name='Background_without_leaves'."
            )

            try:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash", contents=[prompt, img]
                )
            except Exception as e:
                logger.warning(f"Gemini 2.5-flash failed ({e}), falling back to 1.5-flash")
                response = self.gemini_client.models.generate_content(
                    model="gemini-1.5-flash", contents=[prompt, img]
                )

            text = response.text.strip()
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)

            data = json.loads(text)
            return {
                "name": data.get("name", "Unknown Disease"),
                "cause": data.get("cause", "Detailed analysis required."),
                "cure": data.get("cure", "Seek expert advice."),
                "confidence": "99.9%",
                "confidence_value": 0.999,
                "confidence_level": "high",
                "uncertain": False,
                "is_gemini": True,
            }
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from Gemini: {e}")
            return None
        except Exception as e:
            logger.error(f"Gemini vision fallback failed: {e}")
            return None

    def gemini_enrich_encyclopedia(self, disease_name: str) -> Optional[Dict[str, Any]]:
        """
        Enriches disease encyclopedia using Gemini AI.

        Args:
            disease_name: Name of the disease to enrich.

        Returns:
            Dict with cause and cure or None if failed.
        """
        if not self.gemini_client or "healthy" in disease_name.lower() or "background" in disease_name.lower():
            return None

        try:
            prompt = (
                f"You are an expert plant pathologist. Provide a highly detailed scientific analysis "
                f"of the plant disease: '{disease_name}'. Return ONLY a valid JSON object with exactly "
                "two keys: 'cause' (a detailed 2-3 sentence paragraph explaining the pathogen, "
                "transmission, and environmental triggers) and 'cure' (a detailed 2-3 sentence paragraph "
                "providing actionable treatments, fungicides, or cultural controls). Do NOT wrap the "
                "JSON in markdown blocks, just return raw JSON."
            )

            try:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash", contents=[prompt]
                )
            except Exception as e:
                response = self.gemini_client.models.generate_content(
                    model="gemini-1.5-flash", contents=[prompt]
                )

            text = response.text.strip()
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)

            data = json.loads(text)
            return {
                "cause": data.get("cause", ""),
                "cure": data.get("cure", "")
            }
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from Gemini enrichment: {e}")
            return None
        except Exception as e:
            logger.error(f"Gemini encyclopedia enrichment failed: {e}")
            return None

    def predict_disease(self, image_path: str, thresholds: Dict[str, float], cache_redis=None) -> Dict[str, Any]:
        """
        Predicts plant disease from image.

        Args:
            image_path: Path to the image.
            thresholds: Confidence thresholds dict.
            cache_redis: Optional Redis client for caching.

        Returns:
            Dict with prediction details.
        """
        self.init_resources()

        # Caching logic
        img_hash = None
        if cache_redis:
            import hashlib
            with open(image_path, "rb") as f:
                img_bytes = f.read()
            img_hash = hashlib.md5(img_bytes).hexdigest()
            try:
                cached = cache_redis.get(img_hash)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

        features = self.extract_features(image_path)
        prediction = self.model.predict(features, verbose=0)
        class_index = int(np.argmax(prediction, axis=1)[0])
        confidence = float(np.max(prediction, axis=1)[0])
        disease = self.plant_disease[class_index]

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

        # Cache result
        if cache_redis and img_hash:
            try:
                cache_redis.setex(img_hash, 86400, json.dumps(result))
            except Exception as e:
                logger.warning(f"Redis cache error: {e}")

        return result


# Global instance for backward compatibility (but prefer per-request)
_ml_service = MLService()


def get_ml_service() -> MLService:
    """Get the global ML service instance."""
    return _ml_service
