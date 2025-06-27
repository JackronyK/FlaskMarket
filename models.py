from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from datetime import datetime
from zoneinfo import ZoneInfo


# Initialize the database
db = SQLAlchemy()

# Items table
# This table stores the items available in the market
class Items(db.Model):
    __tablename__ = 'items'
    item_id = db.Column(db.String(), nullable=False, primary_key=True)
    name = db.Column(db.String(length=30), nullable=False)
    price = db.Column(db.Float(), nullable=False)
    barcode = db.Column(db.String(length=12), nullable=False, unique=True)
    description = db.Column(db.String(length=1024), nullable=False, unique=True)
    quantity = db.Column(db.Integer(), nullable=False)
    added_by = db.Column(db.String(length=30), db.ForeignKey('admins.admin_id'), nullable=False)
    date_added = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(ZoneInfo("Africa/Nairobi")))
    # Define the relationship with the Admins table
    admin = db.relationship('Admins', backref="items_added")
    def __repr__(self):
        return f'Item {self.name}'
    
class Admins(db.Model):

    __tablename__ = 'admins'

    admin_id = db.Column(db.String(), nullable=False, primary_key=True)
    name = db.Column(db.String(length=30), nullable=False, unique=True)
    email = db.Column(db.String(length=30), nullable=False, unique=True)
    password = db.Column(db.String(length=30), nullable=False)
    is_approved = db.Column(db.Boolean(), nullable=False, default=False)
    is_super_admin = db.Column(db.Boolean(), nullable=False, default=False)
    date_registered = db.Column(db.DateTime(), nullable=False, default=db.func.current_timestamp())

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)
    
    def check_password(self, raw_password):
        return  check_password_hash(self.password, raw_password)
    def __repr__(self):
        return f'Admin {self.name}'

class ItemManagementlog(db.Model):
    __tablename__ = 'item_management_log'
    log_id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.String(), db.ForeignKey('items.item_id'), nullable=False)
    action = db.Column(db.String(length=50), nullable=False)  # e.g., 'added', 'updated', 'deleted'
    admin_id = db.Column(db.String(), db.ForeignKey('admins.admin_id'), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(ZoneInfo("Africa/Nairobi")))
    notes = db.Column(db.Text)
    
    item = db.relationship('Items', backref='management_logs')
    admin = db.relationship('Admins', backref='management_logs')
    
    def __repr__(self):
        return f'Log {self.log_id} for Item {self.item_id} by Admin {self.admin_id}'