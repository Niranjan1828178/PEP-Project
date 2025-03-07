from flask import Flask, request, render_template, redirect, url_for, session, flash, send_file
import os
from flask_sqlalchemy import SQLAlchemy
import json
from groq import Groq
from config import GROQ_API_KEY
import markdown2
import bcrypt  

# Initialize Groq client
groq_client = Groq(api_key=GROQ_API_KEY)

app = Flask(__name__)

# Connection to the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://test:Password@localhost:3307/education'
app.config['SECRET_KEY'] = 'your-secret-key-here'  # Replace os.urandom(24) with a fixed key
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(25), unique=True, nullable=False)
    phone_number = db.Column(db.String(20))
    password = db.Column(db.String(60), nullable=False)
    score = db.Column(db.Integer, default=0) 

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Hashes the password using bcrypt."""
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def check_password(self, password):
        """Checks if the provided password matches the stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

# Define QuizResult model
class QuizResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    topic = db.Column(db.String(20))
    score = db.Column(db.Integer)

    def __repr__(self):
        return f'<QuizResult user_id={self.user_id}, question_id={self.question_id}, score={self.score}>'

# Create database tables within the Flask application context
with app.app_context():
    db.create_all()  

# Route to Index Page
@app.route('/index')
def index():
    if 'logged_in' in session:
        user = User.query.filter_by(username=session['username']).first()
        with open('static/question.json', 'r') as file:
            topics_data = json.load(file)
        
        name = {'first_name': user.first_name, 'last_name': user.last_name}
        return render_template('index.html', user=name, topics=topics_data.keys())
    else:
        return redirect(url_for('login'))  

# Route to Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):  # Use check_password to compare
            session['logged_in'] = True
            session['username'] = username
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')


# Route to Profile Page
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()  # Fetch the user object

    if request.method == 'POST':
        user.first_name = request.form['first_name']
        user.last_name = request.form['last_name']
        user.email = request.form['email']
        user.phone_number = request.form['phone_number']
        db.session.commit()  # Commit the changes to the database
        flash('Profile updated successfully!', 'success')
    return render_template('profile.html', user=user)

# Route to Home Page
@app.route('/')
@app.route('/home')
def home():
    session.clear()
    return render_template('Home.html')

# Route for registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        # Validate input fields
        errors = []
        if not username or not first_name or not last_name or not email or not password:
            errors.append('All fields marked with * are required')
        if password != confirm_password:
            errors.append('Passwords do not match')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters long')
        
        # Check for existing user
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            if existing_user.username == username:
                errors.append('Username already exists')
            if existing_user.email == email:
                errors.append('Email already registered')

        if errors:
            for error in errors:
                flash(error, 'error')  # Changed 'danger' to 'error' for consistency
            return render_template('register.html')  # Changed from redirect to render_template
        
        try:
            new_user = User(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone_number=phone_number
            )
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {str(e)}")
            return render_template('register.html')

    return render_template('register.html')

# Route to log out
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Route to Quiz Page
@app.route('/quiz', methods=['GET'])
def quiz():
    if 'username' not in session:
        flash('You must be logged in to take the quiz!', 'danger')
        return redirect(url_for('login'))
    return render_template('quiz.html')


# Route to Leaderboard Page
@app.route('/leaderboard')
def leaderboard():
    users = User.query.order_by(User.score.desc(),User.username.asc()).all()
    leaderboard_data = []
    rank = 1
    for user in users:
        username = user.username
        total_score = user.score 
        if rank == 1:
            badge = "Gold"
        elif rank == 2:
            badge = "Silver"
        elif rank==3:
            badge = "Bronze"
        else:
            badge = "Participation" 
        leaderboard_data.append({
            'rank': rank,
            'username': username,
            'score': total_score,
        })
        rank += 1 
    return render_template('leaderboard.html', leaderboard_data=leaderboard_data)


def get_data():
    with open('static\\question.json', 'r') as file:
        data = json.load(file)  # Load JSON file as a Python dictionary
    return data 

def get_topic():
    with open('static\\advanced.json', 'r') as file:
        data = json.load(file)  # Load JSON file as a Python dictionary
    return data 

