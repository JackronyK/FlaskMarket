from  flask import Flask, render_template, redirect, url_for, flash, session, request
from functools import wraps
from forms import SingleItemForm, FilesLoadForm, AdminFormLogin, AdminFormSignup
from datetime import timedelta
from flask_migrate import Migrate
from zoneinfo import ZoneInfo
from datetime import datetime
import csv
from io import StringIO
from flask import Response


# Initialize  Flask app
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flash_market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mYluv@/|27'
app.permanent_session_lifetime = timedelta(minutes=10)

from models import db, Items, ItemManagementlog
db.init_app(app)
migrate = Migrate(app, db)

from data_ingestion import ItemsData, Admins, Utils
from models import Admins, Items


# Home page route
@app.route('/')
@app.route('/home')
def home_page():
    return render_template('home.html')

# Admins aunthentication 
# Middleware to protect admins routes
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in') and not session.get('is_approved'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return wrapper

def super_admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in') or not session.get('is_super_admin'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return wrapper

@app.route('/admins')
def admins():
    return render_template('/admin/admins_home.html') 

@app.route('/admin')
def admin_signup_page():
    form = AdminFormSignup()
    return render_template('/admin/admin_signup.html', form=form)

# Admin page route
@app.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    form = AdminFormSignup()
    if form.validate_on_submit():
        # Validate form data
        username = form.name.data.strip()
        password = form.password.data.strip()
        email = form.email.data.strip()

        # validating all fields
        if not username or not password or not email:
            flash("All field are required", "danger")
            return redirect(url_for('admin_signup'))
        

        # Check password strength
        if len(password) < 8:
            flash("Password must be at least 8 characters long", "danger")
        if not any(char.isdigit() for char in password):
            flash("Password must contain at least one digit.", "danger")
            return redirect(url_for('admin_signup'))
        if not any(char.isupper() for char in password):
            flash("Password must contain at least one uppercase letter.", "danger")
            return redirect(url_for('admin_signup'))
        if not any(char.islower() for char in password):
            flash("Password must contain at least one lowercase letter.", "danger")
            return redirect(url_for('admin_signup'))
        if not any(char in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~" for char in password):
            flash("Password must contain at least one special character.", "danger")
            return redirect(url_for('admin_signup'))
        if password != form.confirm_password.data.strip():
            flash("Passwords do not match", "danger")
            return redirect(url_for('admin_signup'))

        # Check existing admin      
        if Admins.query.filter_by(name=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for('admin_signup'))
        if Admins.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for('admin_signup'))
        try:
            new_admin = Admins(name=username, email=email, admin_id = Utils.admin_id_generator())
            new_admin.set_password(password)
            db.session.add(new_admin)
            db.session.commit()
            flash("Admin account succefully created. Please login.", "success")
            return redirect(url_for('admin_login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating admin: {str(e)}", "danger")
            return render_template('/admin/admin_signup.html', form=form)
    return render_template('/admin/admin_signup.html', form=form)

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    form = AdminFormLogin()
    if form.validate_on_submit():
        admin = Admins.query.filter_by(name=form.name.data).first()
        if not admin:
            flash("Invalid Username. Check and try again", "danger")
        elif not admin.check_password(form.password.data):
            flash("Invalid Password. Check and try again", "danger")       
        else:
            session.permanent = True            
            session['admin_logged_in'] = True
            session['is_super_admin'] = admin.is_super_admin
            session['admin_id'] = admin.admin_id

            flash(f"Welcome {admin.name}!", "success")
            if admin.is_super_admin:
                return redirect(url_for('super_admin_manage'))
            else:
                return redirect(url_for('admin_items_view'))     
    return render_template('admin/admin_login.html', form=form)


@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('home_page'))

@app.route('/admin/approvals', methods=['GET', 'POST'])
@super_admin_required
def super_admin_approvals():
    pending_approvals_admin = Admins.query.filter_by(is_approved=False).all()
    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        action = request.form.get('action')
        try:
            admin = Admins.query.get(admin_id)
            if admin:
                if action == 'approve':
                    admin.is_approved = True
                    flash(f"Admin {admin.name} approved successfully.")
                elif action == 'reject':
                    db.session.delete(admin)
                    flash(f"Admin {admin.name} rejected and removed.")
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error processing request: {str(e)}", "danger")
        return redirect(url_for('super_admin_approvals'))
    return render_template('admin/super_admin_approvals.html', pending_admins=pending_approvals_admin)

@app.route('/admin/manage', methods=['GET', 'POST'])
@super_admin_required
def super_admin_manage():
    admins = Admins.query.all()
    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        action = request.form.get('action')
        admin = Admins.query.get_or_404(admin_id)
        if admin:
            if action == 'promote':
                admin.is_super_admin = True
                flash(f"Admin {admin.name} promoted to Super Admin.")
            elif action == 'delete':
                db.session.delete(admin)
                flash(f"Admin {admin.name} deleted successfully.")
            db.session.commit()
        return redirect(url_for('super_admin_manage'))
    return render_template('admin/super_admin_manage.html', admins=admins)

# item Management
@app.route('/admin/items/upload', methods=['GET', 'POST'])
@admin_required
def admin_item_upload():
    form_item = SingleItemForm()
    form_file = FilesLoadForm()
    if form_item.submit.data and form_item.validate_on_submit():
        try:
            ItemsData().load_single_item({
                'item_id':Utils.item_id_generator(),
                'name':form_item.name.data,
                'price': form_item.price.data,
                'barcode': form_item.barcode.data,
                'description': form_item.description.data,
                'quantity': form_item.quantity.data,
                'added_by': session.get('admin_id')
            })
            flash("Item added", "success")
        except Exception as e:
            flash(f"Error adding item: {e}", "danger")
        return redirect(url_for('admin_items_view'))


    if form_file.submit.data and form_file.validate_on_submit():
        file = form_file.file.data
        ext = file.filename.rsplit('.', 1)[1].lower()
        ingestion = ItemsData()
        try:
            if ext == 'csv':
                ingestion.load_csv_from_filestorage(file, session['admin_id'])
            elif ext == 'json':
                ingestion.load_json_from_filestorage(file, session['admin_id'])
            flash("File loaded succefully")
        except Exception as e:
            flash(f"Error loading file: {str(e)}")
        return redirect(url_for('admin_items_view'))
    return render_template('admin/admin_item_upload.html', form_item=form_item, form_file=form_file)

@app.route('/admin/items/view')
@admin_required
def admin_items_view():
    added_by_filter = request.args.get('added_by')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Items.query

    if added_by_filter:
        query = query.filter(Items.added_by == added_by_filter)

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(Items.date_added >= start_dt)

        except ValueError:
            flash("Invalid start date", "warning")
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            query = query.filter(Items.date_added <= end_dt)
        except ValueError:
            flash("Invalid end date", "warning")
    
    items = query.order_by(Items.date_added.desc()).all()
    all_admins = db.session.query(Items.added_by).distinct().all()
    return render_template('admin/admin_items_view.html', items=items, all_admins=all_admins)

@app.route('/admin/items/download')
@admin_required
def download_items_csv():
    items = Items.query.all()
    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['Item ID', 'Name', 'Barcode', 'Price', 'Description', 'Quantity', 'Added By', 'Added On'])

    for item in items:
        writer.writerow([
            item.item_id,
            item.name,
            item.barcode,
            item.price,
            item.description,
            item.quantity,
            item.added_by,
            item.date_added.strftime('%Y-%m-%d %H:%M:%S')
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype='text/csv',
        headers={
            "content-disposition": "attachment;filename=market_items.csv"
        }
    )
@app.route('/admin/items/edit/<string:item_id>', methods=['GET', 'POST'])
@admin_required
def admin_items_edit(item_id):
    item = Items.query.get_or_404(item_id)
    form = SingleItemForm(obj=item)
    
    if form.validate_on_submit():
        try:
            old_data = {
                "name": item.name,
                "price": item.price,
                "quantity": item.quantity
            }

            # Update values
            form.populate_obj(item)
            db.session.commit()

            # Create change summary
            new_data = {
                "name": item.name,
                "price": item.price,
                "quantity": item.quantity
            }
            changes = []
            for field in new_data:
                if old_data[field] != new_data[field]:
                    changes.append(f"{field}: {old_data[field]} → {new_data[field]}")

            notes = "Updated fields: " + ", ".join(changes) if changes else "No visible changes."

            log = ItemManagementlog(
                item_id=item.item_id,
                action="updated",
                admin_id=session.get("admin_id"),
                notes=notes
            )
            db.session.add(log)
            db.session.commit()

            flash("Item updated and logged successfully.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating item: {str(e)}", "danger")
        return redirect(url_for("admin_items_manage"))

    return render_template("admin/admin_items_edit.html", form=form)



@app.route('/admin/items/manage', methods=['GET', 'POST'])
@admin_required
def admin_items_manage():
    from models import Items

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'delete_selected':
            selected_ids = request.form.getlist('selected_items')
            if not selected_ids:
                flash("No items selected for deletion", "warning")
                return redirect(url_for('admin_items_manage'))
            
            try:
                for item_id in selected_ids:
                    item = Items.query.get(item_id)
                    if item:
                        db.session.delete(item)
                db.session.commit()
                flash(f"{len(selected_ids)} items deleted successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error deleting items: {str(e)}", "danger")
            return redirect(url_for('admin_items_manage'))
        
    items = Items.query.order_by(Items.date_added.desc()).all()
    return render_template('admin/admin_items_manage.html', items=items)
    
@app.route('/admin/items/delete/<string:item_id>')
@admin_required
def admin_items_delete(item_id):
    item = Items.query.get_or_404(item_id)
    try:
        # 1. log  the deletion action
        log = ItemManagementlog(
            item_id=item.item_id,
            action='deleted',
            admin_id=session.get('admin_id'),
            notes=f"Item {item.name} deleted by {session.get('admin_id')}"
        )
        db.session.add(log)

        # 2. delete the item
        db.session.delete(item)
        db.session.commit()
        flash("Item deleted and logged successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting item: {str(e)}", "danger")
    return redirect(url_for('admin_items_manage'))  # 👈 redirect back to manage page

  




@app.route('/market')
def market_page():
    items = Items.query.all()
    return  render_template('market.html', items=items)

@app.route('/marketv2')
def market_page2():
    items = Items.query.all()
    return  render_template('market_v2.html', items=items)

@app.context_processor
def inject_now():
    eat = ZoneInfo("Africa/Nairobi")
    return {'now': datetime.now(tz=eat)}



