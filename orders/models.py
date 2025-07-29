from extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo

class Order(db.Model):
    __tablename__ = 'orders'
    order_id = db.Column(db.String(10), primary_key=True)
    user_id = db.Column(db.String(), db.ForeignKey('users.user_id'), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='Pending') # e.g Pending, Paid and Shipped
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(ZoneInfo("Africa/Nairobi")))

    items = db.relationship('OrderItem', backref='order', cascade='all, delete-orphan')

class OrderItem(db.Model):
    __tablename__ = 'order_items'
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(10), db.ForeignKey('orders.order_id'), nullable=False)
    item_id = db.Column(db.String, db.ForeignKey('items.item_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)

class ItemsTransactionLog(db.Model):
    __tablename__ = 'items_transactions'

    transaction_id = db.Column(db.String(), primary_key=True)
    item_id = db.Column(db.String(), db.ForeignKey('items.item_id'), nullable=False)
    change_type = db.Column(db.String(length=50), nullable=False)  # e.g. 'Added', 'Updated', 'Deleted'
    quantity_changed = db.Column(db.Integer(), nullable=False)
    timestamp = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(ZoneInfo("Africa/Nairobi")))
    actor = db.Column(db.String(), nullable=False)

    def __repr__(self):
        return f"<ItemsTransactionLog {self.transaction_id} - {self.change_type} - {self.item_id}>"