from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Relationships
    history_entries = db.relationship(
        "History", backref="user", lazy=True, cascade="all, delete-orphan"
    )
    batch_jobs = db.relationship(
        "BatchJob", backref="user", lazy=True, cascade="all, delete-orphan"
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class History(db.Model):
    __tablename__ = "history"
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    type = db.Column(db.String(20), default="single")  # 'single' or 'batch'
    specimen_id = db.Column(db.String(20))
    timestamp = db.Column(db.String(30))
    image_filename = db.Column(db.String(255))

    # Store prediction as JSON string
    prediction = db.Column(db.Text)
    confidence_percent = db.Column(db.Float)

    # Store notes as JSON string
    notes = db.Column(db.Text, default="[]")


class BatchJob(db.Model):
    __tablename__ = "batch_jobs"
    id = db.Column(db.String(36), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    timestamp = db.Column(db.String(30))
    total_images = db.Column(db.Integer)
    avg_confidence = db.Column(db.Float)


class BatchResult(db.Model):
    __tablename__ = "batch_results"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    batch_id = db.Column(db.String(36), db.ForeignKey("batch_jobs.id"), nullable=False)
    index = db.Column(db.Integer)
    specimen_id = db.Column(db.String(20))
    image_filename = db.Column(db.String(255))
    image_url = db.Column(db.String(512))
    prediction = db.Column(db.Text)
    confidence_percent = db.Column(db.Float)


class AppSetting(db.Model):
    __tablename__ = "app_settings"
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text)  # JSON stored setting

class Disease(db.Model):
    __tablename__ = "diseases"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), unique=True, index=True) # e.g. Apple___Apple_scab or Rice___Leaf_Blast
    crop = db.Column(db.String(100))
    disease_name = db.Column(db.String(150))
    cause = db.Column(db.Text)
    cure = db.Column(db.Text)
    pathogen_type = db.Column(db.String(100))
    image_url = db.Column(db.String(512))
    region = db.Column(db.String(100), default="Global")
