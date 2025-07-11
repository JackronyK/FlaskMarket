from flask import render_template, current_app, redirect, url_for, flash, session
from . import users_bp
from .forms import UserRegistrationForm, UserProfileForm, UserLoginForm
from .models import Users, Users_profile
import phonenumbers
from werkzeug.utils import secure_filename
import os
from extensions import db
from datetime import date
from datetime import datetime
from zoneinfo import ZoneInfo




@users_bp.route('/register', methods=['GET', 'POST'])
def register_user():
    form = UserRegistrationForm()
    if form.validate_on_submit():
    # Create & Commit User
        try:
            username = form.name.data.strip()
            password = form.password.data.strip()
            email = form.email.data.strip()
            confirm_password = form.confirm_password.data.strip()         


            # Validating all fields 
            if not username or not password or not email:
                flash("All field are requesred", "danger")

            # Check password strength
            if len(password) < 8:
                flash("Password must be at least 8 characters long", "danger")
            if not any(c.isdigit() for c in password):
                flash("Password must contain at least one digit", "danger")
                return redirect(url_for('users.register_user'))
            if not any(c.isupper() for c in password):
                flash("Password must contain at least one upper case letter")
                return redirect(url_for('users.register_user'))
            if not any(c.islower() for c in password):
                flash("Password must contain at least one lower case letter", "danger")
                return redirect(url_for('users.register_user'))
            if not any(c in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~" for c in password):
                flash("Password muts contain at least one speacial character", "danger")
            if password != confirm_password:
                flash("Passwords do not match", "danger")
                return redirect(url_for('users.register_user'))

            # Check for existing users
            if Users.query.filter_by(name=username).first():
                flash("The username already exists", "danger")
                return redirect(url_for('users.register_user'))

            if Users.query.filter_by(email=email).first():
                flash("The Email already exists", "danger")
                return redirect(url_for('users.register_user'))
            
            # Adding the new user
            new_user = Users(name=username, email=email, user_id=Users.generate_user_id())
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created', 'success')
            return redirect(url_for('users.user_login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error Adding new user: {e}", "danger")
            return render_template('register_user.html', form=form)           
    return render_template('register_user.html', form=form)


@users_bp.route('/signin', methods=['GET', 'POST'])
def user_login():
    form = UserLoginForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(name=form.name.data).first()
        if not user:
            flash("Invalid Username. Check and try again", "danger")
        elif not user.check_password(form.password.data):
            flash("Invalid Passoword. Check and try again", "danger")
        else:
            session.permanent = True
            session['user_logged_in'] = True
            session['admin_id'] = user.user_id

            flash(f"Welcome {user.name} !", "success")
            return redirect(url_for('users.view_market'))
    return render_template('user_login.html', form=form)

def get_country_phone_code(cc):
    try:
        code = f"+{phonenumbers.example_number_for_type(cc.upper(), phonenumbers.Phonetype.MOBILE).country_code}"
        return code
    except:
        return ''
    


def save_file(file_storage):
    if not file_storage:
        return None
    filename = secure_filename(file_storage.filename)
    today = date.today.isformat()
    base_folder = current_app.config['UPLOAD_FOLDER']
    file_path = os.path.join(base_folder, today, filename)
    file_storage.save(file_path)
    return filename



@users_bp.route('/update_profile', methods=['GET', 'POST'])
def user_profile_update():
    form = UserProfileForm()    
    if form.validate_on_submit():    
        # Phone number processing
        countryalpha2 = form.countrycode.data
        country_phonecode = get_country_phone_code(countryalpha2)
        phonenum = form.phone.data
        complete_phone_num = f"{country_phonecode}-{phonenum}"
        location = form.location.data
        dob = form.dob.data
        profile_pic_filepath = save_file(form.profilepic.data)
        invitationcode = form.invitecode.data
        marketingoptin = form.marketingmessages.data
        
        # New_profile upate
        try:
            new_user_profile = Users_profile (
                userp_id = Users_profile.generate_userp_id,
                user_id = session.get('user_id'),                
                phone_number = complete_phone_num,
                location = location,
                date_of_birth = dob,
                invite_code = invitationcode,
                profile_pic = profile_pic_filepath,
                maketing_opt_in = marketingoptin
            )

            db.session.add(new_user_profile)      
            db.commit()
            flash("Profile updated successfully", "success")
            return redirect(url_for('user_profile_view'))
        except Exception as e:
            db.session.rollback()
            flash('user not found', 'danger')
            return render_template('user_profile_update.html', form=form)
        
    return render_template('user_profile_update.html', form=form)

@users_bp.route('/view')
def view_market():
    return render_template('user_view.html')
        

@users_bp.route('/tester')
def tester_page():
    form = UserProfileForm()
    return render_template('user_profile_update.html', form=form)      
        
@users_bp.context_processor
def inject_now():
    eat = ZoneInfo("Africa/Nairobi")
    return {'now': datetime.now(tz=eat)}      





