from flask import request, redirect, url_for, render_template, session, jsonify, flash, send_file
from extensions import db, app
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from models import Users, School, Settings, QuizResult, UserGroup, ArchivedSchool, Question
from flask_socketio import SocketIO, emit, disconnect
import json
from sqlalchemy.orm import aliased
from sqlalchemy import func
from flask_cors import CORS
import signal
import os
from werkzeug.utils import secure_filename
import random
import eventlet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pandas as pd
from datetime import datetime, timezone
import traceback
import uuid
import io




CORS(app)
eventlet.hubs.use_hub('selects')

# Initialize SocketIO
socketio = SocketIO(app, async_mode='eventlet')
admin_socket = None  # Initialize admin_socket globally
current_question_index = 0
DUMP_FOLDER = os.path.join(os.getcwd(), "db_dumps")
os.makedirs(DUMP_FOLDER, exist_ok=True)



# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'  # Redirect to login page if not logged in

@login_manager.user_loader
def load_user(user_id):
    # Updated method to get a record by ID
    with db.session() as session:
        group = session.get(UserGroup, int(user_id))
        return group




















#############################################################################
#############################PAGE REDIRECTIONS###############################
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")

@app.route('/start_quiz', methods=['GET'])
@login_required
def start_quiz():
    school_id = request.args.get('school_id')
    group_passcode = request.args.get('group_passcode')

    # Store the passcode in the session
    session['group_passcode'] = group_passcode
    session['school_id'] = school_id

    # Redirect to the game page
    return redirect(url_for('game'))

@app.route('/game', methods=['GET'])
@login_required
def game():
    school_id = session.get('school_id')
    group_passcode = session.get('group_passcode')

    # Now you can use school_id and group_passcode as needed
    school = School.query.filter_by(id=school_id).first()
    group = UserGroup.query.filter_by(school_id=school_id, passcode=group_passcode).first()
    settings = Settings.query.first()
    if not settings:
        flash("Quiz settings not configured", "danger")
        return redirect(url_for('index'))

    return render_template("game.html", school=school, group=group, quiz_duration=settings.quiz_duration)

@app.route('/admin_start_quiz', methods=['GET', 'POST'])
@login_required
def admin_start_quiz():
    # Get current quiz settings
    settings = Settings.query.first()
    if not settings:
        flash("Quiz settings not configured", "danger")
        return redirect(url_for('settings'))
    
    # Get questions based on current configuration
    questions = Question.query.filter_by(
        season=settings.current_season,
        subject=settings.current_subject
    ).limit(settings.question_count).all()
    
    if len(questions) < settings.question_count:
        flash(f"Warning: Only {len(questions)} questions available for the current configuration", "warning")
    
    # Convert questions to JSON format
    questions_list = []
    for question in questions:
        questions_list.append({
            "id": question.id,
            "question": question.question_text,
            "choice1": question.option_a,
            "choice2": question.option_b,
            "choice3": question.option_c,
            "choice4": question.option_d,
            "answer": question.correct_answer,
            "image": question.image
        })
    
    # Randomize the questions
    random.shuffle(questions_list)
    
    # Save to JSON file
    questions_json_path = os.path.join('static', 'questions', 'questions.json')
    os.makedirs(os.path.dirname(questions_json_path), exist_ok=True)
    
    try:
        with open(questions_json_path, 'w') as f:
            json.dump(questions_list, f)
    except Exception as e:
        flash(f"Error saving questions: {str(e)}", "danger")
        return redirect(url_for('settings'))
    
    # Pass quiz configuration to template
    return render_template(
        "admin_quiz_session.html",
        question_count=settings.question_count,
        current_season=settings.current_season,
        current_subject=settings.current_subject.title(),
        quiz_duration=settings.quiz_duration  # Keep as seconds
    )

