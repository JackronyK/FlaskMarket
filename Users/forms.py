from flask_wtf import FlaskForm
from wtforms import StringField,  SubmitField, PasswordField, SelectField, DateField, FileField, BooleanField
from wtforms.validators import  DataRequired, Length, Email
import pycountry
from flask_wtf.file import FileAllowed

class UserRegistrationForm(FlaskForm):
    """
    Register the users
    """
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField('Email', validators=[DataRequired(), Length(min=3, max=50), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=30)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), Length(min=8, max=30)])
    submit = SubmitField('Create New User')
    

class UserLoginForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=3, max=30)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=30)])
    submit = SubmitField('Login')

def get_country_codes():
    countries = [(country.alpha_2, country.name) for country in  pycountry.countries]
    countries.sort(key=lambda x: x[1])
    return countries
class UserProfileForm(FlaskForm):
    full_name = StringField('Full Name',validators=[DataRequired()] )
    country_code = SelectField('countrycode', choices=get_country_codes(), validators=[DataRequired()])
    phone = StringField('phone', validators=[DataRequired(), Length(min=9, max=10)])
    location=StringField('location', validators=[DataRequired()])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    profile_pic = FileField('profilepic', validators=[DataRequired(), FileAllowed('jpg', 'png')])
    invite_code = StringField('invitecode')
    marketing_opt_in = BooleanField('marketingmessages', default=True)

