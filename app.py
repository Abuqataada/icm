from flask import request, redirect, url_for, render_template, session, jsonify, flash
from extensions import db, app
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from models import User, School, Settings, QuizResult, Group, ArchivedSchool, Question
from flask_socketio import SocketIO, emit, disconnect
import json
from sqlalchemy.orm import aliased, sessionmaker
from sqlalchemy import func, create_engine
from flask_cors import CORS
import signal
import os
from werkzeug.utils import secure_filename
import random
import eventlet

# Adjust the URI to match your Aiven DB credentials
AIVEN_DB_URI = os.getenv("ICM_DB_URI")

aiven_engine = create_engine(AIVEN_DB_URI)
AivenSession = sessionmaker(bind=aiven_engine)


CORS(app)
eventlet.hubs.use_hub('selects')

# Initialize SocketIO
socketio = SocketIO(app, async_mode='eventlet')
admin_socket = None  # Initialize admin_socket globally
current_question_index = 0



# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'index'  # Redirect to login page if not logged in

@login_manager.user_loader
def load_user(user_id):
    # Updated method to get a record by ID
    with db.session() as session:
        group = session.get(Group, int(user_id))
        return group




















#############################################################################
#############################PAGE REDIRECTIONS###############################
@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template("index.html")

@app.route('/start_quiz', methods=['GET'])
def start_quiz():
    school_id = request.args.get('school_id')
    group_passcode = request.args.get('group_passcode')

    # Store the passcode in the session
    session['group_passcode'] = group_passcode
    session['school_id'] = school_id

    # Redirect to the game page
    return redirect(url_for('game'))

@app.route('/game', methods=['GET'])
def game():
    school_id = session.get('school_id')
    group_passcode = session.get('group_passcode')

    # Now you can use school_id and group_passcode as needed
    school = School.query.filter_by(id=school_id).first()
    group = Group.query.filter_by(school_id=school_id, passcode=group_passcode).first()

    return render_template("game.html", school=school, group=group)

@app.route('/admin_start_quiz', methods=['GET', 'POST'])
def admin_start_quiz():
    return render_template("admin_quiz_session.html")

@app.route('/highscores', methods=['GET', 'POST'])
def highscores():
    return render_template("highscores.html")

@app.route('/home', methods=['GET', 'POST'])
def home():
    # Fetch the current setting
    current_setting = db.session.query(Settings).filter_by(id=1).first()
    allow_quiz = current_setting.allow_quiz

    school_id = request.form['school_id']
    group_passcode = request.form['group_passcode']

    # Check if the school exists
    school = School.query.filter_by(id=school_id).first()
    if not school:
        flash('No school found!')
        return render_template("index.html", error='Invalid school ID!')

    # Fetch the group that matches the passcode within the specified school
    group = Group.query.filter_by(school_id=school_id, passcode=group_passcode).first()

    if group:
        # Get all members of the group
        group_members = group.members

        # Prepare the list of student names
        student_names = [member.fullname for member in group_members]

        # Store the group information in the session
        session['group_id'] = group.id
        session['school_id'] = school_id

        # If the group is an admin, redirect to admin.html
        if group.is_admin:
            login_user(group)  # Log in the actual group instance
            return redirect(url_for("admin_panel"))

        
        # For non-admin groups, render the regular home.html
        return render_template("home.html", school=school, group=group, student_names=student_names, allow_quiz=allow_quiz)

    flash('Invalid group passcode!', 'danger')
    return render_template("index.html")

