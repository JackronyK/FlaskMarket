from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from zoneinfo import ZoneInfo



# Users table
class Users(db.Model):
    __tablename__ = 'users'
    user_id = db.Column(db.String(), nullable=False, primary_key=True)
    name = db.Column(db.String(length=30), nullable=False, unique=True)
    email = db.Column(db.String(length=30), nullable=False, unique=True)
    password = db.Column(db.String(length=30), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())


    @staticmethod
    def generate_user_id():
        last_user = Users.query.filter(Users.user_id.like('U%')).order_by(db.desc(Users.user_id)).first()
        last_user_id = last_user.user_id
        if not last_user_id:
            return "U001"
        last_id = int(last_user_id[1:])
        return f"U{last_id + 1:03d}"
    
    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)
    
    def check_password(self, raw_password):
        return check_password_hash(self.password, raw_password)
    
    def __repr__(self):
        return f'User {self.name}'
class Users_profile(db.Model):
    __tablename__ = 'users_profiles'
    userp_id = db.Column(db.String(length=7), primary_key=True)
    # Profile Fields    
    user_id = db.Column(db.String(), db.ForeignKey('users.user_id'), nullable=False)
    full_name = db.Column(db.String(), nullable=False)
    phone_number = db.Column(db.String(length=30), nullable=False)
    location = db.Column(db.String(200), nullable=False )
    date_of_birth = db.Column(db.Date, nullable=False)
    profile_pic = db.Column(db.String(200), nullable=False) # Path|URL to the pic
    invite_code = db.Column(db.String, nullable=False)
    marketin_opt_in = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    @staticmethod
    def generate_userp_id():
        last_userp = Users_profile.query.filter(Users_profile.userp_id.like('U%')).order_by(db.desc(Users_profile.userp_id)).first()
        last_userp_id = last_userp.userp_id
        if not last_userp_id:
            return "UP001"
        last_id = int(last_userp_id[1:])
        return f"U{last_id + 1:03d}"


class User_aunthet_logs(db.Model):
    log_id = db.Column(db.String(length=6), primary_key=True)
    user_id = db.Column(db.String(), db.ForeignKey('users.user_id'), nullable=False)
    action = db.Column(db.String(), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(ZoneInfo("Africa/Nairobi")))