@app.route('/highscores', methods=['GET', 'POST'])
@login_required
def highscores():
    return render_template("highscores.html")

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    # Check if registration is allowed
    settings = Settings.query.get(1)
    if not settings or not settings.allow_registration:
        flash('Registration is currently closed', 'danger')
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            fullname = request.form['fullname']
            school_id = request.form['school_id']
            group_id = request.form['group_id']
            
            # Validate inputs
            if not all([fullname, school_id, group_id]):
                flash('Please fill in all fields', 'danger')
                return redirect(url_for('index'))
            
            # Check if school and group exist and belong together
            school = School.query.get(school_id)
            group = UserGroup.query.filter_by(id=group_id, school_id=school_id).first()
            
            if not school or not group:
                flash('Invalid school or group selection', 'danger')
                return redirect(url_for('index'))
            
            # Check if group is already full (max 4 students)
            current_student_count = Users.query.filter_by(user_group_id=group_id).count()
            if current_student_count >= 4:
                flash('This group is already full (maximum 4 students)', 'danger')
                return redirect(url_for('index'))
            
            # Create new user
            new_user = Users(
                fullname=fullname,
                school_id=school_id,
                user_group_id=group_id
            )
            
            db.session.add(new_user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed: {str(e)}', 'danger')
            return redirect(url_for('index'))
    
    # For GET request, redirect to index (signup form is on index page)
    return redirect(url_for('index'))
    
@app.route('/home', methods=['GET', 'POST'])
def home():
    # Fetch the current setting
    # Fetch the current setting
    current_setting = db.session.query(Settings).filter_by(id=1).first()

    # Create a default if not found
    if not current_setting:
        current_setting = Settings(id=1, allow_registration=True, allow_quiz=True)
        db.session.add(current_setting)
        db.session.commit()
    allow_quiz = current_setting.allow_quiz

    school_id = request.form['school_id']
    group_passcode = request.form['group_passcode']

    # Check if the school exists
    school = School.query.filter_by(id=school_id).first()
    if not school:
        flash('No school found!')
        return render_template("index.html", error='Invalid school ID!')

    # Fetch the group that matches the passcode within the specified school
    group = UserGroup.query.filter_by(school_id=school.id, passcode=group_passcode).first()

    if group:
        # Get all members of the group
        group_members = group.users

        # Prepare the list of student names
        student_names = [member.fullname for member in group_members]

        # Store the group information in the session
        session['group_id'] = group.id
        session['school_id'] = school.id

        # If the group is an admin, redirect to admin.html
        if group.is_admin:
            login_user(group)  # Log in the actual group instance
            return redirect(url_for("admin_panel"))

        
        # For non-admin groups, render the regular home.html
        login_user(group)  # Log in the actual group instance
        return render_template("home.html", school=school, group=group, student_names=student_names, allow_quiz=allow_quiz)

    flash('Invalid group passcode!', 'danger')
    return render_template("index.html")

@app.route('/settings')
@login_required
def settings():
    # Get current settings or create default
    current_settings = Settings.query.get(1)
    if not current_settings:
        current_settings = Settings(
            allow_registration=True,
            allow_quiz=True,
            current_season=1,
            current_subject='math',
            question_count=10,
            quiz_duration=1800  # 30 minutes in seconds
        )
        db.session.add(current_settings)
        db.session.commit()
    
    # Prepare other data (users, etc.)
    users_with_schools = []
    users = Users.query.all()
    for user in users:
        school = School.query.get(user.school_id)
        group = UserGroup.query.get(user.user_group_id)
        users_with_schools.append({
            'id': user.id,
            'fullname': user.fullname,
            'school_name': school.name if school else 'N/A',
            'group_name': group.name if group else 'N/A'
        })
    
    return render_template(
        "settings.html",
        users=users_with_schools,
        allow_registration=current_settings.allow_registration,
        allow_quiz=current_settings.allow_quiz,
        current_season=current_settings.current_season,
        current_subject=current_settings.current_subject,
        question_count=current_settings.question_count,
        quiz_duration=current_settings.quiz_duration
    )

@app.route('/set-quiz-config', methods=['POST'])
def set_quiz_config():
    if request.method == 'POST':
        try:
            current_season = request.form.get('current_season')
            current_subject = request.form.get('current_subject')
            question_count = request.form.get('question_count')
            quiz_duration = request.form.get('quiz_duration')
            
            # Validate inputs
            if not all([current_season, current_subject, question_count, quiz_duration]):
                flash("Please fill in all required fields", "danger")
                return redirect(url_for('settings'))
            
            try:
                current_season = int(current_season)
                question_count = int(question_count)
                quiz_duration = int(quiz_duration)  # Keep as seconds
                
                if question_count <= 0:
                    flash("Number of questions must be at least 1", "danger")
                    return redirect(url_for('settings'))
                
                if quiz_duration <= 0:
                    flash("Quiz duration must be at least 1 second", "danger")
                    return redirect(url_for('settings'))
                
            except ValueError:
                flash("Invalid number format", "danger")
                return redirect(url_for('settings'))
            
            # Check if enough questions exist for this configuration
            available_questions = Question.query.filter_by(
                season=current_season,
                subject=current_subject
            ).count()
            
            if available_questions < question_count:
                flash(f"Only {available_questions} questions available for this configuration", "warning")
                #return redirect(url_for('settings'))
            
            # Get or create settings
            settings = Settings.query.get(1)
            if not settings:
                settings = Settings(
                    allow_registration=True,
                    allow_quiz=True,
                    current_season=current_season,
                    current_subject=current_subject,
                    question_count=question_count,
                    quiz_duration=quiz_duration
                )
                db.session.add(settings)
            else:
                settings.current_season = current_season
                settings.current_subject = current_subject
                settings.question_count = question_count
                settings.quiz_duration = quiz_duration
            
            db.session.commit()
            
            flash("Quiz configuration updated successfully", "success")
            return redirect(url_for('settings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error updating configuration: {str(e)}", "danger")
            return redirect(url_for('settings'))
        
@app.route('/admin', methods=['GET'])
@login_required
def admin_panel():
    # Fetch all schools along with the number of groups each school has
    schools = School.query.all()
    num_of_schools = len(schools)
    total_students_all_schools = 0  # Initialize total student count for all schools
    data = []
    
    # Create a list of dictionaries with school name, group count, total students, and groups with passcodes
    for school in schools:
        total_students = 0  # Initialize total student count for the school
        school_data = {
            'id': school.id,
            'name': school.name,
            'season': school.season,
            'groups': []
        }

        # Loop through groups to calculate total students
        for group in school.groups:
            student_count = len(group.users)  # Count the number of students in this group
            total_students += student_count  # Add to total student count for the school
            total_students_all_schools += student_count  # Add to total student count for all schools
            
            group_data = {
                'name': group.name,
                'passcode': group.passcode,
                'student_count': student_count,  # Add student count for the group
                'students': [{'name': student.fullname} for student in group.users]  # Fetch student names
            }
            school_data['groups'].append(group_data)

        # Add total student count and group count to school data
        school_data['group_count'] = len(school.groups)
        school_data['total_students'] = total_students  # Add total students for the school
        data.append(school_data)
    #print(data[0]['season'])
    
    return render_template('admin.html', schools=data, num_of_schools=num_of_schools, total_students_all_schools=total_students_all_schools)

@app.route('/results/<int:question_index>', methods=['GET'])
@login_required
def fetch_results(question_index):
    try:
        print(f"Fetching results for question index: {question_index}")
        
        # Define aliased models to avoid naming conflicts
        group_alias = aliased(UserGroup)
        school_alias = aliased(School)
        
        # Fetch quiz results for the specific question, ordered by response time
        results = db.session.query(
            group_alias.name.label('group_name'),
            school_alias.name.label('school_name'),
            QuizResult.answer,
            QuizResult.result,
            QuizResult.response_time,
            QuizResult.score
        ).outerjoin(group_alias, group_alias.id == QuizResult.user_group_id) \
         .outerjoin(school_alias, school_alias.id == group_alias.school_id) \
         .filter(QuizResult.question_index == question_index) \
         .order_by(QuizResult.response_time) \
         .all()
        
        print(f"Raw SQLAlchemy results: {results}")
        print(f"Number of results: {len(results)}")

        # Convert results to a list of dictionaries for JSON response
        results_list = []
        for r in results:
            result_dict = {
                'group_name': r.group_name,
                'school_name': r.school_name,
                'answer': r.answer,
                'result': r.result,
                'response_time': float(r.response_time) if r.response_time else 0,
                'score': float(r.score) if r.score else 0
            }
            results_list.append(result_dict)
            print(f"Processed result: {result_dict}")

        print(f"Final results_list: {results_list}")

        # Return the results with success status
        return jsonify({
            'success': True,
            'count': len(results_list),
            'results': results_list
        })
        
    except Exception as e:
        print(f"Error fetching results: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Error fetching quiz results.'
        }), 500
    
@app.route('/logout')
@login_required
def logout():
    #user_id = current_user.get_id()
    logout_user()
    return render_template("index.html")

@app.route('/archive', methods=['GET'])
@login_required
def archive():
    # Fetch all archived school records
    archived_schools = ArchivedSchool.query.all()
    
    # Extract details of each archived school
    schools_data = []
    for school in archived_schools:
        school_info = {
            'id': school.id,
            'name': school.name,
            'season': school.season,
            # Add other fields here if they exist in your model, e.g., 'location': school.location
        }
        schools_data.append(school_info)

    # Pass the structured data to the template
    return render_template('archive.html', archived_schools=schools_data)

@app.route('/checkresults')
@login_required
def checkresults():
    return render_template('checkresult.html')

@app.route('/questions_page', methods=['GET'])
@login_required
def questions_page():
    settings = Settings.query.first()
    current_season = settings.current_season if settings else 1
    current_subject = settings.current_subject if settings else 'math'
    questions = Question.query.order_by(Question.id.desc()).all()
    return render_template('add_questions.html', current_season=current_season, current_subject=current_subject, questions=questions)










































def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions































########################## ADMIN SETTINGS ###########################
#####################################################################
@app.route('/toggle-registration', methods=['POST'])
@login_required  # Add this decorator to protect the endpoint
def toggle_registration():
    if not current_user.is_admin:
        flash("Unauthorized: Only admins can modify settings", "danger")
        return redirect(url_for('index'))

    try:
        # Get or create settings record
        settings = Settings.query.get(1)
        if not settings:
            settings = Settings(
                id=1,
                allow_registration=True,
                allow_quiz=True
            )
            db.session.add(settings)
            db.session.commit()

        # Toggle the registration setting
        settings.allow_registration = not settings.allow_registration
        db.session.commit()

        flash(f"Registration is now {'open' if settings.allow_registration else 'closed'}", "success")
        return redirect(url_for('settings'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error while toggling registration: {str(e)}", "danger")
        return redirect(url_for('settings'))
    
@app.route('/toggle_quiz', methods=['POST'])
@login_required  # Ensure only logged-in users can access this route
def toggle_quiz():
    # Fetch the current setting
    current_setting = db.session.query(Settings).filter_by(id=1).first()

    # If no setting exists, create a default one
    if not current_setting:
        current_setting = Settings(allow_registration=True, allow_quiz=True)  # Set default values
        db.session.add(current_setting)
        db.session.commit()

    if request.method == 'POST':
        # Toggle the allow_quiz setting
        current_setting.allow_quiz = not current_setting.allow_quiz

        # Save the updated setting
        db.session.commit()

    return render_template("settings.html", allow_registration=current_setting.allow_registration, allow_quiz=current_setting.allow_quiz)  # Redirect to settings or wherever appropriate

@app.route('/delete-school/<int:id>', methods=['POST'])
@login_required
def delete_school(id):
    if current_user.is_admin:
        # Attempt to retrieve the school from the active School model
        school = School.query.get(id)
        
        # If the school is not found in the active model, check ArchivedSchool
        if not school:
            school = ArchivedSchool.query.get_or_404(id)

        # Access the correct group and student relationships depending on the model
        if isinstance(school, School):
            groups = school.groups
            students = school.users
        else:
            groups = school.archived_groups
            students = school.archived_users

        # Prevent deletion of Admin group
        if UserGroup.query.filter_by(school_id=school.id).first().is_admin:
            flash(f'Admin group cannot be deleted!', 'danger')
            return redirect(url_for('admin_panel'))
        
        # Delete students and groups associated with the school
        if students:
            for student in students:
                db.session.delete(student)  # Delete each student

        if groups:
            for group in groups:
                db.session.delete(group)  # Delete each group

        # Delete the school itself
        db.session.delete(school)
        
        # Commit the deletion
        db.session.commit()
        flash(f'School deleted successfully.', 'success')
    else:
        flash('Unauthorised action', 'danger')
    
    return redirect(url_for('admin_panel'))

@app.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    if current_user.is_admin: # Ensure only admin can perform this action
        # Fetch the current setting
        user = Users.query.get_or_404(user_id)
        try:
            # Prevent deletion of Admin user
            if user.is_admin:
                flash(f'You cannot delete a Super Admin!', 'info')
                return redirect(url_for('settings'))
            
            db.session.delete(user)
            db.session.commit()
            flash(f'Student {user.fullname.upper()} has been deleted sucessfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting student: {str(e)}', 'danger')
    else:
        flash('Unauthorised action', 'danger')
    return redirect(url_for('settings'))

@app.route('/add-school', methods=['POST'])
@login_required
def add_school():
    try:
        # Get school name and group count from the form
        school_name = request.form['schoolname']
        group_count = int(request.form['groupcount'])
        season = int(request.form['season'])

        # Create a new school WITHOUT specifying the ID
        new_school = School(name=school_name, season=season)
        db.session.add(new_school)
        db.session.commit()  # Commit to get the auto-generated school id

        # Create the specified number of groups for the school
        for i in range(1, group_count + 1):
            group_name = f"Group {i}"
            new_group = UserGroup(name=group_name, school_id=new_school.id)
            db.session.add(new_group)

        db.session.commit()  # Commit groups to the database

        flash(f"School '{school_name}' and groups added successfully.", 'success')
        return redirect(url_for('settings'))
    except Exception as e:
        flash(f"Error adding school and groups: {str(e)}")
        print(f"Error adding school and groups: {str(e)}")
        return redirect(url_for('settings'))
        
# For login (includes all schools)
@app.route('/get-all-schools')
def get_all_schools():
    try:
        schools = School.query.all()
        return jsonify({
            'schools': [{'id': school.id, 'name': school.name} for school in schools]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# For signup (excludes admin school)
@app.route('/get-regular-schools')
def get_regular_schools():
    try:
        schools = School.query.filter(School.id != 1).all()  # Exclude school with id=1
        return jsonify({
            'schools': [{'id': school.id, 'name': school.name} for school in schools]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_groups/<int:school_id>', methods=['GET'])
def get_groups(school_id):
    groups = UserGroup.query.filter_by(school_id=school_id).all()
    group_list = [{
        'id': group.id,
        'name': group.name,
        'student_count': len(group.users)} for group in groups]
    
    return jsonify(group_list)

@app.route('/archive_school/<int:school_id>', methods=['POST'])
def archive_school(school_id):
    school = School.query.get(school_id)
    if not school:
        flash("School not found!", "error")
        return redirect(url_for('admin_panel'))

    try:
        if UserGroup.query.filter_by(school_id=school.id).first().is_admin:
            flash("You cannot archive Admin School!", "info")
        else:
            school.archive()
            flash("School successfully archived!", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while archiving the school.", "error")
    
    return redirect(url_for('admin_panel'))

# Route for adding questions
@app.route('/add-question', methods=['GET', 'POST'])
def add_question():
    # Get current quiz configuration
    current_settings = Settings.query.first()
    
    if not current_settings:
        flash("Quiz configuration not set. Please configure quiz settings first.", "danger")
        return redirect(url_for('settings'))

    if request.method == 'POST':
        try:
            # Get form data
            question_text = request.form.get('question_text', '').strip()
            option_a = request.form.get('option_a', '').strip()
            option_b = request.form.get('option_b', '').strip()
            option_c = request.form.get('option_c', '').strip()
            option_d = request.form.get('option_d', '').strip()
            correct_answer = request.form.get('correct_answer')
            image = request.files.get('image')
            
            # Validate required fields
            if not all([question_text, option_a, option_b, option_c, option_d, correct_answer]):
                flash("Please fill in all required fields", "danger")
                return redirect(url_for('add_question'))
            
            # Validate question text length
            if len(question_text) > 1000:
                flash("Question text is too long (max 1000 characters)", "danger")
                return redirect(url_for('add_question'))
            
            # Validate options length
            for option in [option_a, option_b, option_c, option_d]:
                if len(option) > 255:
                    flash("Option text is too long (max 255 characters)", "danger")
                    return redirect(url_for('add_question'))
            
            # Convert and validate correct answer
            try:
                correct_answer = int(correct_answer)
                if correct_answer not in [1, 2, 3, 4]:
                    raise ValueError
            except ValueError:
                flash("Invalid correct answer selection", "danger")
                return redirect(url_for('add_question'))
            
            # Handle image upload if present
            image = None
            if image:
                if not allowed_file(image.filename):
                    flash("Invalid image file type. Allowed: png, jpg, jpeg, gif", "danger")
                    return redirect(url_for('add_question'))
                
                if image.content_length > 4 * 1024 * 1024:  # 4MB limit
                    flash("Image file is too large (max 4MB)", "danger")
                    return redirect(url_for('add_question'))
                
                filename = secure_filename(image.filename)
                image = f"{uuid.uuid4().hex}_{filename}"
                try:
                    image.save(os.path.join(app.config['UPLOAD_FOLDER'], image))
                except Exception as e:
                    flash(f"Failed to save image: {str(e)}", "danger")
                    return redirect(url_for('add_question'))
            
            # Create new question with current season and subject from settings
            new_question = Question(
                question_text=question_text,
                option_a=option_a,
                option_b=option_b,
                option_c=option_c,
                option_d=option_d,
                correct_answer=correct_answer,
                image=image,
                season=current_settings.current_season,
                subject=current_settings.current_subject,
                created_at=datetime.now(timezone.utc)
            )
            
            db.session.add(new_question)
            db.session.commit()
            
            flash("Question added successfully!", "success")
            return redirect(url_for('add_question'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding question: {str(e)}", "danger")
            return redirect(url_for('add_question'))
    
    # For GET requests, show form with current configuration
    return redirect(url_for('questions_page'))

@app.route('/bulk_upload_questions', methods=['POST'])
def bulk_upload_questions():
    if 'excel_file' not in request.files:
        flash('No file uploaded', 'danger')
        return redirect(url_for('add_question'))
    
    file = request.files['excel_file']
    if file.filename == '':
        flash('No file selected', 'danger')
        return redirect(url_for('add_question'))
    
    # Check if file is allowed
    def allowed_file(filename, allowed_extensions):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
    
    if file and allowed_file(file.filename, {'xlsx', 'xls'}):
        try:
            # Read the Excel file
            df = pd.read_excel(file)
            
            # Validate required columns
            required_columns = ['Question Text', 'Option A', 'Option B', 'Option C', 'Option D', 'Correct Answer']
            if not all(col in df.columns for col in required_columns):
                flash('Excel file missing required columns. Please use the template.', 'danger')
                return redirect(url_for('add_question'))
            
            success_count = 0
            error_rows = []
            
            # Get current season and subject from session or form
            # You might need to adjust this based on how you're storing these values
            current_settings = Settings.query.first()
            if current_settings:
                current_season = current_settings.current_season
                current_subject = current_settings.current_subject
            else:
                current_season = 1  # Default to 1 if not set
                current_subject = 'General'  # Default to 'General' if not set

            # Process each row
            for index, row in df.iterrows():
                row_num = index + 2  # +2 because Excel rows start at 1 and we have header row
                
                # Validate row data
                question_text = str(row['Question Text']).strip()
                option_a = str(row['Option A']).strip()
                option_b = str(row['Option B']).strip()
                option_c = str(row['Option C']).strip()
                option_d = str(row['Option D']).strip()
                correct_answer = str(row['Correct Answer']).strip().upper()
                
                # Skip empty rows
                if not question_text:
                    continue
                
                # Validate required fields
                errors = []
                if not question_text:
                    errors.append('Question text is required')
                if not option_a:
                    errors.append('Option A is required')
                if not option_b:
                    errors.append('Option B is required')
                if not option_c:
                    errors.append('Option C is required')
                if not option_d:
                    errors.append('Option D is required')
                if not correct_answer:
                    errors.append('Correct answer is required')
                elif correct_answer not in ['A', 'B', 'C', 'D']:
                    errors.append('Correct answer must be A, B, C, or D')
                
                if errors:
                    error_rows.append(f"Row {row_num}: {', '.join(errors)}")
                    continue
                
                # Map correct answer to numeric value
                correct_answer_map = {'A': 1, 'B': 2, 'C': 3, 'D': 4}
                correct_answer_num = correct_answer_map[correct_answer]
                
                try:
                    # Create new question using SQLAlchemy
                    new_question = Question(
                        question_text=question_text,
                        option_a=option_a,
                        option_b=option_b,
                        option_c=option_c,
                        option_d=option_d,
                        correct_answer=correct_answer_num,
                        season=current_season,
                        subject=current_subject,
                        created_at=datetime.now(timezone.utc)
                    )
                    
                    db.session.add(new_question)
                    db.session.commit()
                    success_count += 1
                    
                except Exception as db_error:
                    db.session.rollback()
                    error_rows.append(f"Row {row_num}: Database error - {str(db_error)}")
            
            # Prepare flash messages
            if success_count > 0:
                flash(f'Successfully uploaded {success_count} questions', 'success')
            
            if error_rows:
                error_msg = f'{len(error_rows)} rows had errors. First few: ' + '; '.join(error_rows[:3])
                if len(error_rows) > 3:
                    error_msg += f'... and {len(error_rows) - 3} more'
                flash(error_msg, 'warning')
                
        except Exception as e:
            flash(f'Error processing file: {str(e)}', 'danger')
    else:
        flash('Invalid file type. Please upload an Excel file (.xlsx or .xls)', 'danger')
    
    return redirect(url_for('add_question'))

@app.route('/download_template')
def download_template():
    # Create a sample DataFrame with instructions
    data = {
        'Question Text': ['What is 2+2?', 'Capital of France?', 'Chemical symbol for gold'],
        'Option A': ['3', 'London', 'Ag'],
        'Option B': ['4', 'Berlin', 'Fe'],
        'Option C': ['5', 'Madrid', 'Au'],
        'Option D': ['6', 'Paris', 'Pb'],
        'Correct Answer': ['B', 'D', 'C']
    }
    
    df = pd.DataFrame(data)
    
    # Create instructions sheet
    instructions_data = {
        'Column': ['Question Text', 'Option A', 'Option B', 'Option C', 'Option D', 'Correct Answer'],
        'Description': [
            'The question text (required)',
            'First answer option (required)',
            'Second answer option (required)',
            'Third answer option (required)',
            'Fourth answer option (required)',
            'Correct answer (A, B, C, or D, case insensitive)'
        ]
    }
    
    instructions_df = pd.DataFrame(instructions_data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Example Questions', index=False)
        instructions_df.to_excel(writer, sheet_name='Instructions', index=False)
        
        # Get workbook and worksheet objects for formatting
        workbook = writer.book
        worksheet = writer.sheets['Example Questions']
        
        # Add some formatting
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })
        
        # Apply header format
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
        
        # Adjust column widths
        worksheet.set_column('A:A', 30)  # Question Text
        worksheet.set_column('B:E', 20)  # Options
        worksheet.set_column('F:F', 15)  # Correct Answer
    
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='question_upload_template.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

# ---------- inline edit ----------
@app.route('/<int:q_id>/edit-question', methods=['GET', 'POST'])
def edit_question(q_id):
    q = Question.query.get_or_404(q_id)
    if request.method == 'POST':
        q.question_text = request.form['question_text']
        q.option_a = request.form['option_a']
        q.option_b = request.form['option_b']
        q.option_c = request.form['option_c']
        q.option_d = request.form['option_d']
        q.correct_answer = int(request.form['correct_answer'])
        db.session.commit()
        flash('Question updated.', 'success')
        return redirect(url_for('questions_page'))
    return render_template('edit_question.html', q=q)

# ---------- delete ----------
@app.route('/<int:q_id>/delete-question', methods=['POST'])
def delete_question(q_id):
    q = Question.query.get_or_404(q_id)
    db.session.delete(q)
    db.session.commit()
    flash('Question deleted.', 'info')
    return redirect(url_for('questions.table'))

@app.route('/generate_questions_json', methods=['POST'])
@login_required
def generate_questions_json():
    # Get the number of questions from the form
    num_questions = int(request.form.get('num_questions', 0))

    # Fetch all questions from the database using SQLAlchemy
    questions = Question.query.all()

    # Map database rows to dictionaries
    questions_list = [
        {
            "id": question.id,
            "question": question.question_text,
            "choice1": question.option_a,
            "choice2": question.option_b,
            "choice3": question.option_c,
            "choice4": question.option_d,
            "answer": question.correct_answer,
            "image": question.image
        }
        for question in questions
    ]

    # Randomly shuffle the questions
    random.shuffle(questions_list)

    # Limit the number of questions to the specified amount
    questions_list = questions_list[:num_questions]

    # Save the questions to a JSON file
    with open('static/questions/questions.json', 'w') as json_file:
        json.dump(questions_list, json_file)

    flash(f'{num_questions} quiz questions generated successfully!', 'success')
    return render_template("admin_quiz_session.html")


@app.route('/download-data')
@login_required
def download_data():
    """Show download confirmation page with preview of incoming data"""
    try:
        remote_engine = create_engine(app.config['SQLALCHEMY_BINDS']['remote'])
        
        preview_data = {}
        
        with remote_engine.connect() as conn:
            # Get counts of records that will be downloaded
            tables = ['school', 'user_group', 'user']

            for table in tables:
                count = pd.read_sql(f"SELECT COUNT(*) FROM {table}", conn).iloc[0,0]
                
                # For school table, exclude admin school (id=1)
                if table == 'school':
                    count = pd.read_sql(
                        "SELECT COUNT(*) FROM school WHERE id != 1", 
                        conn
                    ).iloc[0,0]
                
                # Get sample records (first 3)
                sample = pd.read_sql(
                    f"SELECT * FROM {table} {'WHERE id != 1' if table == 'school' else ''} LIMIT 3",
                    conn
                ).to_dict('records')
                
                preview_data[table] = {
                    'count': count,
                    'sample': sample
                }
        
        return render_template(
            'download_confirmation.html',
            preview_data=preview_data
        )
        
    except Exception as e:
        print(f"Error fetching preview data: {str(e)}")
        flash(f"Could not fetch preview data: {str(e)}", "danger")
        return redirect(url_for('admin_panel'))
    

@app.route('/process-download', methods=['POST'])
@login_required
def process_download():
    """Handle the actual data download from remote to local"""
    try:
        # Create database connections
        remote_engine = create_engine(app.config['SQLALCHEMY_BINDS']['remote'])
        local_engine = create_engine(app.config['SQLALCHEMY_BINDS']['local'])
        
        # Tables needed for offline quiz
        tables = ['school', 'user_group', 'users', 'quiz', 'questions']
        
        results = {}
        
        with remote_engine.connect() as remote_conn, local_engine.connect() as local_conn:
            for table in tables:
                try:
                    # Read from remote
                    df = pd.read_sql_table(table, remote_conn)
                    
                    if df.empty:
                        results[table] = {'status': 'skipped', 'reason': 'empty'}
                        continue
                        
                    # Special handling for school table (preserve admin school)
                    if table == 'school':
                        # Delete all schools except admin (id=1) from local
                        local_conn.execute(f"DELETE FROM {table} WHERE id != 1")
                        # Filter out admin school from download
                        df = df[df['id'] != 1]
                    else:
                        # Clear local table completely
                        local_conn.execute(f"DELETE FROM {table}")
                    
                    # Write to local SQLite in instance folder
                    if not df.empty:
                        df.to_sql(
                            table,
                            local_conn,
                            if_exists='append',
                            index=False,
                            method='multi'
                        )
                    
                    results[table] = {
                        'status': 'success',
                        'rows': len(df)
                    }
                    
                except Exception as e:
                    results[table] = {
                        'status': 'failed',
                        'error': str(e)
                    }
                    continue
        
        # Prepare success message
        success_tables = [t for t in results if results[t]['status'] == 'success']
        failed_tables = [t for t in results if results[t]['status'] == 'failed']
        
        if failed_tables:
            flash(
                f"Download completed with {len(success_tables)} successful tables. "
                f"Failed tables: {', '.join(failed_tables)}",
                "warning"
            )
        else:
            flash(
                f"Successfully downloaded {len(success_tables)} tables",
                "success"
            )
            
        return redirect(url_for('admin_panel'))
        
    except Exception as e:
        flash(f"Download failed: {str(e)}", "danger")
        return redirect(url_for('admin_panel'))



@app.route('/upload-data')
@login_required
def upload_data():
    """Show upload confirmation page with stats"""
    try:
        # Connect to local SQLite database in instance folder
        local_engine = create_engine(app.config['SQLALCHEMY_BINDS']['local'])
        
        with local_engine.connect() as conn:
            # Count new schools available for upload
            new_schools_count = pd.read_sql(
                "SELECT COUNT(*) FROM school WHERE id != 1 AND NOT EXISTS ("
                "SELECT 1 FROM remote.school WHERE remote.school.id = school.id"
                ")", 
                conn
            ).iloc[0,0]
            
        return render_template(
            'upload_confirmation.html',
            new_schools_count=new_schools_count
        )
        
    except Exception as e:
        flash(f"Could not check upload data: {str(e)}", "danger")
        return redirect(url_for('admin_panel'))

@app.route('/process-upload', methods=['POST'])
@login_required
def process_upload():
    """Handle the actual data upload"""
    try:
        # Create engines using the binds configuration
        local_engine = create_engine(app.config['SQLALCHEMY_BINDS']['local'])
        remote_engine = create_engine(app.config['SQLALCHEMY_BINDS']['remote'])
        
        with local_engine.connect() as local_conn, remote_engine.connect() as remote_conn:
            # Get only new schools that don't exist in remote
            new_schools = pd.read_sql(
                "SELECT * FROM school WHERE id != 1 AND NOT EXISTS ("
                "SELECT 1 FROM remote.school WHERE remote.school.id = school.id"
                ")",
                local_conn
            )
            
            if new_schools.empty:
                flash("No new schools to upload", "info")
                return redirect(url_for('admin_panel'))
            
            # Upload to remote
            new_schools.to_sql(
                'school',
                remote_conn,
                if_exists='append',
                index=False
            )
            
            flash(f"Successfully uploaded {len(new_schools)} new school(s)", "success")
            return redirect(url_for('admin_panel'))
            
    except Exception as e:
        flash(f"Upload failed: {str(e)}", "danger")
        return redirect(url_for('admin_panel'))

@app.route('/configure-quiz', methods=['POST'])
def configure_quiz():
    if request.method == 'POST':
        try:
            # Get form data
            season = request.form.get('quiz_season')
            subject = request.form.get('quiz_subject')
            question_count = request.form.get('question_count')
            
            # Validate inputs
            if not all([season, subject, question_count]):
                flash("Please fill in all required fields", "danger")
                return redirect(url_for('settings'))
            
            # Convert to integers
            try:
                season = int(season)
                question_count = int(question_count)
            except ValueError:
                flash("Invalid season or question count format", "danger")
                return redirect(url_for('settings'))
            
            # Check if questions exist for this season and subject
            question_count_available = Question.query.filter_by(
                season=season,
                subject=subject.lower()
            ).count()
            
            if question_count_available < question_count:
                flash(f"Only {question_count_available} questions available for {subject.title()} in Season {season}", "warning")
                return redirect(url_for('settings'))
            
            # Get or create settings
            settings = Settings.query.get(1)
            if not settings:
                settings = Settings(
                    allow_registration=True,
                    allow_quiz=True,
                    current_season=season,
                    current_subject=subject,
                    question_count=question_count
                )
                db.session.add(settings)
            else:
                settings.current_season = season
                settings.current_subject = subject
                settings.question_count = question_count
            
            db.session.commit()
            
            flash(f"Quiz configured: Season {season}, {subject.title()} with {question_count} questions", "success")
            return redirect(url_for('settings'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Error configuring quiz: {str(e)}", "danger")
            return redirect(url_for('settings'))






























############## UTILITY FUNCTIONS #################
##################################################
def calculate_score(base_score, time_taken, time_limit):
    # Calculate the maximum time threshold for full points (10% of time limit)
    full_score_threshold = time_limit * 0.1

    # If answered within 40% of the time, give full score
    if time_taken <= full_score_threshold:
        return round(base_score, 2)  # Round to 2 decimal places

    # Otherwise, calculate score based on time taken
    score = base_score * (1 - (time_taken / time_limit))

    # Ensure score does not go below zero
    return round(max(0, score), 2)

#export data from DB to txt
def export_database_to_txt(output_file="database_dump.txt"):
    with open(output_file, "w", encoding="utf-8") as f:
        for model in [Users, School, UserGroup]:  # Add all models you want
            f.write(f"--- {model.__name__} ---\n")
            records = model.query.all()
            if not records:
                f.write("No records found.\n\n")
                continue

            for record in records:
                f.write(", ".join(
                    [f"{k}={v}" for k, v in record.__dict__.items() if not k.startswith("_")]
                ) + "\n")
            f.write("\n")
    return output_file

@app.route("/update-group", methods=["POST"])
def update_group():
    group = UserGroup.query.filter_by(passcode="EEAS5I00").first()
    if group:
        group.passcode = "1234ABCD"
        group.is_admin = True
        db.session.commit()
        return "Group updated successfully."
    return "Group not found."

@app.route("/download-database")
def download_database():
    with app.app_context():
        file_path = export_database_to_txt()
        return send_file(file_path, as_attachment=True)




















##############  SOCKET CONNECTIONS  ##############
##################################################
connected_clients = {}
current_question_index = 0
connected_groups_count = 0

def load_questions():
    try:
        with open('static/questions/questions.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        flash("Questions file not found.")
        return []
    except json.JSONDecodeError:
        flash("Error decoding JSON from questions file.")
        return []

@socketio.on('connect')
def handle_connect():
    global admin_socket
    global connected_groups_count
    flash("A Group has made a connection")

    # Check if group is logged in
    if 'group_id' in session:
        group_id = session['group_id']
        school_id = session['school_id']
        
        # Retrieve group details from the database
        group = UserGroup.query.filter_by(id=group_id, school_id=school_id).first()
        if group:
            # Store group information based on socket session ID
            connected_clients[request.sid] = {
                'group_id': group_id,
                'group_name': f"Group {group_id} in School {school_id}",
                'school_id': school_id,
                'is_admin': group.is_admin  # Ensure this is set correctly
            }

            # Update connected groups count
            connected_groups_count += 1
            #print("Connected Groups Count:", connected_groups_count)
            #print("Connected Clients:", connected_clients)

            # If this is the admin, set the admin_socket
            if group.is_admin:
                if admin_socket:
                    # If an admin is already connected, reject the new one
                    emit('message', 'Another admin is already connected.', room=request.sid)
                    disconnect()  # Disconnect this new admin
                else:
                    # Set this as the admin connection
                    admin_socket = request.sid
                    emit('update_client_count', (connected_groups_count - 1), broadcast=True)
                    #print(f"Admin Group {group_id} connected.")
            else:
                emit('update_client_count', (connected_groups_count - 1), broadcast=True)
                #print(f"Group {group_id} connected.")

        else:
            flash("Unauthorized group connection attempt.")
            disconnect()  # Disconnect if group not found
    else:
        #print("No group ID in session. Disconnecting.")
        disconnect()  # Disconnect if not logged in as a group

@socketio.on('disconnect')
def handle_disconnect():
    global admin_socket
    global connected_groups_count

    if request.sid in connected_clients:
        group_info = connected_clients.pop(request.sid)
        connected_groups_count -= 1

        if group_info['group_id'] == session.get('group_id') and group_info.get('is_admin', False):
            # Reset admin_socket if admin disconnects
            admin_socket = None
            #print(f"Admin Group {group_info['group_id']} disconnected.")
        else:
            flash(f"Group {group_info['group_id']} disconnected.")
        
        # Notify others about the updated client count
        emit('update_client_count', (connected_groups_count - 1), broadcast=True)

@socketio.on('submit_answer')
def handle_submit_answer(data):
    group_info = connected_clients.get(request.sid)
    questions = load_questions()  # Load questions from JSON file

    if group_info:
        user_group_id = group_info['group_id']
        answer = data.get('answer')  # This is expected to be "A", "B", "C", or "D"
        question_index = data.get('question_index')
        response_time = data.get('response_time', 0)

        # Validate response_time and question_index
        if not isinstance(response_time, (int, float)):
            response_time = 0
        if question_index is None or not (0 <= question_index < len(questions)):
            return  # Invalid question index

        # Retrieve the group and associated school name
        group = UserGroup.query.get(user_group_id)
        school_name = group.school.name if group and group.school else "Unknown School"  # Get school name or default

        # Get the correct answer's letter by mapping letters to choices
        question_data = questions[question_index]
        # Get the correct answer's index (1-4)
        correct_answer_index = question_data['answer']  # This is an integer (1-4)
        letter_to_choice = {
            'A': question_data['choice1'],
            'B': question_data['choice2'],
            'C': question_data['choice3'],
            'D': question_data['choice4']
        }

        # Mapping integers to corresponding choice letters
        index_to_letter = {
            1: 'A',  # choice1
            2: 'B',  # choice2
            3: 'C',  # choice3
            4: 'D'   # choice4
        }

        # Get the corresponding letter for the correct answer
        correct_answer_letter = index_to_letter.get(correct_answer_index)

        # Determine if the answer is correct
        selected_answer_value = letter_to_choice.get(answer)  # Get the choice value based on letter
        # Determine the result
        result = (
            'correct' if selected_answer_value == question_data[f'choice{correct_answer_index}'] else
            'time up' if answer == 0 else
            'incorrect'
        )

        time_limit = 45  # Define time limit per question in seconds
        base_score = 5  # Define base score for each question
        if result == 'correct':
            score = calculate_score(base_score, response_time, time_limit)
        else:
            score = 0

        # Save the result in the database
        quiz_result = QuizResult(
            user_group_id=user_group_id,
            question_index=question_index,
            answer=answer,  # Store the letter choice ("A", "B", "C", or "D")
            result=result,
            response_time=response_time,
            score=score,  # Store the calculated score
            school_id=group.school_id,
            season=1
        )
        db.session.add(quiz_result)
        db.session.commit()

        # Emit result to admin and to the group
        if admin_socket:
            #print('message sent to the admin')
            emit('message', f'{school_name} ({group.name}) choose {answer} ({result}) in {response_time}s.', room=admin_socket)
        emit('answer_result', {'correct_answer': correct_answer_letter, 'response_time': response_time}, room=request.sid)
    else:
        flash("Group not found in connected clients.")

@socketio.on('fetch_total_group_results')
def handle_fetch_total_group_results():
    try:
        # Define aliased models to avoid naming conflicts
        group_alias = aliased(UserGroup)
        school_alias = aliased(School)
        
        # Calculate total scores and response times for each group
        results = db.session.query(
            group_alias.name.label('group_name'),
            school_alias.name.label('school_name'),
            func.sum(QuizResult.score).label('total_score'),
            func.sum(QuizResult.response_time).label('total_response_time')
        ).outerjoin(group_alias, group_alias.id == QuizResult.group_id) \
         .outerjoin(school_alias, school_alias.id == group_alias.school_id) \
         .group_by(group_alias.name, school_alias.name) \
         .order_by(func.sum(QuizResult.score).desc(), func.sum(QuizResult.response_time).asc()) \
         .all()

        # Format the results
        formatted_results = []
        for result in results:
            formatted_results.append({
                'group_name': result.group_name,
                'school_name': result.school_name,
                'total_score': round(result.total_score, 2),
                'total_response_time': round(result.total_response_time, 2)
            })

        # Send the sorted results back to the client
        emit('display_total_group_results', formatted_results, room=request.sid)
    except Exception as e:
        #print('Error fetching total group results:', e)
        emit('message', 'Error fetching total group results.', room=request.sid)

@socketio.on('restart_quiz')
def handle_restart_quiz():
    global current_question_index
    current_question_index = 0  # Reset the question index

    try:
        # Get the highest season number from the School model
        highest_season = db.session.query(db.func.max(School.season)).scalar()

        if highest_season is not None:
            # Delete all quiz results for that season
            db.session.query(QuizResult).filter(QuizResult.season == highest_season).delete()
            db.session.commit()  # Commit the changes
            flash(f'Deleted quiz results for season {highest_season}.')
        else:
            flash('No seasons found in the database.')

        # Emit event to reset the question and choices
        #emit('new_question', {'question': '', 'choices': ['', '', '', '']}, broadcast=True)
        emit('new_question', {'question': '', 'choices': {'A': '', 'B': '', 'C': '', 'D': ''}, 'index': current_question_index - 1}, broadcast=True)
        
        # Emit event to clear the messages div on the client side
        emit('clear_messages', broadcast=True)

    except Exception as e:
        flash(f'Error during restart quiz: {str(e)}')
        # You might want to emit an error message back to the client
        emit('error_message', {'error': 'Failed to restart the quiz.'}, broadcast=True)

    
@socketio.on('next_question')
def handle_next_question():
    global current_question_index
    questions = load_questions()  # Load questions from JSON file

    try:
        client_info = connected_clients.get(request.sid)
        #print('Client Info: ', client_info)
        if client_info and client_info.get('is_admin') and current_question_index < len(questions):
            question_data = questions[current_question_index]
            
            # Structure the choices as letters with their corresponding options
            choices = {
                'A': question_data['choice1'],
                'B': question_data['choice2'],
                'C': question_data['choice3'],
                'D': question_data['choice4']
            }
            
            question = {
                'question': question_data['question'],
                'choices': choices,
                'answer': question_data['answer'],  # Keep this as the value, assuming it's needed for validation
                'image': question_data['image'],
                'is_admin': client_info['is_admin']  # Include admin flag
            }
            question['index'] = current_question_index

            # Reset the 'answered' flag for all connected clients
            for client in connected_clients.values():
                client['answered'] = False

            # Emit the question with choices labeled as A, B, C, D
            emit('new_question', question, broadcast=True)
            # Emit event to clear the messages div on the client side
            emit('clear_messages', broadcast=True)
            current_question_index += 1
        else:
            emit('message', 'End of quiz.', broadcast=True)
    except Exception as e:
        flash(f"Error in next_question: {str(e)}")
        emit('message', 'An error occurred while loading the next question.', room=request.sid)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    os.kill(os.getpid(), signal.SIGINT)  # Sends an interrupt signal to terminate the process
    return "Server shutting down..."


if __name__ == '__main__':
    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    print("Starting server with Eventlet...")
    socketio.run(app, debug=True)
