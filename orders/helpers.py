from  flask import session
def get_cart():
    """Returns session cart dict: {item_id: quantity}"""
    return session.setdefault('cart', {})

def add_to_cart(item_id, qty=1):
    cart = get_cart()
    cart[item_id] = cart.get(item_id, 0) + qty
    session.modified = True

def remove_from_cart(item_id):
    cart = get_cart()
    if item_id in  cart:
        del cart[item_id]
        session.modified = True

def clear_cart():
    session.pop('cart', None)

