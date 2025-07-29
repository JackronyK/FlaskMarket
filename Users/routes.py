from flask import render_template, redirect, url_for, flash, session, request, make_response, render_template_string
from . import users_bp
from .forms import UserRegistrationForm, UserProfileForm, UserLoginForm, UserPasswordChangeForm, UserPasswordResetForm, UserPasswordResetConfirmForm
from .models import Users, UsersProfile, UserAuthLogs
from orders.models import Order
from extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo
from admins.models import Items
from .helpers import  check_password_strength, save_file, update_or_create_user_profile, prefill_profile_form, log_user_action, send_reset_email, verify_reset_token, generate_reset_token
from orders.helpers import get_cart
from werkzeug.security import check_password_hash
from weasyprint import HTML
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

            # Logging the activity
            log_user_action(user_id=user.user_id, action="Logged in")

            flash(f"Welcome {user.name} !", "success")
            return redirect(url_for('users.user_dashboard'))
    return render_template('user_login.html', form=form)


@users_bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    form = UserPasswordChangeForm()
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to change your password", "warning")
        return redirect(url_for('users.user_login'))
    user = Users.query.get(user_id)

    if form.validate_on_submit():
        if not check_password_hash(user.password, form.current_password.data):
            flash("Wrong current password", "danger")
        else:
            # Check new password strength
            is_strong, message = check_password_strength(form.new_password.data)
            if not is_strong:
                flash(message, "danger")
                return redirect(url_for('users.change_password'))
            
            # new password must be different from current
            if form.new_password.data == form.current_password.data:
                flash("New password must be different from current password", "danger")
                return redirect(url_for('users.change_password'))

            user.set_password(form.new_password.data)
            db.session.commit()
            log_user_action(user_id=user.user_id, action="Changed password")
            flash("Password changed successfully", "success")
            return redirect(url_for('users.user_dashboard'))
    return render_template('user_change_password.html', form=form, user=user)



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
            # Logging 
            log_user_action(user_id, "Updated profile")
            flash("Profile updated successfully", "success")
            return redirect(url_for('users.view_profile'))
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to update profile: {str(e)}", 'danger')
            return render_template('user_profile_update.html', form=form)   
    profile = UsersProfile.query.filter_by(user_id=user_id).first()    

    return render_template('user_profile_update.html', form=form, profile=profile)

@users_bp.route('/logout')
def user_logout():    
    session.clear()
    session['user_logged_in'] = False
    return redirect(url_for('users.user_login'))


@users_bp.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = UserPasswordResetForm()
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()

        if user:
            token = generate_reset_token(user.email)
            reset_url = url_for('users.reset_password', token=token, _external=True)
            send_reset_email(user.email, reset_url, user.name)
            log_user_action(user_id=user.user_id, action="Requested password reset email")
        
        flash("if the email exists, a reset link has been  sent.", "info")        
        return redirect(url_for('users.user_login'))
    return render_template("user_forgot_password.html", form=form)

@users_bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = verify_reset_token(token)
    if not email:
        flash("Invalid or expired token", "danger")
        return redirect(url_for('users.forgot_password'))
    
    user = Users.query.filter_by(email=email).first_or_404()
    form = UserPasswordResetConfirmForm()

    if form.validate_on_submit():
        is_strong, msg = check_password_strength(form.new_password.data)
        if not is_strong:
            flash(msg, "danger")
            return redirect(request.url)
        
        user.set_password(form.new_password.data)
        db.session.commit()
        log_user_action(user_id=user.user_id, action="Password Reset via token")
        flash("Password reset successful. Please login.", "success")
        return redirect(url_for('users.user_login'))
    
    return render_template('user_reset_password.html', form=form, token=token)
    

@users_bp.route('/profile')
def view_profile():
    user_id = session.get('user_id')

    if not user_id:
        flash("Please login to view your profile.", "warning")
        return redirect(url_for('users.user_login'))
    user = Users.query.filter_by(user_id=user_id).first()
    profile = UsersProfile.query.filter_by(user_id=user_id).first()
    log_user_action(user_id, "Viewed Profile")
    return render_template('user_profile_view.html', user=user, profile=profile)

