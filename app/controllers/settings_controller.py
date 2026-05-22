from flask import (
    Blueprint,
    request,
    redirect,
    url_for,
    flash,
    make_response,
    render_template,
)
from flask_login import login_required

from app.models import db, AppSetting
from app.services.translation_service import LANGUAGES, DEFAULT_LANGUAGE
from app.utils import load_settings, save_settings

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/set-language/<lang>")
def set_language(lang):
    selected = (lang or "").strip().lower()
    if selected not in LANGUAGES:
        selected = DEFAULT_LANGUAGE
    next_url = request.args.get("next")
    if not next_url:
        next_url = request.referrer or url_for("main.home")
    resp = make_response(redirect(next_url))
    resp.set_cookie(
        "lang", selected, max_age=30 * 24 * 60 * 60, samesite="Lax", httponly=False
    )
    return resp


@settings_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        try:
            high = float(request.form.get("high_threshold", 0.8))
            medium = float(request.form.get("medium_threshold", 0.6))
            low = float(request.form.get("low_threshold", 0.4))
            require_expert_review = request.form.get("require_expert_review") == "on"
            if not (0 < low <= medium <= high <= 1):
                flash("Invalid thresholds: Must be 0 < low ≤ medium ≤ high ≤ 1")
                return redirect(url_for("settings.settings"))
            settings_data = {
                "confidence_thresholds": {"high": high, "medium": medium, "low": low},
                "require_expert_review": require_expert_review,
            }
            save_settings(settings_data)
            flash("Settings updated successfully!")
        except ValueError:
            flash("Invalid input: Please enter valid numbers between 0 and 1.")
        return redirect(url_for("settings.settings"))

    current_settings = load_settings()
    return render_template(
        "settings.html",
        thresholds=current_settings["confidence_thresholds"],
        require_expert_review=current_settings["require_expert_review"],
    )
