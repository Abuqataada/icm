from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
import os

app = Flask(__name__)

# Configure SQLite database
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "for_development")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("ICM_DB_URI", "sqlite:///users.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Disable debug mode in production
app.config["DEBUG"] = os.getenv("FLASK_ENV", "production") == "development"

# Configure upload folder for images
app.config['UPLOAD_FOLDER'] = 'static/uploads'

pymysql.install_as_MySQLdb()

db = SQLAlchemy(app)

# Create the database tables
with app.app_context():
    db.create_all()