@app.route('/signup', methods=['POST'])
def signup():
    try:
        # Fetch the current registration setting
        current_setting = db.session.query(Settings).filter_by(id=1).first()

        # Check if registration is enabled
        if not current_setting or not current_setting.allow_registration:
            return 'Registration has closed for this programme. Please try again later.', 403

        fullname = request.form['fullname'].strip().lower()
        school_id = request.form['school_id']
        group_id = request.form['group_id']  # Group selection during signup

        # Check if the selected group has less than 4 users
        group = Group.query.filter_by(id=group_id).first()
        if len(group.members) >= 4:
            return 'The selected group already has 4 members. Please select another group.', 400

        if school_id == '5':
            flash('Only a super admin can register another admin. Please select another school!', 'info')
            return render_template("index.html")
        # Create new user
        new_user = User(fullname=fullname, school_id=school_id, group_id=group_id)

        db.session.add(new_user)
        db.session.commit()

        return render_template("index.html")
    except Exception as e:
        flash(f"Error during signup: {e}")
        return 'An error occurred during signup. Please try again.', 500

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
            student_count = len(group.members)  # Count the number of students in this group
            total_students += student_count  # Add to total student count for the school
            total_students_all_schools += student_count  # Add to total student count for all schools
            
            group_data = {
                'name': group.name,
                'passcode': group.passcode,
                'student_count': student_count,  # Add student count for the group
                'students': [{'name': student.fullname} for student in group.members]  # Fetch student names
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
        # Define aliased models to avoid naming conflicts
        group_alias = aliased(Group)
        school_alias = aliased(School)
        
        # Fetch quiz results for the specific question, ordered by response time
        results = db.session.query(
            group_alias.name.label('group_name'),
            school_alias.name.label('school_name'),
            QuizResult.answer,
            QuizResult.result,
            QuizResult.response_time,
            QuizResult.score
        ).outerjoin(group_alias, group_alias.id == QuizResult.group_id) \
         .outerjoin(school_alias, school_alias.id == group_alias.school_id) \
         .filter(QuizResult.question_index == question_index) \
         .order_by(QuizResult.response_time) \
         .all()

        # Convert results to a list of dictionaries for JSON response
        results_list = [{
            'group_name': r.group_name,
            'school_name': r.school_name,
            'answer': r.answer,
            'result': r.result,
            'response_time': r.response_time,
            'score': r.score
        } for r in results]
        
        return jsonify({'results': results_list})
    except Exception as e:
        flash('Error fetching results:', e)
        return jsonify({'error': 'Error fetching quiz results.'}), 500

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
def checkresults():
    return render_template('checkresult.html')

@app.route('/questions_page', methods=['GET'])
def questions_page():
    return render_template('add_questions.html')










































########################## ADMIN SETTINGS ###########################
#####################################################################
@app.route('/toggle-registration', methods=['POST'])
def toggle_registration():
    # Fetch the current setting
    current_setting = db.session.query(Settings).filter_by(id=1).first()

    # If no setting exists, create a default one
    if not current_setting:
        current_setting = Settings(allow_registration=True, allow_quiz=True)  # Set default values
        db.session.add(current_setting)
        db.session.commit()

    # Only toggle the allow_registration setting if the request method is POST
    if request.method == 'POST':
        current_setting.allow_registration = not current_setting.allow_registration

        # Save the updated setting
        db.session.commit()

    # Render the template with the current setting
    return render_template("settings.html", allow_registration=current_setting.allow_registration, allow_quiz=current_setting.allow_quiz)


@app.route('/toggle_quiz', methods=['POST'])
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
            students = school.students
        else:
            groups = school.archived_groups
            students = school.archived_students

        # Prevent deletion of Admin group (assuming ID 5 is the admin group)
        if int(school.id) == 5:
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
        user = User.query.get_or_404(user_id)
        try:
            if int(user.id) == 1:
                flash(f'You cannot delete a Super Admin!', 'info')
                return redirect(url_for('settings'))
            
            db.session.delete(user)
            db.session.commit()
            flash(f'Student {user.fullname.upper()} has been deleted sucessfully.', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting student: {e}', 'danger')
    else:
        flash('Unauthorised action', 'danger')
    return redirect(url_for('settings'))

@app.route('/add-school', methods=['POST'])
def add_school():
    try:
        # Get school name and group count from the form
        school_name = request.form['schoolname']
        group_count = int(request.form['groupcount'])
        season = int(request.form['season'])

        # Create a new school
        new_school = School(name=school_name, season=season)
        db.session.add(new_school)
        db.session.commit()  # Commit to get the school id

        # Create the specified number of groups for the school
        for i in range(1, group_count + 1):
            group_name = f"Group {i}"
            new_group = Group(name=group_name, school_id=new_school.id)
            db.session.add(new_group)

        db.session.commit()  # Commit groups to the database

        return redirect(url_for('settings'))
    except Exception as e:
        flash(f"Error adding school and groups: {e}")
        return 'An error occurred while adding the school and groups.', 500

@app.route('/get-schools')
def get_schools():
    schools = School.query.all()
    schools_list = [{'id': school.id, 'name': school.name} for school in schools]
    return jsonify({'schools': schools_list})

@app.route('/get_groups/<int:school_id>', methods=['GET'])
def get_groups(school_id):
    groups = Group.query.filter_by(school_id=school_id).all()
    group_list = [{
        'id': group.id,
        'name': group.name,
        'student_count': len(group.members)  # Assuming `group.members` returns a list of students
    } for group in groups]
    
    return jsonify(group_list)

@app.route('/settings', methods=['GET', 'POST'])
def settings():
    users_with_schools = []
    # Fetch the current setting
    current_setting = db.session.query(Settings).filter_by(id=1).first()

    # Fetch all the users from the database
    users = User.query.all()

    for user in users:
        school = School.query.filter_by(id=user.school_id).first()
        group = Group.query.filter_by(id=user.school_id).first()
        users_with_schools.append({
            'id': user.id,
            'fullname': user.fullname,
            'school_name': school.name if school else 'N/A',
            'group_name': group.name if group else 'N/A'
        })

    # If no setting exists, create a default one
    if not current_setting:
        current_setting = Settings(allow_registration=True, allow_quiz=True)  # Set default values
        db.session.add(current_setting)
        db.session.commit()

    # Only toggle the allow_registration setting if the request method is POST
    if request.method == 'POST':
        current_setting.allow_registration = not current_setting.allow_registration

        # Save the updated setting
        db.session.commit()

    # Render the template with the current setting
    return render_template("settings.html", users=users_with_schools, allow_registration=current_setting.allow_registration, allow_quiz=current_setting.allow_quiz)

@app.route('/archive_school/<int:school_id>', methods=['POST'])
def archive_school(school_id):
    school = School.query.get(school_id)
    if not school:
        flash("School not found!", "error")
        return redirect(url_for('admin_panel'))

    try:
        if int(school.id) == 5:
            flash("You cannot archive Admin School!", "info")
        else:
            school.archive()
            flash("School successfully archived!", "success")
    except Exception as e:
        db.session.rollback()
        flash("An error occurred while archiving the school.", "error")
    
    return redirect(url_for('admin_panel'))

# Route for adding questions
@app.route('/add_question', methods=['GET', 'POST'])
def add_question():
    if request.method == 'POST':
        question_text = request.form['question_text']
        option_a = request.form['option_a']
        option_b = request.form['option_b']
        option_c = request.form['option_c']
        option_d = request.form['option_d']
        correct_answer = request.form['correct_answer']
        image = None

        # Save the image if provided
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']
            filename = secure_filename(file.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(image_path)
            image = image_path

        # Save the question to the database
        new_question = Question(
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
            image=image
        )
        db.session.add(new_question)
        db.session.commit()

        flash('Question Added!', 'success')
        return redirect(url_for('add_question'))

    return render_template('add_questions.html')  # This renders the form

@app.route('/generate_questions_json', methods=['POST'])
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

@app.route('/sync-database', methods=['GET'])
@login_required
def sync_database():
    from extensions import db as local_db
    try:
        aiven_session = AivenSession()

        # Get all Aiven schools
        aiven_schools = aiven_session.query(School).all()

        for a_sch in aiven_schools:
            # Check if school exists in local DB
            existing_school = local_db.session.get(School, a_sch.id)
            if not existing_school:
                local_school = School(id=a_sch.id, name=a_sch.name, season=a_sch.season)
                local_db.session.add(local_school)

            for a_group in a_sch.groups:
                existing_group = local_db.session.get(Group, a_group.id)
                if not existing_group:
                    local_group = Group(
                        id=a_group.id,
                        name=a_group.name,
                        passcode=a_group.passcode,
                        school_id=a_group.school_id,
                        is_admin=a_group.is_admin
                    )
                    local_db.session.add(local_group)

                for a_user in a_group.members:
                    existing_user = local_db.session.get(User, a_user.id)
                    if not existing_user:
                        local_user = User(
                            id=a_user.id,
                            fullname=a_user.fullname,
                            school_id=a_user.school_id,
                            group_id=a_user.group_id,
                            is_admin=a_user.is_admin
                        )
                        local_db.session.add(local_user)

        local_db.session.commit()
        flash("New data synced from Aiven to local database successfully!", 'success')
        return redirect(url_for("admin_panel"))

    except Exception as e:
        local_db.session.rollback()
        return jsonify({"error": str(e)}), 500






































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

questions = load_questions()

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
        group = Group.query.filter_by(id=group_id, school_id=school_id).first()
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

    if group_info:
        group_id = group_info['group_id']
        answer = data.get('answer')  # This is expected to be "A", "B", "C", or "D"
        question_index = data.get('question_index')
        response_time = data.get('response_time', 0)

        # Validate response_time and question_index
        if not isinstance(response_time, (int, float)):
            response_time = 0
        if question_index is None or not (0 <= question_index < len(questions)):
            return  # Invalid question index

        # Retrieve the group and associated school name
        group = Group.query.get(group_id)
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
            group_id=group_id,
            question_index=question_index,
            answer=answer,  # Store the letter choice ("A", "B", "C", or "D")
            result=result,
            response_time=response_time,
            score=score,  # Store the calculated score
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
        group_alias = aliased(Group)
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
        flash(f'Error during restart quiz: {e}')
        # You might want to emit an error message back to the client
        emit('error_message', {'error': 'Failed to restart the quiz.'}, broadcast=True)

    
@socketio.on('next_question')
def handle_next_question():
    global current_question_index

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
        flash(f"Error in next_question: {e}")
        emit('message', 'An error occurred while loading the next question.', room=request.sid)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    os.kill(os.getpid(), signal.SIGINT)  # Sends an interrupt signal to terminate the process
    return "Server shutting down..."


if __name__ == '__main__':
    # Ensure the upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    print("Starting server with Eventlet...")
    socketio.run(app, host="0.0.0.0", port=5000, debug=False)