@users_bp.route('/profile_logs')
def user_logs():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to view activity logs", "warning")
        return redirect(url_for('users.user_login'))
    
    logs = UserAuthLogs.query.filter_by(user_id=user_id).order_by(UserAuthLogs.timestamp.desc()).all()
    return render_template('user_logs.html', logs=logs)

@users_bp.route('/download_profile')
def download_profile():
    user_id = session.get('user_id')
    user = Users.query.filter_by(user_id=user_id).first()
    profile = UsersProfile.query.filter_by(user_id=user_id).first()

    html_content = render_template('user_pdf_template.html', user=user, profile=profile)
    pdf = HTML(string=html_content).write_pdf()

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename={user.name}_profile.pdf'
    return response


@users_bp.route('/dashboard')
def user_dashboard():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in  to Continue", "warning")
        return redirect(url_for('users.user_login'))
    
    # Fetch user & Profile
    user = Users.query.filter_by(user_id=user_id).first()
    profile = UsersProfile.query.filter_by(user_id=user_id).first()

    # Time-based greetings
    now = datetime.now(ZoneInfo("Africa/Nairobi"))
    hour = now.hour
    if hour < 12 : 
        greeting = "Good Morning"
    elif hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"

    # Stats
    total_items = Items.query.count()

    # Orders
    total_orders = Order.query.filter_by(user_id=user_id).count()


    # Profile completeness 
    fields = ['full_name', 'phone_number', 'location', 'date_of_birth', 'profile_pic']
    filled = sum(bool(getattr(profile, f, None)) for f in fields) if profile else 0
    completeness = filled/len(fields)

    # Last Login
    last_log = UserAuthLogs.query.filter_by(user_id=user_id).order_by(UserAuthLogs.timestamp.desc()).first()

    return render_template('user_dashboard.html',
                           user=user,
                           profile=profile,
                           greeting=greeting,
                           total_items=total_items,
                           total_orders = total_orders,
                           completeness=f"{completeness:.2%}",
                           last_log = last_log
                           )

@users_bp.route('/view')
def view_market():
    # Base query
    items_query = Items.query

    # Serch by name or barcode (SKU)
    q = request.args.get('q', type=str)
    if q:
        term = f"%{q.strip()}%"
        items_query = items_query.filter(
            db.or_(
                Items.name.ilike(term),
                Items.barcode.ilike(term)
            )
        )

    # Filter by  category
    category = request.args.get('category', type=str)
    if category:
        items_query = items_query.filter_by(category=category)

    # Filter by price range
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    if min_price is not None:
        items_query = items_query.filter(Items.price >= min_price)
    if max_price is not None:
        items_query = items_query.filter(Items.price <= max_price)

    # Execute
    items = items_query.order_by(Items.name).all()

    # For  category dropdown
    categories = [c[0] for c in db.session.query(Items.category).distinct()]

    return render_template('market_view.html', 
                           items=items,
                           q=q or "",
                           selected_category=category or "",
                           min_price=min_price if min_price is not None else "",
                           max_price=max_price if max_price is not None else "",
                           categories=categories)

"""
@users_bp.route('/shop')
def add_to_cart():
    items = Items.query.all()
    return render_template('add_cart.html')       

"""
@users_bp.route('/tester')
def tester_page():
    form = UserProfileForm()
    return render_template('user_profile_update.html', form=form)      
        
@users_bp.context_processor
def inject_now():
    eat = ZoneInfo("Africa/Nairobi")
    return {
        'now': datetime.now(tz=eat),
        'cart': get_cart()
    }      

from flask_mail import Message
from extensions import mail
@users_bp.route('/send_testing_email')
def send_testing_email():
    msg = Message(
        subject="Test Email from Abuu Market",
        bcc=["karani.riungu.a@gmail.com", "karanijackrony@gmail.com"],
        body="This is a test email from Abuu Market. If you see this, the email functionality is working!"
    )
    mail.send(msg)
    flash("Test email sent successfully!", "success")
    return redirect(url_for('users.user_dashboard'))

