from flask import render_template, redirect, url_for, request
from . import users_bp
from .forms import RegistrationForm, LoginForm
from app import db

@users_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
    # Create & Commit User
        flash('Account created', 'success')
        return redirect(url_for('users.login'))
    return render_template('register.html', form=form)