import uuid
import json
from datetime import datetime
from flask import Blueprint, request, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from app.models import db, History, BatchJob, BatchResult

history_bp = Blueprint("history", __name__)


@history_bp.route("/history")
@login_required
def history():
    history_data = []
    singles = History.query.filter_by(user_id=current_user.id).all()
    for s in singles:
        history_data.append(
            {
                "id": s.id,
                "type": s.type,
                "specimen_id": s.specimen_id,
                "timestamp": s.timestamp,
                "image_filename": s.image_filename,
                "prediction": json.loads(s.prediction) if s.prediction else {},
                "confidence_percent": s.confidence_percent,
                "notes": json.loads(s.notes) if s.notes else [],
            }
        )
    batches = BatchJob.query.filter_by(user_id=current_user.id).all()
    for b in batches:
        results = BatchResult.query.filter_by(batch_id=b.id).all()
        res_data = []
        for r in results:
            res_data.append(
                {
                    "index": r.index,
                    "specimen_id": r.specimen_id,
                    "image_filename": r.image_filename,
                    "image_url": r.image_url,
                    "prediction": json.loads(r.prediction) if r.prediction else {},
                    "confidence_percent": r.confidence_percent,
                }
            )
        history_data.append(
            {
                "id": b.id,
                "type": "batch",
                "timestamp": b.timestamp,
                "total_images": b.total_images,
                "avg_confidence": b.avg_confidence,
                "results": res_data,
            }
        )
    history_data.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return render_template("history.html", history=history_data)


@history_bp.route("/api/notes/<specimen_id>", methods=["POST", "GET"])
@login_required
def api_notes(specimen_id):
    entry = History.query.filter_by(
        specimen_id=specimen_id, user_id=current_user.id
    ).first()
    if request.method == "GET":
        if entry:
            return {"notes": json.loads(entry.notes) if entry.notes else []}, 200
        return {"error": "Specimen not found"}, 404

    data = request.get_json()
    note_text = data.get("note", "").strip()
    if not note_text:
        return {"error": "Note text is required"}, 400

    if entry:
        notes = json.loads(entry.notes) if entry.notes else []
        new_note = {
            "text": note_text,
            "timestamp": datetime.now().isoformat(),
            "id": str(uuid.uuid4()),
        }
        notes.append(new_note)
        entry.notes = json.dumps(notes)
        db.session.commit()
        return {"success": True, "note": new_note}, 201
    return {"error": "Specimen not found"}, 404


@history_bp.route("/api/notes/<specimen_id>/<note_id>", methods=["DELETE"])
@login_required
def api_delete_note(specimen_id, note_id):
    entry = History.query.filter_by(
        specimen_id=specimen_id, user_id=current_user.id
    ).first()
    if entry:
        notes = json.loads(entry.notes) if entry.notes else []
        entry.notes = json.dumps([n for n in notes if n.get("id") != note_id])
        db.session.commit()
        return {"success": True}, 200
    return {"error": "Specimen not found"}, 404


@history_bp.route("/save-note", methods=["POST"])
@login_required
def save_note():
    entry_id = (request.form.get("entry_id") or "").strip()
    note_text = (request.form.get("note") or "").strip()
    if not entry_id:
        flash("Could not save note. Entry not found.")
        return redirect(request.referrer or url_for("history.history"))

    entry = History.query.filter_by(id=entry_id, user_id=current_user.id).first()
    if entry:
        notes = json.loads(entry.notes) if entry.notes else []
        notes.append(
            {
                "text": note_text,
                "timestamp": datetime.now().isoformat(),
                "id": str(uuid.uuid4()),
            }
        )
        entry.notes = json.dumps(notes)
        db.session.commit()
        flash("Note saved to history.")
        return redirect(request.referrer or url_for("history.history"))

    flash("Could not save note. Entry not found.")
    return redirect(request.referrer or url_for("history.history"))
