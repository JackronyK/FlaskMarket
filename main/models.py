from extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo

class SiteVisitLog(db.Model):
    __tablename__ = 'site_visit_logs'
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(256), nullable=True)
    visited_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())

class ContactSubmission(db.Model):
    __tablename__='contatc_submission'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(150), nullable=False)
    message  = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Africa/Nairobi")))