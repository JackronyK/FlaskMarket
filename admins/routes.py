from flask import render_template, redirect, url_for, flash, request, session, Response
from . import admins_bp
from admins.forms import SingleItemForm, FilesLoadForm, AdminFormSignup, AdminFormLogin
from admins.models import AdminActionLog, ItemManagementlog, Admins, Items
from admins.data_ingestion import ItemsData, Admins, Utils
from functools import wraps
from extensions import db
from datetime import datetime
from zoneinfo import ZoneInfo
import csv
from io import StringIO


# Admins Aunthentication
def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in') and not session.get('is_approved'):
            return redirect(url_for('admins.admin_login'))
        return f(*args, **kwargs)
    return wrapper

def super_admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get('admin_logged_in') or not session.get('is_super_admin'):
            return redirect(url_for('admins.admin_login'))
        return f(*args, **kwargs)
    return wrapper

@admins_bp.route('/admins')
def admins():
    return render_template('/admin/admins_home.html') 

# Sign up
@admins_bp.route('/admin/signup', methods=['GET', 'POST'])
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
            return redirect(url_for('admins.admin_signup'))
        

        # Check password strength
        if len(password) < 8:
            flash("Password must be at least 8 characters long", "danger")
        if not any(char.isdigit() for char in password):
            flash("Password must contain at least one digit.", "danger")
            return redirect(url_for('admins.admin_signup'))
        if not any(char.isupper() for char in password):
            flash("Password must contain at least one uppercase letter.", "danger")
            return redirect(url_for('admins.admin_signup'))
        if not any(char.islower() for char in password):
            flash("Password must contain at least one lowercase letter.", "danger")
            return redirect(url_for('admins.admin_signup'))
        if not any(char in "!@#$%^&*()-_=+[]{}|;:'\",.<>?/`~" for char in password):
            flash("Password must contain at least one special character.", "danger")
            return redirect(url_for('admins.admin_signup'))
        if password != form.confirm_password.data.strip():
            flash("Passwords do not match", "danger")
            return redirect(url_for('admins.admin_signup'))

        # Check existing admin      
        if Admins.query.filter_by(name=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for('admins.admin_signup'))
        if Admins.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for('admins.admin_signup'))
        try:
            new_admin = Admins(name=username, email=email, admin_id = Utils.admin_id_generator())
            new_admin.set_password(password)
            db.session.add(new_admin)
            db.session.commit()
            flash("Admin account succefully created. Please login.", "success")
            return redirect(url_for('admins.admin_login'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error creating admin: {str(e)}", "danger")
            return render_template('/admin/admin_signup.html', form=form)
    return render_template('/admin/admin_signup.html', form=form)


# Sign  in
@admins_bp.route('/admin/login', methods=['GET','POST'])
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
                return redirect(url_for('admins.super_admin_manage'))
            else:
                return redirect(url_for('admins.admin_items_view'))     
    return render_template('admin/admin_login.html', form=form)


# Log out
@admins_bp.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admins.admin_login'))

# Super admin
## Approvals
@admins_bp.route('/admin/approvals', methods=['GET', 'POST'])
@super_admin_required
def super_admin_approvals():
    pending_approvals_admin = Admins.query.filter_by(is_approved=False).all()
    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        action = request.form.get('action')
        current_admin_id = session.get('admin_id')
        try:
            admin = Admins.query.get(admin_id)
            if admin:
                
                if action == 'approve':
                    admin.is_approved = True                    
                    flash(f"Admin {admin.name} approved successfully.")
                elif action == 'reject':
                    db.session.delete(admin)
                    flash(f"Admin {admin.name} rejected and removed.")
                current_admin = Admins.query.filter_by(admin_id=current_admin_id).first()
                admin_log = AdminActionLog(
                    log_id=AdminActionLog.generate_log_id(),
                    action=action,
                    target_admin_id=admin_id,
                    performed_by_admin_id=current_admin_id,
                    timestamp=datetime.now(tz=ZoneInfo("Africa/Nairobi")),
                    notes=f"Admin {admin.name} ({admin.admin_id}) was {action}d by Admin {current_admin.name} ({current_admin_id})"
                )
                db.session.add(admin_log)
                db.session.commit()
        except Exception as e:
            db.session.rollback()
            flash(f"Error processing request: {str(e)}", "danger")
        return redirect(url_for('admins.super_admin_approvals'))
    return render_template('admin/super_admin_approvals.html', pending_admins=pending_approvals_admin)

## Manage
@admins_bp.route('/admin/manage', methods=['GET', 'POST'])
@super_admin_required
def super_admin_manage():
    admins = Admins.query.all()
    if request.method == 'POST':
        admin_id = request.form.get('admin_id')
        action = request.form.get('action')
        current_admin_id = session.get('admin_id')

        valid_actions = ['promote', 'demote', 'deactivate']
        if action not in valid_actions:
            flash("Invalid action requested.", "danger")
            return redirect(url_for('admins.super_admin_manage'))

        admin = Admins.query.get_or_404(admin_id)

        if admin.admin_id == current_admin_id and action in ['demote', 'deactivate']:
            flash("You cannot demote or deactivate yourself.", "danger")
            return redirect(url_for('admins.super_admin_manage'))

        try:
            if action == 'promote':
                admin.is_super_admin = True
                flash(f"Admin {admin.name} promoted to Super Admin.", "success")
            elif action == 'demote':
                admin.is_super_admin = False
                flash(f"Admin {admin.name} demoted from Super Admin.", "info")
            elif action == 'deactivate':
                admin.is_approved = False
                flash(f"Admin {admin.name} has been deactivated.", "warning")

            # Log the action
            current_admin = Admins.query.filter_by(admin_id=current_admin_id).first()
            admin_log = AdminActionLog(
                log_id=AdminActionLog.generate_log_id(),
                action=action,
                target_admin_id=admin.admin_id,
                performed_by_admin_id=current_admin_id,
                timestamp=datetime.now(tz=ZoneInfo("Africa/Nairobi")),
                notes=f"Admin {admin.name} ({admin.admin_id}) was {action}d by Admin {current_admin.name} ({current_admin_id})"
            )

            db.session.add(admin_log)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            flash(f"Error processing request: {str(e)}", "danger")

        return redirect(url_for('admins.super_admin_manage'))

    return render_template('admin/super_admin_manage.html', admins=admins)

# Item Management
## upload
@admins_bp.route('/admin/items/upload', methods=['GET', 'POST'])
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
                'discount': form_item.discount.data,
                'category': form_item.category.data,
                'image_url': form_item.image_url.data.filename if form_item.image_url.data else None,
                'barcode': form_item.barcode.data,
                'description': form_item.description.data,
                'quantity': form_item.quantity.data,
                'added_by': session.get('admin_id')
            })
            # Logging  
            
            flash("Item added", "success")
        except Exception as e:
            flash(f"Error adding item: {e}", "danger")
        return redirect(url_for('admins.admin_items_view'))


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
        return redirect(url_for('admins.admin_items_view'))
    return render_template('admin/admin_item_upload.html', form_item=form_item, form_file=form_file)

