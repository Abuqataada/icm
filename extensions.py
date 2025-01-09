from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure SQLite database
app.config['SECRET_KEY'] = 'nhjvsnjtrhgv,nvknryvn4wt7tvt4ttnsnhj$362$#@^$#@h#$$#&$GYCGHSGHDcgcegcsfgyes'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://avnadmin:AVNS_LxUTMKMU7GW7gwm1sas@postgresdb-abuqataada21-54f9.d.aivencloud.com:23198/defaultdb?sslmode=require'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure upload folder for images
app.config['UPLOAD_FOLDER'] = 'static/uploads'

db = SQLAlchemy(app)

# Create the database tables
with app.app_context():
    db.create_all()