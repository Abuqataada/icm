from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

import os

app = Flask(__name__, instance_relative_config=True)
# Configure SQLite database
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "for_development")
#app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("ICM_DB_URI", "sqlite:///users.db")


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(app.instance_path, 'users.db')
#app.config['SQLALCHEMY_BINDS'] = {
#    'remote': 'postgresql://neondb_owner:npg_CzyA6c9imSWL@ep-noisy-sun-a41ubng9-pooler.us-east-1.aws.neon.tech/icm_db?sslmode=require&channel_binding=require',
#    'local': 'sqlite:///' + os.path.join(app.instance_path, 'users.db')
#}


app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Disable debug mode in production
app.config["DEBUG"] = os.getenv("FLASK_ENV", "production") == "development"

# Configure upload folder for images
app.config['UPLOAD_FOLDER'] = 'static/uploads'

#pymysql.install_as_MySQLdb()

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Create the database tables
with app.app_context():
    db.create_all()
