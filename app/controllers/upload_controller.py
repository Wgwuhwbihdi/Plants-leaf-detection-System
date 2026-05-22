import os
import uuid
import json
import random
from datetime import datetime
from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    flash,
    current_app,
    render_template,
    send_from_directory,
)
from werkzeug.utils import secure_filename
import cloudinary
import cloudinary.uploader
from flask_login import login_required, current_user

from app import limiter
from app.models import db, History
from app.utils import allowed_file, load_settings
from app.services import ml_service

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/uploadimages/<path:filename>")
def uploaded_images(filename):
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)


@upload_bp.route("/upload/", methods=["POST"])
@login_required
@limiter.limit("20 per minute")
def uploadimage():
    from app import cache_redis

    if "img" not in request.files:
        flash("No file part found in the request.")
        return redirect(url_for("main.home"))

    image = request.files["img"]
    if image.filename == "":
        flash("No image selected. Please choose a file to upload.")
        return redirect(url_for("main.home"))

    stream_bytes = image.read()
    image.seek(0)
    if not allowed_file(image.filename, stream_bytes):
        flash(
            "Unsupported or malicious file type detected. Please upload valid PNG, JPG, JPEG, or GIF."
        )
        return redirect(url_for("main.home"))

    filename = secure_filename(image.filename)
    unique_filename = f"temp_{uuid.uuid4().hex}_{filename}"
    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
    image.save(save_path)

    active_settings = load_settings()
    prediction = ml_service.model_predict(
        save_path, cache_redis, active_settings["confidence_thresholds"]
    )

    if ml_service.gemini_client and (
        prediction.get("uncertain")
        or prediction.get("name") == "Background_without_leaves"
        or prediction.get("confidence_value", 1.0) < 0.6
    ):
        fallback_pred = ml_service.gemini_vision_fallback(save_path)
        if fallback_pred:
            prediction = fallback_pred
        else:
            flash("AI Diagnostics temporarily unavailable due to high server demand. Falling back to base model.", "error")

    # ENRICH WITH MASTER DATABASE
    from app.models import Disease
    disease_record = Disease.query.filter_by(name=prediction.get("name")).first()
    if disease_record:
        # ML -> AI -> Encyclopedia Auto-Enrichment
        if not disease_record.cause or len(disease_record.cause) < 30 or "No cause information" in disease_record.cause:
            if prediction.get("is_gemini") and prediction.get("cause"):
                disease_record.cause = prediction.get("cause")
                disease_record.cure = prediction.get("cure")
                db.session.commit()
            else:
                ai_enrichment = ml_service.gemini_enrich_encyclopedia(disease_record.name)
                if ai_enrichment and ai_enrichment.get("cause"):
                    disease_record.cause = ai_enrichment.get("cause")
                    disease_record.cure = ai_enrichment.get("cure")
                    db.session.commit()
                    
        prediction["cause"] = disease_record.cause
        prediction["cure"] = disease_record.cure
        prediction["pathogen_type"] = disease_record.pathogen_type
        prediction["db_image_url"] = disease_record.image_url

    if current_app.config["CLOUD_STORAGE_ENABLED"]:
        try:
            cloud_res = cloudinary.uploader.upload(save_path, folder="phyto lab_scans")
            image_url = cloud_res.get("secure_url")
            if os.path.exists(save_path):
                os.remove(save_path)
        except Exception:
            image_url = url_for("upload.uploaded_images", filename=unique_filename)
    else:
        image_url = url_for("upload.uploaded_images", filename=unique_filename)

    specimen_id = f"PH-{random.randint(1000,9999)}"
    confidence_percent = prediction["confidence_value"] * 100

    new_history = History(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        type="single",
        specimen_id=specimen_id,
        timestamp=datetime.now().isoformat(),
        image_filename=unique_filename,
        prediction=json.dumps(prediction),
        confidence_percent=confidence_percent,
        notes="[]",
    )
    db.session.add(new_history)
    db.session.commit()

    if prediction.get("uncertain"):
        return render_template(
            "uncertain_results.html",
            prediction=prediction,
            imagepath=image_url,
            specimen_id=specimen_id,
            confidence_percent=confidence_percent,
            history_entry_id=new_history.id,
        )
    return render_template(
        "results.html",
        prediction=prediction,
        imagepath=image_url,
        specimen_id=specimen_id,
        confidence_percent=confidence_percent,
        history_entry_id=new_history.id,
    )
