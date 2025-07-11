import os
class Config:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///Abuu_market.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'mYluv@/|27'
    BASEDIR = os.path.abspath(os.path.dirname(__file__))
    UPLOAD_FOLDER = os.path.join(BASEDIR, 'users', 'static','uploads', 'profile_pics')

