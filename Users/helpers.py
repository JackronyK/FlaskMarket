import os
from  datetime import date, datetime
from flask import current_app, flash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from .models import UsersProfile, UserAuthLogs
from extensions import db, mail
import phonenumbers
import uuid
from zoneinfo import ZoneInfo
from itsdangerous import URLSafeTimedSerializer
from flask import current_app
from flask_mail import Message

# ---------
# Password Strength checker
# -------
def check_password_strength(password):
    if len(password) <8:
        return False, "Password must be at least 8 characters long"
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one upper case letter"
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lower case letter"
    if not any(c in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~" for c in password):
        return False, "Password muts contain at least one speacial character", "danger"
    return True, "Strong Password"


# ---------
# Save File
# -------
def save_file(file_storage):
    if not file_storage:
        flash("No file submitted.", "warning")
        return None

    # Debug: Check type
    if not isinstance(file_storage, FileStorage):
        return file_storage if isinstance(file_storage, str) else None

    try:
        filename = secure_filename(file_storage.filename)
        if filename == '':
            flash("Empty filename received.", "warning")
            return None

        today = date.today().isoformat()
        base_folder = current_app.config['UPLOAD_FOLDER']
        folder_path = os.path.join(base_folder, today)
        os.makedirs(folder_path, exist_ok=True)

        file_path = os.path.join(folder_path, filename)
        file_storage.save(file_path)

        flash(f"File saved to {file_path}", "success")
        return os.path.join(today, filename)  # Return relative path

    except Exception as e:
        flash(f"Failed to save file: {str(e)}", "danger")
        return None
    
# ---------
# Get Country Phone code
# -------

def get_country_phone_code(cc):
    try:
        code = f"+{phonenumbers.example_number_for_type(cc.upper(), phonenumbers.PhoneNumberType.MOBILE).country_code}"
        return code
    except:
        return ''
    

# ---------
# Create or Update user profile
# -------
def update_or_create_user_profile(user_id, form, file_path):
    user_profile = UsersProfile.query.filter_by(user_id=user_id).first()
    raw_phone = form.phone.data.strip()
    cleaned_phone = raw_phone[1:] if raw_phone.startswith("0") else raw_phone
    phone = f"{get_country_phone_code(form.country_code.data)}-{cleaned_phone}"

    if user_profile:
        # Updating
        user_profile.full_name = form.full_name.data
        user_profile.phone_number = phone
        user_profile.location = form.location.data
        user_profile.date_of_birth = form.date_of_birth.data
        user_profile.profile_pic = file_path or user_profile.profile_pic
        user_profile.invite_code = form.invite_code.data
        user_profile.marketing_opt_in = form.marketing_opt_in.data
    else:
        # Creating
        new_profile = UsersProfile(
            userp_id = UsersProfile.generate_userp_id(),
            user_id = user_id,
            full_name = form.full_name.data,               
            phone_number = phone,
            location = form.location.data,
            date_of_birth = form.date_of_birth.data,
            invite_code = form.invite_code.data,
            profile_pic = file_path,
            marketing_opt_in = form.marketing_opt_in.data
        )
        db.session.add(new_profile)


# ---------
# Prefiller helper function
# -------
def prefill_profile_form(user_id, form):
    user_profile = UsersProfile.query.filter_by(user_id=user_id).first()

    if not user_profile:
        return None
    
    try:
        form.full_name.data = user_profile.full_name
        form.phone.data = user_profile.phone_number.split("-")[-1]
        form.location.data = user_profile.location
        form.date_of_birth.data = user_profile.date_of_birth
        form.invite_code.data = user_profile.invite_code
        form.country_code.data = user_profile.phone_number.split("-")[0]

    except Exception as e:
        flash(f"Error prefiling profile form: {e}", "warning")
    
    return user_profile


# ---------
# Log User Actions
# -------

def log_user_action(user_id, action):
    log_entry = UserAuthLogs(
        log_id=str(uuid.uuid4())[:6].upper(),
        user_id=user_id,
        action=action,
        timestamp=datetime.now(ZoneInfo("Africa/Nairobi"))
    )
    db.session.add(log_entry)
    db.session.commit()




def generate_reset_token(email):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    return s.dumps(email, salt='password-reset')


def verify_reset_token(token, expiration=3600):
    s = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])

    try:
        email = s.loads(token, salt='password-reset', max_age=expiration)
    except Exception:
        return None
    return email


def send_reset_email(to_email, reset_url, user_name):
    subject = "Abuu Market | Password Reset Request"
    body = f"""
Hello {user_name},

You requested a password reset. Click the link below to reset your password:

{reset_url}

If you did not make this request, simply ignore this email.

-- Abuu Market Team
"""
    msg = Message(subject=subject, recipients=[to_email], body=body)
    mail.send(msg)

