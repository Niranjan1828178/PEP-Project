from flask import Flask, request, render_template, redirect, url_for, session, flash,send_file
import os
from flask_sqlalchemy import SQLAlchemy
import json


app = Flask(__name__)

# Connection to the database
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://test:Password@localhost:3307/education'
app.config['SECRET_KEY'] = os.urandom(24) 
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
    password = db.Column(db.String(25), nullable=False)
    score = db.Column(db.Integer, default=0) 

    def __repr__(self):
        return f'<User {self.username}>'

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
        name={'first_name':user.first_name,'last_name':user.last_name}
        return render_template('index.html',user=name) 
    else:
        return redirect(url_for('login'))  

# Route to Login Page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password==password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index')) 
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')


# Route to Profile Page
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'logged_in' not in session:
        return redirect(url_for('login'))

    user = User.query.filter_by(username=session['username']).first()  # Fetch the user object

    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.phone_number = request.form['phone_number']
        db.session.commit()  # Commit the changes to the database
        flash('Profile updated successfully!', 'success')
    print(user)
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
        print("hi came to register!!!!")
        if password != confirm_password:
            flash('Passwords do not match. Please try again.', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()

        if existing_user:
            flash('Username or email already exists. Try another one.', 'danger')
        else:
            new_user = User(username=username, first_name=first_name, last_name=last_name, email=email,
                            phone_number=phone_number, password=password)
            db.session.add(new_user)  # Add the new user to the session
            db.session.commit()  # Commit the transaction to the database
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))

    return render_template('register.html')

# Route to log out
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# Route to Quiz Page
@app.route('/quiz', methods=['GET', 'POST'])
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
    print(leaderboard_data)
    return render_template('leaderboard.html', leaderboard_data=leaderboard_data)


def get_data():
    with open('static\\question.json', 'r') as file:
        data = json.load(file)  # Load JSON file as a Python dictionary
    return data 

def get_topic():
    with open('static\\advanced.json', 'r') as file:
        data = json.load(file)  # Load JSON file as a Python dictionary
    return data 

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
        print("crossed")
        user = User.query.filter_by(username=session['username']).first()
        print(f"got user:{user}: score: {score}")
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
        print(f"got tsc:{ts}")
        db.session.commit()
        if score == 10:
            advance = get_topic()
            advance = advance[topic]
            data = {"score": score, "improvement": advance}
        else:
            data = {"score": score, "improvement": wrong_answer}
        return render_template('progress.html', result=data)
    return redirect(url_for('index'))

# main Starts
if __name__ == '__main__':
    app.run(debug=True)