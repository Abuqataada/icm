from flask import Flask
from flask_sqlalchemy import SQLAlchemy
<<<<<<< HEAD
import pymysql
from flask_migrate import Migrate

=======
>>>>>>> ed55138 (Updated the db)
import os

app = Flask(__name__)

# Configure SQLite database
<<<<<<< HEAD
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "for_development")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("ICM_DB_URI", "sqlite:///users.db")
=======
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('ICM_DB_URI')
#app.config['SECRET_KEY'] = 'nhjvsnjtrhgv,nvknryvn4wt7tvt4ttnsnhj$362$#@^$#@h#$$#&$GYCGHSGHDcgcegcsfgyes'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://avnadmin:AVNS_LxUTMKMU7GW7gwm1sas@postgresdb-abuqataada21-54f9.d.aivencloud.com:23198/defaultdb?sslmode=require'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
>>>>>>> ed55138 (Updated the db)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Disable debug mode in production
app.config["DEBUG"] = os.getenv("FLASK_ENV", "production") == "development"

# Configure upload folder for images
app.config['UPLOAD_FOLDER'] = 'static/uploads'

pymysql.install_as_MySQLdb()

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Create the database tables
with app.app_context():
    db.create_all()
