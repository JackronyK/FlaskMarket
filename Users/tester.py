from users.models import Users
from extensions import db
def generate_user_id():
    last_user_id = Users.query.filter(Users.user_id.like('U%')).order_by(db.desc(Users.user_id)).first()
    if not last_user_id:
        return "U001"
    last_id = int(last_user_id[1:])
    return f"U{last_id + 1:03d}"

generate_user_id()