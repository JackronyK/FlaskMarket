from . import main_bp
from flask import render_template
from admins.models import Items
from datetime import datetime
from  zoneinfo import ZoneInfo


@main_bp.route('/')
@main_bp.route('/home')
def home_page():
    return render_template('home.html')

@main_bp.route('/market')
def market_page():
    items = Items.query.all()
    return  render_template('market.html', items=items)

@main_bp.route('/marketv2')
def market_page2():
    items = Items.query.all()
    return  render_template('market_v2.html', items=items)

@main_bp.context_processor
def inject_now():
    eat = ZoneInfo("Africa/Nairobi")
    return {'now': datetime.now(tz=eat)}
