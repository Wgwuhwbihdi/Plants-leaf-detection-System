from flask import Blueprint, render_template

from app.services import ml_service

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def home():
    from flask_login import current_user
    from app.models import History
    import json
    
    recent_history = []
    if current_user.is_authenticated:
        entries = History.query.filter_by(user_id=current_user.id).order_by(History.timestamp.desc()).limit(2).all()
        for s in entries:
            recent_history.append({
                "id": s.id,
                "specimen_id": s.specimen_id,
                "timestamp": s.timestamp,
                "prediction": json.loads(s.prediction) if s.prediction else {}
            })
    return render_template("home.html", recent_history=recent_history)


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/help")
def help():
    return render_template("help.html")


@main_bp.route("/encyclopedia")
def encyclopedia():
    from app.models import Disease
    diseases = Disease.query.all()
    # Sort diseases so India/Global isn't just randomly placed
    diseases.sort(key=lambda d: d.name)
    
    # We still need a list of dictionaries to pass to JS tojson filter
    disease_list = [
        {
            "name": d.name,
            "cause": d.cause,
            "cure": d.cure,
            "image_url": d.image_url
        } for d in diseases
    ]
    return render_template("encyclopedia.html", diseases=disease_list)


@main_bp.route("/contact")
def contact():
    return render_template("contact.html")


@main_bp.route("/terms")
def terms():
    return render_template("terms.html")


@main_bp.route("/privacy")
def privacy():
    return render_template("privacy.html")


@main_bp.route("/offline")
def offline():
    return render_template("offline.html")
