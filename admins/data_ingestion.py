import pandas as pd
import json
from extensions import db
from admins.models import Items, Admins, ItemManagementlog
from werkzeug.security import generate_password_hash
import logging

from flask import flash
from werkzeug.utils import secure_filename
import os
import requests
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

class ItemsData:
    """
    This class is responsible for loading items data from a CSV file, json  or single items into the database.
    """
    def __init__(self, file_path=None):
        self.file_path = file_path

    def save_items(self, item):
        """
        Save a single item to the database.
        """
        try:
            db.session.add(item)
            db.session.commit()
            logger.info(f"Item {item.name} saved successfully.")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error saving item {item.name}: {e}")
            raise
    def load_single_item(self, item_data):
        try:
            itemid = item_data.get('item_id') if 'item_id' in item_data and pd.notna(item_data.get('item_id')) else Utils.item_id_generator()
            bar_code = item_data.get('barcode') if 'barcode' in item_data and item_data['barcode'] else Utils.barcode_generator()
            
            item_name = item_data['name']
            image_file = item_data.get('image_file')

            # If an image file is provided, save it
            if image_file and image_file.filename != "":
                image_url = Utils.save_file(image_file, subfolder='items')
                logger.info(f"Image for {item_name} saved successfully at {image_url}.")

            # Else, check if another item with same name exists
            else:
                existing_item = Items.query.filter_by(name=item_name).first()
                if existing_item and existing_item.image_url:
                    image_url = existing_item.image_url
                    logger.info(f"Using existing image for {item_name} at {image_url}.")
                else:
                    image_url = Utils.fetch_image(item_name)
                    logger.info(f"Fetched image for {item_name} from external source: {image_url}.")    

            item = Items(
                item_id= str(itemid),
                name=item_data['name'],
                price=item_data['price'],
                discount=item_data.get('discount'),
                barcode= str(bar_code),
                image_url = image_url,
                category=item_data.get('category', 'others'),
                description=item_data['description'],
                quantity=item_data['quantity'],
                added_by=item_data['added_by']
            )
            self.save_items(item)
        except KeyError as ke:
            logger.error(f"Missing key in item data: {ke}")
            raise
        except Exception as e:
            logger.error(f"Error loading single item: {e}")
            raise

    def load_csv_from_filestorage(self, file_storage, added_by):
        """
        Load items from a CSV file uploaded via Flask's FileStorage to the database.

        :param file_storage: The file storage object containing the CSV file.
        :param added_by: The ID of the admin who added the items.
        """
        try:
            # Read the CSV file from the FileStorage object
            df = pd.read_csv(file_storage)
            
            # Iterate over the rows and create Items objects
            for _, row in df.iterrows():
                # ensure id: if csv provides id use it else generate
                item_id = row.get('item_id') if 'item_id' in row and pd.notna(row.get('item_id')) else Utils.item_id_generator()
                bar_code = row.get('barcode') if 'barcode' in row and pd.notna(row.get('barcode')) else Utils.barcode_generator()


                # Check if the item already exists
                image_url = row.get('image_url')
                if not image_url or image_url.strip() == "":
                    image_url = Utils.fetch_image(row['name'])

                item = Items(
                    item_id=str(item_id),
                    name=row['name'],
                    price=row['price'],
                    discount=row.get('discount'),
                    barcode=str(bar_code),
                    image_url=image_url,
                    description=row['description'],
                    quantity=row['quantity'],
                    category=row.get('category', 'others'),
                    added_by=added_by
                )
                self.save_items(item)
        except Exception as e:
            logger.error(f"Error loading CSV file from FileStorage: {e}")
            raise


    def load_json_from_filestorage(self, file_storage, added_by):
        """
        Load items from a JSON file uploaded via Flask's FileStorage to the database.

        :param file_storage: The file storage object containing the JSON file.
        :param added_by: The ID of the admin who added the items.
        """
        try:
            # Read the JSON file from the FileStorage object
            data = json.load(file_storage)
            
            # Iterate over the items and create Items objects
            for item_data in data:
                item_id = item_data.get('item_id') if 'item_id' in item_data and item_data['item_id'] else Utils.item_id_generator()
                bar_code = item_data.get('barcode') if 'barcode' in item_data and item_data['barcode'] else Utils.barcode_generator()
                
                # Check if the item already exists
                image_url = item_data.get('image_url')
                if not image_url or image_url.strip() == "":
                    image_url = Utils.fetch_image(item_data['name'])
                item = Items(
                    item_id=str(item_id),
                    name=item_data['name'],
                    price=item_data['price'],
                    discount=item_data.get('discount'),
                    barcode=str(bar_code),
                    image_url=image_url,
                    description=item_data['description'],
                    category=item_data.get('category', 'others'),
                    quantity=item_data['quantity'],
                    added_by=added_by
                )
                self.save_items(item)
        except Exception as e:
            logger.error(f"Error loading JSON file from FileStorage: {e}")
            raise



