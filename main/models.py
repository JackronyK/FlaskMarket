from extensions import db

class SiteVisitLog(db.Model):
    __tablename__ = 'site_visit_logs'
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(256), nullable=True)
    visited_at = db.Column(db.DateTime, nullable=False, server_default=db.func.now())