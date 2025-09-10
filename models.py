from extensions import db, app
from flask_login import UserMixin
import random
import string
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

class Users(db.Model, UserMixin):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    
    # Relationships
    school_id = db.Column(db.Integer, db.ForeignKey('school.id', ondelete="CASCADE"), nullable=False)
    school = db.relationship('School', back_populates='users')
    
    user_group_id = db.Column(db.Integer, db.ForeignKey('user_group.id', ondelete="SET NULL"), nullable=True)
    group = db.relationship('UserGroup', back_populates='users')

    def __init__(self, fullname, school_id, is_admin=False, group_id=None, **kwargs):
        super().__init__(**kwargs)
        self.fullname = fullname
        self.school_id = school_id
        self.is_admin = is_admin
        if group_id:
            self.user_group_id = group_id  # Note: use user_group_id, not group_id

    def __repr__(self):
        return f'<User {self.fullname} (ID: {self.id})>'

class School(db.Model):
    __tablename__ = 'school'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    season = db.Column(db.Integer, default=1)
    
    # Relationships
    users = db.relationship('Users', back_populates='school', cascade='all, delete-orphan', passive_deletes=True)
    groups = db.relationship('UserGroup', back_populates='school', cascade='all, delete-orphan', passive_deletes=True)
    quiz_results = db.relationship('QuizResult', back_populates='school', cascade='all, delete-orphan')

    def archive(self):
        archived_school = ArchivedSchool(
            name=self.name,
            season=self.season,
            archived_date=datetime.now(timezone.utc)
        )
        db.session.add(archived_school)
        
        for user in self.users:
            archived_user = ArchivedUser(
                name=user.fullname,
                archived_school=archived_school
            )
            db.session.add(archived_user)
        
        for group in self.groups:
            archived_group = ArchivedGroup(
                name=group.name,
                archived_school=archived_school
            )
            db.session.add(archived_group)
        
        db.session.delete(self)
        db.session.commit()

class UserGroup(db.Model, UserMixin):  # Add UserMixin back
    __tablename__ = 'user_group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    passcode = db.Column(db.String(10), nullable=False, unique=True)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id', ondelete="CASCADE"), nullable=False)
    is_active = db.Column(db.Boolean, default=True)  # Required by Flask-Login

    # Relationships
    school = db.relationship('School', back_populates='groups')
    users = db.relationship('Users', back_populates='group')
    quiz_results = db.relationship('QuizResult', back_populates='user_group')

    # Required by Flask-Login
    def get_id(self):
        return str(self.id)

    def __init__(self, name, school_id, is_admin=False):
        self.name = name
        self.school_id = school_id
        self.is_admin = is_admin
        self.passcode = self.generate_passcode()

    def generate_passcode(self, length=8):
        characters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(characters) for _ in range(length))

class QuizResult(db.Model):
    __tablename__ = 'quiz_result'
    id = db.Column(db.Integer, primary_key=True)
    user_group_id = db.Column(db.Integer, db.ForeignKey('user_group.id'), nullable=False)
    question_index = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.String(100))
    result = db.Column(db.String(50))
    response_time = db.Column(db.Float)
    score = db.Column(db.Float)
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)
    season = db.Column(db.Integer)

    # Relationships
    user_group = db.relationship('UserGroup', back_populates='quiz_results')
    school = db.relationship('School', back_populates='quiz_results')

# Archived models remain the same
class ArchivedSchool(db.Model):
    __tablename__ = 'archived_school'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    season = db.Column(db.Integer)
    archived_date = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    archived_users = db.relationship('ArchivedUser', back_populates='archived_school', cascade='all, delete-orphan')
    archived_groups = db.relationship('ArchivedGroup', back_populates='archived_school', cascade='all, delete-orphan')

class ArchivedUser(db.Model):
    __tablename__ = 'archived_user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    archived_school_id = db.Column(db.Integer, db.ForeignKey('archived_school.id', ondelete='CASCADE'))
    archived_school = db.relationship('ArchivedSchool', back_populates='archived_users')

class ArchivedGroup(db.Model):
    __tablename__ = 'archived_group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    archived_school_id = db.Column(db.Integer, db.ForeignKey('archived_school.id', ondelete='CASCADE'))
    archived_school = db.relationship('ArchivedSchool', back_populates='archived_groups')

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    allow_registration = db.Column(db.Boolean, default=True)
    allow_quiz = db.Column(db.Boolean, default=True)
    current_season = db.Column(db.Integer)
    current_subject = db.Column(db.String(50))
    question_count = db.Column(db.Integer)
    quiz_duration = db.Column(db.Integer)  # Duration in seconds
    
class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(255), nullable=True)
    season = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now(timezone.utc))




def create_default_admin():
    """Create default admin school and admin group if they don't exist"""
    try:
        # Check if admin school already exists
        admin_school = School.query.filter_by(id=1).first()
        
        if not admin_school:
            # Create admin school
            admin_school = School(
                id=1,
                name="System Administrator",
                season=1
            )
            db.session.add(admin_school)
            db.session.flush()  # Flush to get the ID
        
        # Check if admin group already exists
        admin_group = UserGroup.query.filter_by(school_id=1, is_admin=True).first()
        
        if not admin_group:
            # Create admin group with a specific passcode
            admin_group = UserGroup(
                name="System Administrator",
                school_id=1,
                is_admin=True
            )
            # Set a specific passcode for admin (you can change this)
            admin_group.passcode = "9GVTJJ52"
            db.session.add(admin_group)
            db.session.flush()
        
        # Check if admin user already exists
        admin_user = Users.query.filter_by(is_admin=True).first()
        
        if not admin_user:
            # Create admin user
            admin_user = Users(
                fullname="System Administrator",
                school_id=1,
                user_group_id=admin_group.id,
                is_admin=True
            )
            db.session.add(admin_user)
        
        db.session.commit()
        print("Default admin setup completed successfully")
        
    except IntegrityError:
        db.session.rollback()
        print("Default admin already exists")
    except Exception as e:
        db.session.rollback()
        print(f"Error creating default admin: {str(e)}")

# Initialize database
with app.app_context():
    db.create_all()
    create_default_admin()
