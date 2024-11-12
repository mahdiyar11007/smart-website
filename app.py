from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from model import predict  # Importing the predict function from model.py

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'COZ1TCwxc2J1tYFl3scDCyr3'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class PredictionHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    input_data = db.Column(db.String(200), nullable=False)
    prediction_result = db.Column(db.String(200), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('predictions', lazy=True))

with app.app_context():
    db.create_all()

# Decorator to enforce login requirement
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            return 'User already exists! Please choose a different username or email.'

        hashed_password = generate_password_hash(password)
        
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['username'] = user.username  
            session['user_id'] = user.id  
            return redirect(url_for('input_data'))  
        else:
            return 'Invalid credentials. Please try again.'
    
    return render_template('login.html')

@app.route('/input', methods=['GET', 'POST'])
@login_required
def input_data():
    if request.method == 'POST':
        # Collecting features from the form
        features = [
            float(request.form['age']),
            float(request.form['sex']),
            float(request.form['cp']),
            float(request.form['trestbps']),
            float(request.form['chol']),
            float(request.form['fbs']),
            float(request.form['restecg']),
            float(request.form['thalach']),
            float(request.form['exang']),
            float(request.form['oldpeak']),
            float(request.form['slope']),
            float(request.form['ca']),
            float(request.form['thal'])
        ]
        
        result = predict(features)

        prediction = PredictionHistory(
            user_id=session['user_id'],
            input_data=str(features),
            prediction_result=str(result)
        )
        db.session.add(prediction)
        db.session.commit()
        
        return render_template('result.html', result=result)
    
    return render_template('input.html')

@app.route('/profile')
@login_required
def profile():
    user = User.query.filter_by(id=session['user_id']).first()
    predictions = PredictionHistory.query.filter_by(user_id=user.id).order_by(PredictionHistory.timestamp.desc()).all()
    
    return render_template('profile.html', user=user, predictions=predictions)

@app.route('/error')
def error():
    error_message = "An error has occurred."
    return render_template('error.html', error_message=error_message)

if __name__ == '__main__':
    app.run(debug=True)
