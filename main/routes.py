from . import main_bp
from  extensions import db
from .forms import ContactForm
from .models import ContactSubmission
from flask import render_template, flash, redirect, url_for
from admins.models import Items
from datetime import datetime
from  zoneinfo import ZoneInfo


@main_bp.route('/')
def home_page():
    discounted_items = (
        Items.query
            .filter(Items.discount != None)
            .order_by(Items.discount.asc())
            .limit(4)
            .all()
    )
    return render_template('home.html', discounted_items=discounted_items)

@main_bp.route('/market')
def market_page():
    items = Items.query.all()
    return  render_template('market.html', items=items)

@main_bp.route('/about')
def about_page():
    return render_template('about.html')

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact_page():
    form = ContactForm()
    if form.validate_on_submit():
        # Save Subbmission
        submission = ContactSubmission(
            name=form.name.data.strip(),
            email=form.email.data.strip(),
            subject=form.subject.data.strip(),
            message=form.message.data.strip()
        )
        db.session.add(submission)
        db.session.commit()
        flash("Thank you! Your message has been sent.", "success")
        return redirect(url_for('main.contact_page'))
    return render_template('contact.html', form=form)

@main_bp.route('/marketv2')
def market_page2():
    items = Items.query.all()
    return  render_template('market_v2.html', items=items)

@main_bp.context_processor
def inject_now():
    eat = ZoneInfo("Africa/Nairobi")
    return {'now': datetime.now(tz=eat)}
