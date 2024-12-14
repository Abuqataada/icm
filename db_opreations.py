from extensions import db, app
from sqlalchemy import text


# Adding admin user(s)
"""from app import db, app
from models import User

# Create a new admin user
with app.app_context():
    admin = User(
        fullname='Super Admin',
        is_admin=True,
        school_id=1,
        group_id=1
    )

    # Add and commit to the database
    db.session.add(admin)
    db.session.commit()

    print('Admin user created successfully!')"""



# Deleting all the quizresults data from the database
"""from app import db, app, QuizResult

# Delete all quiz result records
def delete_all_quiz_results():
    try:
        # Delete all records from the quiz_results table
        QuizResult.query.delete()
        
        # Commit the changes to the database
        db.session.commit()
        print("All quiz results have been deleted.")
    except Exception as e:
        db.session.rollback()  # Rollback in case of any error
        print(f"Error deleting quiz results: {e}")

# Call the function
with app.app_context():
    delete_all_quiz_results()"""







# Promote user to admin
"""
from app import db, User, app

# Replace with the email of the user you want to promote
user_email = 'abuqataada21@gmail.com'

with app.app_context():
    # Query the user by email
    user = User.query.filter_by(email=user_email).first()

    if user:
        user.is_admin = True  # Set the user as admin
        db.session.commit()  # Commit the changes
        print(f"{user_email} has been successfully set as an admin.")
    else:
        print(f"User with email {user_email} not found.")
"""














"""
def update_groups_passcodes():
    groups = Group.query.all()

    for group in groups:
        if not group.passcode:  # If the group doesn't have a passcode yet
            group.passcode = group.generate_passcode()
            db.session.add(group)

    db.session.commit()
    return "Passcodes have been generated for all groups."

with app.app_context():
    update_groups_passcodes()
"""


# Modify a table in the database
"""from extensions import db, app  # Adjust the import according to your structure
from sqlalchemy import text

class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    allow_registration = db.Column(db.Boolean, default=True)
    allow_quiz = db.Column(db.Boolean, default=True)

# Create the database tables
with app.app_context():
    # Drop the settings table
    db.session.execute(text('DROP TABLE IF EXISTS settings;'))
    db.session.commit()
    db.create_all()"""













#Alter the Settings Table (If You Prefer to Keep Existing Data)
"""from sqlalchemy import text

with app.app_context():
    #db.session.execute(text('CREATE TABLE new_settings (id INTEGER PRIMARY KEY, allow_registration BOOLEAN, allow_quiz BOOLEAN);'))
    #db.session.commit()

    #db.session.execute(text('INSERT INTO new_settings (id, allow_registration) SELECT id, allow_registration FROM settings;'))
    #db.session.commit()

    db.session.execute(text('DROP TABLE IF EXISTS new_settings;'))
    db.session.commit()

    #db.session.execute(text('ALTER TABLE new_settings RENAME TO settings;'))
    #db.session.commit()

    settings_columns = db.session.execute(text('PRAGMA table_info(settings);')).fetchall()
    for column in settings_columns:
        print(column)  # This will print all columns in the settings table"""








# Adding the is_admin column to the group model
"""from sqlalchemy import text

with app.app_context():
    # Step 1: Add the `is_admin` column with a default value of False
    db.session.execute(text('ALTER TABLE "group" ADD COLUMN is_admin BOOLEAN DEFAULT FALSE;'))
    db.session.commit()

    # Step 2: Verify the updated schema to ensure `is_admin` column was added
    group_columns = db.session.execute(text('PRAGMA table_info("group");')).fetchall()
    for column in group_columns:
        print(column)  # This will print all columns in the updated `group` table, including `is_admin`"""



# Adding the group_id and removing user_id column from the QuizResult model


"""with app.app_context():
    # Step 1: Add the `group_id` column with a foreign key constraint pointing to the `id` column in `group` table
    db.session.execute(text('ALTER TABLE quiz_result ADD COLUMN score FLOAT;'))
    #db.session.execute(text('ALTER TABLE quiz_result ADD CONSTRAINT fk_group_id FOREIGN KEY (group_id) REFERENCES "group"(id);'))
    
    # Step 2: Remove the `user_id` column from `quiz_result`
    #db.session.execute(text('CREATE TABLE quiz_result_temp AS SELECT id, group_id, question_index, answer, result, response_time FROM quiz_result;'))
    #db.session.execute(text('DROP TABLE quiz_result;'))
    #db.session.execute(text('ALTER TABLE quiz_result_temp RENAME TO quiz_result;'))

    db.session.commit()

    # Step 3: Verify the updated schema to ensure `group_id` was added and `user_id` was removed
    quiz_result_columns = db.session.execute(text('PRAGMA table_info("quiz_result");')).fetchall()
    for column in quiz_result_columns:
        print(column)
"""














# Adding the group_id and removing user_id column from the QuizResult model
"""with app.app_context():
    # Step 1: Add the `season` column  to the school table
    db.session.execute(text('ALTER TABLE quiz_result ADD COLUMN season INTEGER;'))
    #db.session.execute(text('ALTER TABLE quiz_result ADD CONSTRAINT fk_group_id FOREIGN KEY (group_id) REFERENCES "group"(id);'))
    
    # Step 2: Remove the `user_id` column from `quiz_result`
    #db.session.execute(text('CREATE TABLE quiz_result_temp AS SELECT id, group_id, question_index, answer, result, response_time FROM quiz_result;'))
    #db.session.execute(text('DROP TABLE quiz_result;'))
    #db.session.execute(text('ALTER TABLE quiz_result_temp RENAME TO quiz_result;'))

    db.session.commit()

    # Step 3: Verify the updated schema to ensure `group_id` was added and `user_id` was removed
    school_columns = db.session.execute(text('PRAGMA table_info("quiz_result");')).fetchall()
    for column in school_columns:
        print(column)"""




with app.app_context():
    db.session.execute(text('DROP TABLE IF EXISTS questions;'))
    #db.session.commit()
    #db.session.execute(text('CREATE TABLE questions (id INTEGER PRIMARY KEY AUTOINCREMENT, question_text TEXT NOT NULL, option_a TEXT NOT NULL, option_b TEXT NOT NULL, option_c TEXT NOT NULL, option_d TEXT NOT NULL, correct_answer INTEGER NOT NULL, image TEXT);'))
    db.session.commit()

