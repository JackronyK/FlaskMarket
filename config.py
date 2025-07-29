import os
import logging
class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///Abuu_market.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'mYluv@/|27'
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASEDIR, 'users', 'static','uploads', 'profile_pics')
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = "abuu.markets@gmail.com"
    MAIL_PASSWORD = "znlz bkwt htjc otwy"
    MAIL_DEFAULT_SENDER = ("Abuu Market", "abuu.markets@gmail.com")

    

