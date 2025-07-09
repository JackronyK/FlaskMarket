from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, IntegerField, TextAreaField, SubmitField, PasswordField, SelectField, DateField, FileField, BooleanField
from wtforms.validators import  DataRequired, Length, Email, Optional
import pycountry
from flask_wtf.file import FileAllowed, FileRequired

class UserRegistrationForm(FlaskForm):
    """
    Register the users
    """
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField('Email', validators=[DataRequired(), Length(min=3, max=50), Email(message="Enter a valid email address")])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=30)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=8, max=30)])
    SubmitField = SubmitField('Create New User')
    

class UserLoginForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=30)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=30)])
    submit = SubmitField('Login')

def get_country_codes():
    countries = [(country.alpha_2, country.name) for country in  pycountry.countries]
    countries.sort(key=lambda x: x[1])
    return countries
class UserProfileForm(FlaskForm):
    country_code = SelectField('countrycode', choices=get_country_codes(), message="Select your country", validators=[DataRequired()])
    phone = StringField('phone', validators=[DataRequired(), Length(min=9, max=10)], message="Enter Phone Number without countryCode")
    location=StringField('location', validators=[DataRequired()])
    date_of_birth = DateField('dob', validators=[DataRequired()])
    profile_pic = FileField('profilepic', validators=[DataRequired(), FileAllowed('jpg', 'png')])
    invite_code = StringField('invitecode')
    marketing_opt_in = BooleanField('marketing messages', default=True)

