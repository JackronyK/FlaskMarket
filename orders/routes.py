from . import orders_bp
from extensions import db
from orders.helpers import get_cart, clear_cart, remove_from_cart, add_to_cart
from flask import redirect, url_for, flash, render_template, request, session
from admins.models import Items
from .models import Order, OrderItem, ItemsTransactionLog
import uuid
from zoneinfo import ZoneInfo
from datetime import datetime

@orders_bp.route('/add/<string:item_id>', methods=['GET', 'POST'])
def add_item(item_id):
    if request.method == 'POST':
        quantity = int(request.form.get('quantity', 1))
    else:
        quantity = int(request.args.get('quantity', 1))

    item = Items.query.get_or_404(item_id)

    if quantity < 1:
        flash("Quantity must be at least 1", "warning")
        return redirect(request.referrer or url_for('Users.view_market'))
    if quantity > item.quantity:
        flash(f"Not enough stock for {item.name}. Available: {item.quantity}", "warning")
        return redirect(url_for('Users.view_market'))
    

    # add to cart
    add_to_cart(item_id, quantity)
    flash("Item added to cart.", "succcess")
    return redirect(request.referrer or url_for('orders.view_cart'))

@orders_bp.route('/cart')
def view_cart():
    cart = get_cart()
    line_items = []
    total = 0
    for item_id, qty in cart.items():
        item = Items.query.get(item_id)
        if not item: continue
        line_total = float(item.price) * qty
        total += line_total
        line_items.append({
            'item':item,
            'quantity': qty,
            'line_total': f"{line_total:,.2f}"
        })

    return render_template('cart.html', line_items=line_items, total=f"{total:,.2f}")

@orders_bp.route('/remove/<string:item_id>')
def remove_item(item_id):
    remove_from_cart(item_id)
    flash("Item removed from  cart", "danger")
    return redirect(url_for('orders.view_cart'))

@orders_bp.route('/checkout', methods=['GET', 'POST'])
def checkout():
    user_id = session.get('user_id')
    if not user_id:
        flash("Please log in to checkout", 'warning')
        return redirect(url_for('users.user_login'))
    
    cart = get_cart()
    if not cart:
        flash("your cart is empty.", "info")
        return redirect(url_for("orders.view_cart"))
    
    if request.method == 'POST':
        # Create Order
        order_id = f"O{uuid.uuid4().hex[:6].upper()}"
        total = 0
        new_order = Order(
            order_id=order_id,
            user_id=user_id,
            total = 0
        )
        db.session.add(new_order)

        # Add items
        for item_id, qty in cart.items():
            item = Items.query.get(item_id)
            if not  item:
                continue

            if qty > item.quantity:
                flash(f"Not enough stock for {item.name}. Available: {item.quantity}", "warning")
                return redirect(url_for('orders.view_cart'))
            
            # Subtract from stock
            item.quantity -= qty

            # Log transaction
            tx = ItemsTransactionLog(
                transaction_id=f"T{uuid.uuid4().hex[:10].upper()}",
                item_id=item.item_id,
                change_type='Sold',
                quantity_changed=-qty,
                actor=user_id,
                timestamp=datetime.now(ZoneInfo("Africa/Nairobi"))
            )
            db.session.add(tx)

            # Create order Item
            line_total = float(item.price) * qty
            total += line_total
            oi = OrderItem(
                order_id=order_id,
                item_id=item.item_id,
                quantity=qty,
                unit_price=item.price

            )
            db.session.add(oi)
        new_order.total=total
        db.session.commit()
        clear_cart()

        flash(f"Order {order_id} placed! Total Ksh {total:.2f}", "success")        
        return redirect(url_for('orders.view_orders'))
    
    return view_cart()

@orders_bp.route('/history')
def view_orders():
    user_id = session.get('user_id')
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    return render_template('order_history.html', orders=orders)

@orders_bp.context_processor
def inject_now():
    eat = ZoneInfo("Africa/Nairobi")
    return {
        'now': datetime.now(tz=eat),
        'cart': get_cart()
    }

