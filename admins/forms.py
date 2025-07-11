from flask_wtf import FlaskForm
from  wtforms import StringField, FloatField, FileField, IntegerField, TextAreaField, SubmitField, PasswordField
from wtforms.validators import DataRequired, Length, Email, Optional
from flask_wtf.file import FileAllowed, FileRequired

class SingleItemForm(FlaskForm):
    """
    This class is responsible for creating a form for adding a single item to the database.
    """
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=30)])
    price = FloatField('Price', validators=[DataRequired()])
    barcode = StringField('Barcode', validators=[Optional(), Length(min=1, max=12)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(min=1, max=1024)])
    quantity = IntegerField('Quantity', validators=[DataRequired()])
    submit = SubmitField('Add Item')


class FilesLoadForm(FlaskForm):
    """
    This class is responsible for creating a form for loading files to the database.
    """
    file = FileField('File', validators=[FileRequired(), FileAllowed(['csv', 'json'], 'CSV or JSON files only!')])
    submit = SubmitField('Upload File')

class AdminFormSignup(FlaskForm):
    """
    This class is responsible for creating a form for adding an admin to the database.
    """
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField('Email', validators=[DataRequired(), Length(min=3, max=50), Email(message="Enter a valid email address.")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=30)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=8, max=30)])
    submit = SubmitField('Add Admin')

class AdminFormLogin(FlaskForm):
    """
    This class is responsible for creating a form for admin login.
    """
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=30)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=30)])
    submit = SubmitField('Login')