## view
@admins_bp.route('/admin/items/view')
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

## download
@admins_bp.route('/admin/items/download')
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

## edit
@admins_bp.route('/admin/items/edit/<string:item_id>', methods=['GET', 'POST'])
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
                log_id=Utils.log_id_generator(),  # Generate a unique log ID
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
        return redirect(url_for("admins.admin_items_manage"))

    return render_template("admin/admin_items_edit.html", form=form)

# Manage
@admins_bp.route('/admin/items/manage', methods=['GET', 'POST'])
@admin_required
def admin_items_manage():


    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'delete_selected':
            selected_ids = request.form.getlist('selected_items')
            if not selected_ids:
                flash("No items selected for deletion", "warning")
                return redirect(url_for('admins.admin_items_manage'))

            try:
                # Enable autoflush to ensure all changes are flushed before deletion


                for item_id in selected_ids:
                    item = Items.query.filter_by(item_id=item_id).first()
                    if item:
                        current_itemid = item.item_id
                        current_name = item.name

                        # 1. log the deletion action
                        with db.session.no_autoflush:
                        # Create a log entry for the deletion
                            log = ItemManagementlog(
                                log_id=Utils.log_id_generator(),  # Generate a unique log ID
                                item_id=current_itemid,
                                action='deleted',
                                admin_id=session.get('admin_id'),
                                notes=f"Item {current_name} deleted in batch by admin {session.get('admin_id')}"
                            )
                            db.session.add(log)

                            # 2. delete the item
                            db.session.delete(item)  

                            # Commit all changes         
                db.session.commit()
                flash(f"{len(selected_ids)} items deleted and logged successfully!", "success")
            except Exception as e:
                db.session.rollback()
                flash(f"Error deleting items: {str(e)}", "danger")
            return redirect(url_for('admins.admin_items_manage'))
        
    items = Items.query.order_by(Items.date_added.desc()).all()
    return render_template('admin/admin_items_manage.html', items=items)
    

## Delete
@admins_bp.route('/admin/items/delete/<string:item_id>')
@admin_required
def admin_items_delete(item_id):
    item = Items.query.get_or_404(item_id)
    try:
        # 1. log  the deletion action
        log = ItemManagementlog(
            log_id=Utils.log_id_generator(),  # Generate a unique log ID
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
    return redirect(url_for('admins.admin_items_manage'))  # 👈 redirect back to manage page

  
@admins_bp.route('/admin/activity')
def admin_activity():
    logs = AdminActionLog.query.order_by(AdminActionLog.timestamp.desc()).all()
    return render_template('admin/super_admin_activity.html', logs=logs)

@admins_bp.route('/admin/item/activity')
def item_activity_log():
    logs = ItemManagementlog.query.order_by(ItemManagementlog.timestamp.desc()).all()
    return render_template('admin/items_manage_logs.html', logs=logs)





@admins_bp.context_processor
def inject_now():
    eat = ZoneInfo("Africa/Nairobi")
    return {'now': datetime.now(tz=eat)}

@admins_bp.context_processor
def inject_stats():
    stats = {
        'total_items': Items.query.count(),
        'total_admins': Admins.query.count(),        
        'pending_approvals': Admins.query.filter_by(is_approved=False).count(),
        'active_admins': Admins.query.filter_by(is_approved=True).count(),
        'updated_items': ItemManagementlog.query.filter_by(action='updated').count(),
        'deleted_items': ItemManagementlog.query.filter_by(action='deleted').count(),
    }
    recent_items_logs = ItemManagementlog.query.order_by(ItemManagementlog.timestamp.desc()).limit(5).all()
    recent_admins_logs = AdminActionLog.query.order_by(AdminActionLog.timestamp.desc()).limit(5).all()

    return {
        'stats': stats,
        'recent_admins_logs': recent_admins_logs,
        'recent_items_logs': recent_items_logs
    }