class AdminsData:
    """
    This class is responsible for loading admins data from a CSV file, json  or single admins into the database.
    """
    def __init__(self, file_path=None):
        self.file_path = file_path


    def save_admins(self, admin):
        """
        Save a single admin to the database.
        """
        try:
            db.session.add(admin)
            db.session.commit()
            print(f"Admin {admin.name} saved successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error saving admin {admin.name}: {e}")
    
    def load_csv(self):
        """
        Load admins from a csv to the database
        """
        try:
            # Read the CSV file
            df = pd.read_csv(self.file_path)
            # Iterate over the rows and create Admins objects
            for _, row in df.iterrows():
                admin = Admins(
                    admin_id=row['admin_id'],
                    name=row['name'],
                    email=row['email'],
                    password=generate_password_hash(row['password']),
                    is_approved=row['is_approved'],
                    is_super_Admin=row['is_super_Admin']
                )
                self.save_admins(admin)
        except Exception as e:
            print(f"Error loading CSV file: {e}")
    def load_json(self):
        """
        Load admins from a json file to the database
        """
        try:
            # Read the JSON file
            with open(self.file_path, 'r') as file:
                data = json.load(file)
            # Iterate over the items and create Admins objects
            for admin_data in data:
                admin = Admins(
                    admin_id=admin_data['admin_id'],
                    name=admin_data['name'],
                    email=admin_data['email'],
                    password=generate_password_hash(admin_data['password']),
                    is_approved=admin_data['is_approved'],
                    is_super_Admin=admin_data['is_super_Admin']
                )
                self.save_admins(admin)
        except Exception as e:
            print(f"Error loading JSON file: {e}")
    def load_single_admin(self, admin_data):
        """
        Load a single admin to the database
        """
        try:
            admin = Admins(
                admin_id=admin_data['admin_id'],
                name=admin_data['name'],
                email=admin_data['email'],
                password=generate_password_hash(admin_data['password']),
                is_approved=admin_data['is_approved'],
                is_super_Admin=admin_data['is_super_Admin']
            )
            self.save_admins(admin)
        except Exception as e:
            print(f"Error loading single admin: {e}")


class Utils:
    """
    This class is responsible for helper functions
    """
    @staticmethod
    def admin_id_generator():
        """
        Generate a unique admin id
        """
        last_admin = Admins.query.order_by(Admins.admin_id.desc()).first()
        if last_admin:
            last_num = int(last_admin.admin_id.replace("admin", ""))
            return f"admin{last_num + 1:03d}"
        return "admin001"
    @staticmethod
    def item_id_generator():
        """
        Generate a unique item id
        """
        last_item = Items.query.order_by(Items.item_id.desc()).first()
        if last_item:
            last_num = int(last_item.item_id.replace("item", ""))
            return f"item{last_num + 1:03d}"
        return "item001"
    
    @staticmethod
    def barcode_generator():
        """
        Generate a unique barcode
        """
        last_item = Items.query.order_by(Items.barcode.desc()).first()
        if last_item:
            last_num = int(last_item.barcode)
            return str(last_num + 1).zfill(12)
        return "123456789001"
    
    @staticmethod
    def log_id_generator():
        """
        Generate a unique log ID like L001, L002, ...
        """
        last_log = ItemManagementlog.query.filter(ItemManagementlog.log_id.like('L%')).order_by(
            db.desc(ItemManagementlog.log_id)
        ).first()

        if not last_log:
            return "L001"

        last_num = int(last_log.log_id[1:])
        return f"L{last_num + 1:03d}"
    
    @staticmethod
    def fetch_image(item_name, save_folder='admins/static/images/items'):
        access_key = os.getenv("UNSPLASH_ACCESS_KEY")
        secret_key = os.getenv("UNSPLASH_SECRET_KEY")

        """
        Fetch an image from an external API based on the item name.
        """
        try:
            headers = {
                'Accept-Version': 'v1',
                'Authorization': f'Client-ID {access_key}'
            }

            params = {
                'query': item_name,
                'orientation': 'squarish',
            }
            response = requests.get('https://api.unsplash.com/photos/random', headers=headers, params=params)
            if response.status_code != 200:
                print(f"[Unsplash API] faied API call: {response.status_code}")
                return None
            
            # Extract the image URL
            image_url = response.json().get('urls', {}).get('regular')
            if not image_url:
                print(f"[Unsplash] Image URL not found in response for {item_name}.")
                return None
            
            # Download the image
            image_data = requests.get(image_url)
            if image_data.status_code != 200:
                print(f"Failed to download image: {image_data.status_code}")
                return None
            
            # Save the image to the specified folder
            filename = secure_filename(f"{item_name.lower().replace(' ', '_')}.jpg")
            os.makedirs(save_folder, exist_ok=True)
            file_path = os.path.join(save_folder, filename)

            with open(file_path, 'wb') as file:
                file.write(image_data.content)
            print(f"Image for {item_name} saved successfully at {file_path}.")

            return f"images/items/{filename}"
        
        except Exception as e:
            print(f"[Unsplash] Exception Error fetching image for {item_name}: {e}")
            return None
        

    @staticmethod
    def save_file(file, subfolder='items'):
        """
        Save a file to the specified subfolder.
        """
        if not file:
            return None
        
        filename = secure_filename(file.filename)
        upload_folder = os.path.join(os.getcwd(), 'admins', 'static', 'images', subfolder)
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        return f"images/{subfolder}/{filename}"
        



            



 