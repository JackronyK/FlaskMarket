from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hush
from  flask_migrate import Migrate
from datetime import datetime
from zoneinfo import ZoneInfo

#Initialize the db
db = SQLAlchemy()

# Users table
class Users(db.model):
    __tablename__ = 'users'
    user_id = db.Column(db.String(), nullable=False, primary_key=True)
    name = db.Column(db.String(length=30), nullable=False, unique=True)
    email = db.Column(db.String(length=30), nullable=False, unique=True)
    password_hash = db.Column(db.String(length=30, nullable=False))
    # Profile Fields
    phone_number = db.Column(db.String(length=30), nullable=False)
    location = db.Column(db.String(200))
    date_of_birth = db.Column(db.Date)
    profile_pic = db.Column(db.Column(200)) # Path|URL to the pic
    invite_code = db.Column(db.Column, default=False)
    marketin_opt_in = db.Column(db.Boolean, default=False)
    create_at = db.Column(db.DateTime, default=db.func.current_timestamp)

    def generate_user_id():
        last_user_id = Users.query.filter(Users.user_id.like('U%').order_by(db.desc(Users.user_id))).first()
        if not last_user_id:
            return "U001"
        last_id = int(last_user_id[1:])
        return f"U{last_id + 1:03d}"
    
    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)
    
    def check_password(self, raw_password):
        return check_password_hush(self.password, raw_password)
    
    def __repr__(self):
        return f'User {self.name}'

class User_aunthet_logs():
    log_id = db.Column(db.string(length=6), primary_key=True)
    user_id = db.Column(db.string(), db.ForeignKey('users.user_id'), nullable=False)
    action = db.Column(db.String(), nullable=False)
    timestamp = db.Column(db.Datetime(timezone=True), nullable=False, default=lambda: datetime.now(ZoneInfo("Africa/Nairobi")))





