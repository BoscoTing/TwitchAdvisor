import os
from dotenv import load_dotenv
load_dotenv()

class Config(object):
    # Env
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = "/static/assets"
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    JSON_AS_ASCII = False
    JSONIFY_PRETTYPRINT_REGULAR = True
    TOKEN_EXPIRE = 2592000

    # JWT token
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or "test"

    # Database
    SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{os.environ.get('DB_USERNAME')}:{os.environ.get('DB_PASSWORD')}@{os.environ.get('DB_HOST')}:3306/{os.environ.get('DB_DATABASE')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    DB_HOST = os.environ.get('DB_HOST')
    DB_USERNAME = os.environ.get('DB_USERNAME')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_DATABASE = os.environ.get('DB_DATABASE')