# Add this near other helper functions in Main.py
def get_step_content(topic, subtopic):
    """Helper function to get content for a specific step"""
    try:
        with open('static/question.json', 'r') as file:
            topics_data = json.load(file)
        
        question = next((q for q in topics_data[topic] if q['subtopic'] == subtopic), None)
        
        if question:
            prompt = f"""Explain {subtopic} in {topic} programming language with the following structure:
            1. Brief Introduction (2-3 sentences)
            2. Main Concept (detailed explanation)
            3. Code Examples (with comments if necessary else text or formule examples)
            4. Key Points to Remember
            
            Format the response with proper Markdown headings and code blocks."""
            
            response = groq_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                max_tokens=2048
            )
            content = response.choices[0].message.content

            # Parse content into sections
            sections = []
            current_section = {"heading": "", "description": "", "examples": []}
            in_code_block = False
            current_code = ""
            
            for line in content.split('\n'):
                if line.startswith('#'):  # Section header
                    if current_section["heading"]:
                        if current_code:
                            current_section["examples"].append(current_code)
                            current_code = ""
                        sections.append(current_section.copy())
                    current_section = {
                        "heading": line.replace('#', '').strip(),
                        "description": "",
                        "examples": []
                    }
                elif line.strip().startswith('```'):
                    if in_code_block:
                        current_section["examples"].append(current_code.strip())
                        current_code = ""
                        in_code_block = False
                    else:
                        in_code_block = True
                else:
                    if in_code_block:
                        current_code += line + "\n"
                    elif line.strip():
                        current_section["description"] += line + "\n"
            
            # Add the last section
            if current_section["heading"]:
                if current_code:
                    current_section["examples"].append(current_code)
                sections.append(current_section)

            return {
                "content": {
                    "title": f"{subtopic} in {topic}",
                    "introduction": sections[0]["description"] if sections else "",
                    "sections": sections[1:] if len(sections) > 1 else sections,
                    "summary": question['link'] if question else "Visit the provided link to learn more.",
                    "notes": "Practice these concepts to better understand them."
                }
            }
        return None
    except Exception as e:
        print(f"Error in get_step_content: {str(e)}")
        return None

# Route to Progress Page and calculate progress
@app.route('/result', methods=['GET', 'POST'])
def result():
    if 'username' not in session:
        flash('You must be logged in to take the quiz!', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        data = get_data()
        topic = request.form.get('subject')
        questions = data[topic]
        score = 0
        wrong_answer = []
        for q in questions:
            correct_answer = q["options"][int(q["answer"])]
            selected_answer = request.form.get(str(q["id"]))
            if selected_answer is not None:
                if correct_answer == selected_answer:
                    score += 1
                else:
                    if wrong_answer:
                        t = True
                        for i in wrong_answer:
                            if q["subtopic"] == i[0]:
                                t = False
                        if t:
                            da = [q["subtopic"], q["link"]]
                            wrong_answer.append(da)
                    else:
                        da = [q["subtopic"], q["link"]]
                        wrong_answer.append(da)
        user = User.query.filter_by(username=session['username']).first()
        quizres = QuizResult.query.filter_by(user_id=user.id).all()
        t = True
        for q in quizres:
            if q.topic == topic:
                q.score = score
                db.session.commit()
                t = False
        if t:
            new_user = QuizResult(user_id=user.id, topic=topic, score=score)
            db.session.add(new_user)
        user_results = QuizResult.query.filter_by(user_id=user.id).all()
        ts = 0
        for usr in user_results:
            ts += usr.score
        user.score = ts
        db.session.commit()
        if score == 10:
            advance = get_topic()
            advance = advance[topic]
            data = {"score": score, "improvement": advance}
        else:
            data = {"score": score, "improvement": wrong_answer}
        return render_template('progress.html', result=data)
    return redirect(url_for('index'))

@app.route('/topics/<topic>')
def topic_content(topic):
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Initialize progress tracking if not exists
    if 'progress' not in session:
        session['progress'] = {}
    if topic not in session['progress']:
        session['progress'][topic] = {
            'current_step': 0,
            'total_steps': len(get_topic_content(topic)),
            'completed': False
        }
    
    # Redirect to the current step
    current_step = session['progress'][topic]['current_step']
    return redirect(url_for('topic_step', topic=topic, step=current_step))

def get_topic_content(topic):
    # Helper function to get structured content for a topic
    with open('static/question.json', 'r') as file:
        topics_data = json.load(file)
    
    if topic not in topics_data:
        return []
        
    subtopics = list(set(q['subtopic'] for q in topics_data[topic]))
    return subtopics

@app.route('/topics/<topic>/step/<int:step>')
def topic_step(topic, step):
    if 'username' not in session:
        return redirect(url_for('login'))
        
    subtopics = get_topic_content(topic)
    total_steps = len(subtopics)
    
    if step < 0 or step >= total_steps:
        return redirect(url_for('topic_content', topic=topic))
    
    # Update progress
    if topic in session['progress']:
        if step > session['progress'][topic]['current_step']:
            session['progress'][topic]['current_step'] = step
            if step == total_steps - 1:
                session['progress'][topic]['completed'] = True
        session.modified = True
    
    # Get content for current step
    current_subtopic = subtopics[step]
    content = [get_step_content(topic, current_subtopic)]
    
    return render_template('steps.html',
                         topic=topic,
                         current_step=step,
                         total_steps=total_steps,
                         progress=(step / total_steps) * 100,
                         section_name=f"Learning {topic}",
                         content=content)

# Add this helper function
@app.template_filter('markdown')
def markdown_filter(text):
    return markdown2.markdown(text, extras=['fenced-code-blocks', 'tables'])

# main Starts
if __name__ == '__main__':
    app.run(debug=True)