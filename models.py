from extensions import db, app
from flask_login import UserMixin
import random
import string
from datetime import datetime, timezone



# Define the User model
class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    fullname = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Foreign key relationship with School
    school_id = db.Column(db.Integer, db.ForeignKey('school.id', ondelete="CASCADE"), nullable=False)

    # Foreign key relationship with Group
    group_id = db.Column(db.Integer, db.ForeignKey('group.id', ondelete="SET NULL"), nullable=True)  # Set to NULL if group is deleted

    def __init__(self, fullname, school_id, group_id=None, is_admin=False):
        self.fullname = fullname
        self.school_id = school_id
        self.group_id = group_id
        self.is_admin = is_admin


# Define the School model
class School(db.Model):
    __tablename__ = 'school'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    season = db.Column(db.Integer, default=1)
    
    # Relationship with User and Group (Cascade delete)
    students = db.relationship('User', backref='school', cascade='all, delete-orphan', passive_deletes=True)
    groups = db.relationship('Group', backref='school', cascade='all, delete-orphan', passive_deletes=True)

    def archive(self):
        # Archive associated users and groups
        archived_school = ArchivedSchool(
            name=self.name,
            season=self.season,
            archived_date=datetime.now(timezone.utc)
        )
        db.session.add(archived_school)
        
        # Move each student and group to archived relationships
        for student in self.students:
            archived_student = ArchivedUser(
                name=student.name,
                school=archived_school  # Associate with ArchivedSchool
            )
            db.session.add(archived_student)
        
        for group in self.groups:
            archived_group = ArchivedGroup(
                name=group.name,
                archived_school_id=self.id   # Associate with ArchivedSchool
            )
            db.session.add(archived_group)
        
        db.session.delete(self)
        db.session.commit()

# Define ArchivedSchool model
class ArchivedSchool(db.Model):
    __tablename__ = 'archived_school'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    season = db.Column(db.Integer)
    archived_date = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    
    # Relationships for archived students and groups
    archived_students = db.relationship('ArchivedUser', backref='archived_school', cascade='all, delete-orphan')
    archived_groups = db.relationship('ArchivedGroup', backref='archived_school', cascade='all, delete-orphan')

# Define ArchivedUser model
class ArchivedUser(db.Model):
    __tablename__ = 'archived_user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    archived_school_id = db.Column(db.Integer, db.ForeignKey('archived_school.id', ondelete='CASCADE'))

# Define ArchivedGroup model
class ArchivedGroup(db.Model):
    __tablename__ = 'archived_group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    archived_school_id = db.Column(db.Integer, db.ForeignKey('archived_school.id', ondelete='CASCADE'))


# Define the Group model
class Group(db.Model, UserMixin):
    __tablename__ = 'group'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # Field to identify admin groups
    
    # Add a passcode field for the group
    passcode = db.Column(db.String(10), nullable=False, unique=True)

    # Foreign key to associate the group with a school
    school_id = db.Column(db.Integer, db.ForeignKey('school.id', ondelete="CASCADE"), nullable=False)

    # Relationship with Users (students)
    members = db.relationship('User', backref='group', cascade='all, delete-orphan', passive_deletes=True)

    def __init__(self, name, school_id, passcode=None, is_admin=False):
        """Initialize a new group with a name, school_id, and optional passcode."""
        self.name = name
        self.school_id = school_id
        self.passcode = self.generate_passcode()  # Generate passcode when group is created

    def generate_passcode(self, length=8):
        """Generate a random alphanumeric passcode with uppercase letters and digits."""
        characters = string.ascii_uppercase + string.digits  # Uppercase letters and digits only
        return ''.join(random.choice(characters) for _ in range(length))

# Define the QuizResult model
class QuizResult(db.Model):
    __tablename__ = 'quiz_result'
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
    question_index = db.Column(db.Integer, nullable=False)
    answer = db.Column(db.String(100))
    result = db.Column(db.String(50))
    response_time = db.Column(db.Float)
    score = db.Column(db.Float)  # New column to store the calculated score
    school_id = db.Column(db.Integer, db.ForeignKey('school.id'), nullable=False)  # FIXED
    season = db.Column(db.Integer)  # just store the value, don’t foreign key it

    # Relationship with Group
    group = db.relationship('Group', backref='quiz_results', lazy=True)

    # Relationship to fetch the associated School
    school = db.relationship('School', backref='quiz_results', lazy=True)

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    allow_registration = db.Column(db.Boolean, default=True)
    allow_quiz = db.Column(db.Boolean, default=True)

# Define the Questions model
class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(255), nullable=True)  # Path to the uploaded image



"""from flask_migrate import Migrate
from extensions import app, db  # Ensure you import your app and db

migrate = Migrate(app, db)"""

# Create the database tables
with app.app_context():
    db.create_all()