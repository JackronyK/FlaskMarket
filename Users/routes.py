from flask import render_template, redirect, url_for, flash, session, request
from . import users_bp
from .forms import UserRegistrationForm, UserProfileForm, UserLoginForm
from .models import Users
from extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo
from admins.models import Items
from .helpers import  check_password_strength, save_file, update_or_create_user_profile, prefill_profile_form



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
                flash("All fields are required", "danger")
                return redirect(url_for('users.register_user'))

            # Check password strength
            is_strong, message = check_password_strength(password)
            if not is_strong:
                flash(message, "danger")
                return redirect(url_for('users.register_user'))
        
            # Confirm Match
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
            flash('Account created Succefully!', 'success')
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
            redirect(url_for('users.user_login'))

        elif not user.check_password(form.password.data):
            flash("Invalid Passoword. Check and try again", "danger")
            redirect(url_for('users.user_login'))
        else:
            session.permanent = True
            session['user_logged_in'] = True
            session['user_id'] = user.user_id

            flash(f"Welcome {user.name} !", "success")
            return redirect(url_for('users.view_market'))
    return render_template('user_login.html', form=form)


@users_bp.route('/update_profile', methods=['GET', 'POST'])
def user_profile_update():
    form = UserProfileForm()
    user_id = session.get('user_id')  

    if not user_id:
        flash("Session expired. Please login again.", "warning")
        return redirect(url_for("users.user_login"))  
    # Prepopulate if GET
    if request.method == 'GET':
        prefill_profile_form(user_id, form) 

    # Handle standard  form submissin
    if form.validate_on_submit():
        try:
            profile_pic_filepath = save_file(form.profile_pic.data) 
            update_or_create_user_profile(user_id, form, profile_pic_filepath)
            db.session.commit()
            flash("Profile updated successfully", "success")
            return redirect(url_for('users.view_market'))
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to update profile: {str(e)}", 'danger')
            return render_template('user_profile_update.html', form=form)       

    return render_template('user_profile_update.html', form=form)

@users_bp.route('/logout')
def user_logout():    
    session.clear()
    session['user_logged_in'] = False
    return redirect(url_for('users.user_login'))

@users_bp.route('/view')
def view_market():
    items = Items.query.all()
    return render_template('user_view.html', items=items)
        

@users_bp.route('/tester')
def tester_page():
    form = UserProfileForm()
    return render_template('user_profile_update.html', form=form)      
        
@users_bp.context_processor
def inject_now():
    eat = ZoneInfo("Africa/Nairobi")
    return {'now': datetime.now(tz=eat)}      





