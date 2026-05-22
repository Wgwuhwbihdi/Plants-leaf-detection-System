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
)
from werkzeug.utils import secure_filename
from celery.result import AsyncResult
import cloudinary
import cloudinary.uploader
from flask_login import login_required, current_user

from app.models import db, BatchJob, BatchResult
from app.utils import allowed_file, load_settings
from app.services.task_service import process_batch, celery

batch_bp = Blueprint("batch", __name__)


@batch_bp.route("/batch-upload/", methods=["POST"])
@login_required
def batch_upload():
    if "images" not in request.files:
        flash("No files found in the request.")
        return redirect(url_for("main.home"))
    images = request.files.getlist("images")
    if not images or all(image.filename == "" for image in images):
        flash("No images selected. Please choose files to upload.")
        return redirect(url_for("main.home"))

    valid_images = []
    saved_files = []
    specimen_ids = []

    os.makedirs(current_app.config["UPLOAD_FOLDER"], exist_ok=True)
    for image in images:
        if image.filename == "":
            continue
        if not allowed_file(image.filename):
            flash(f"Unsupported file type for {image.filename}.")
            return redirect(url_for("main.home"))

        unique_filename = f"temp_{uuid.uuid4().hex}_{secure_filename(image.filename)}"
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"], unique_filename)
        image.save(save_path)

        valid_images.append(save_path)
        saved_files.append(unique_filename)
        specimen_ids.append(f"PH-{random.randint(1000,9999)}")

    if not valid_images:
        flash("No valid images were uploaded.")
        return redirect(url_for("main.home"))

    settings = load_settings()
    task = process_batch.delay(valid_images, settings["confidence_thresholds"])

    batch_id = str(uuid.uuid4())
    new_batch = BatchJob(
        id=batch_id,
        user_id=current_user.id,
        timestamp=datetime.now().isoformat(),
        total_images=len(valid_images),
        avg_confidence=0,
    )
    db.session.add(new_batch)
    db.session.commit()

    return render_template(
        "batch_processing.html",
        task_id=task.id,
        batch_id=batch_id,
        saved_files=saved_files,
        specimen_ids=specimen_ids,
        valid_images=valid_images,
    )


@batch_bp.route("/api/batch-status/<task_id>/<batch_id>", methods=["POST"])
@login_required
def batch_status(task_id, batch_id):
    b = BatchJob.query.filter_by(id=batch_id, user_id=current_user.id).first()
    if not b:
        return {"state": "FAILURE", "status": "Unauthorized or not found."}

    task = AsyncResult(task_id, app=celery)
    if task.state == "PENDING":
        return {"state": task.state, "status": "Pending..."}
    elif task.state != "FAILURE":
        if task.ready():
            predictions = task.result
            data = request.json
            saved_files = data.get("saved_files", [])
            specimen_ids = data.get("specimen_ids", [])
            valid_images = data.get("valid_images", [])

            image_urls = []
            for save_path, unique_filename in zip(valid_images, saved_files):
                if current_app.config["CLOUD_STORAGE_ENABLED"]:
                    try:
                        cloud_res = cloudinary.uploader.upload(
                            save_path, folder="phyto lab_scans"
                        )
                        image_urls.append(cloud_res.get("secure_url"))
                        if os.path.exists(save_path):
                            os.remove(save_path)
                    except Exception:
                        image_urls.append(
                            url_for("upload.uploaded_images", filename=unique_filename)
                        )
                else:
                    image_urls.append(
                        url_for("upload.uploaded_images", filename=unique_filename)
                    )

            batch_results = []
            total_confidence = 0
            for i, (prediction, image_url, specimen_id, saved_file) in enumerate(
                zip(predictions, image_urls, specimen_ids, saved_files)
            ):
                conf = prediction["confidence_value"] * 100
                total_confidence += conf
                result = {
                    "index": i + 1,
                    "specimen_id": specimen_id,
                    "image_filename": saved_file,
                    "image_url": image_url,
                    "prediction": prediction,
                    "confidence_percent": conf,
                }
                batch_results.append(result)

                r_entry = BatchResult(
                    batch_id=batch_id,
                    index=i + 1,
                    specimen_id=specimen_id,
                    image_filename=saved_file,
                    image_url=image_url,
                    prediction=json.dumps(prediction),
                    confidence_percent=conf,
                )
                db.session.add(r_entry)

            avg_confidence = (
                total_confidence / len(batch_results) if batch_results else 0
            )
            b.avg_confidence = avg_confidence
            db.session.commit()

            return {
                "state": "SUCCESS",
                "result": batch_results,
                "avg_confidence": avg_confidence,
            }
        else:
            return {"state": task.state, "status": str(task.info)}
    return {"state": "FAILURE", "status": str(task.info)}


@batch_bp.route("/batch/<batch_id>")
@login_required
def view_batch(batch_id):
    b = BatchJob.query.filter_by(id=batch_id, user_id=current_user.id).first_or_404()
    results = (
        BatchResult.query.filter_by(batch_id=batch_id).order_by(BatchResult.index).all()
    )
    batch_results = []
    for r in results:
        batch_results.append(
            {
                "index": r.index,
                "specimen_id": r.specimen_id,
                "image_filename": r.image_filename,
                "image_url": r.image_url,
                "prediction": json.loads(r.prediction),
                "confidence_percent": r.confidence_percent,
            }
        )
    return render_template(
        "batch_results.html",
        batch_results=batch_results,
        batch_id=b.id,
        avg_confidence=b.avg_confidence,
    )
