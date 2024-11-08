from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import joblib
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital_admin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.urandom(24)
db = SQLAlchemy(app)

# Load the saved model
loaded_model = joblib.load('Model/xgboost_model.pkl')

# Models
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    parameters = db.relationship('Parameters', backref='patient', uselist=False, cascade="all, delete-orphan")

class Parameters(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False, unique=True)
    # Parameters fields
    MDVP_Fo = db.Column(db.Float, nullable=False)
    MDVP_Fhi = db.Column(db.Float, nullable=False)
    MDVP_Flo = db.Column(db.Float, nullable=False)
    MDVP_Jitter = db.Column(db.Float, nullable=False)
    MDVP_Jitter_Abs = db.Column(db.Float, nullable=False)
    MDVP_RAP = db.Column(db.Float, nullable=False)
    MDVP_PPQ = db.Column(db.Float, nullable=False)
    Jitter_DDP = db.Column(db.Float, nullable=False)
    MDVP_Shimmer = db.Column(db.Float, nullable=False)
    MDVP_Shimmer_dB = db.Column(db.Float, nullable=False)
    Shimmer_APQ3 = db.Column(db.Float, nullable=False)
    Shimmer_APQ5 = db.Column(db.Float, nullable=False)
    MDVP_APQ = db.Column(db.Float, nullable=False)
    Shimmer_DDA = db.Column(db.Float, nullable=False)
    NHR = db.Column(db.Float, nullable=False)
    HNR = db.Column(db.Float, nullable=False)
    RPDE = db.Column(db.Float, nullable=False)
    DFA = db.Column(db.Float, nullable=False)
    spread1 = db.Column(db.Float, nullable=False)
    spread2 = db.Column(db.Float, nullable=False)
    D2 = db.Column(db.Float, nullable=False)
    PPE = db.Column(db.Float, nullable=False)

# Initialize database with admin user
def initialize_database():
    with app.app_context():
        db.create_all()
        if not Admin.query.filter_by(username='admin').first():
            db.session.add(Admin(username='admin', password=generate_password_hash('admin123')))
            db.session.commit()
            print("Database initialized with default admin.")

# Decorator for login-required routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            flash("Please log in to access this page.")
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            return redirect(url_for('dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/patient_login', methods=['GET','POST'])
def patient_login():
    username = request.form.get('username')
    password = request.form.get('password')

    patient = Patient.query.filter_by(username=username).first()
    if patient and check_password_hash(patient.password, password):
        session['patient_id'] = patient.id  # Store patient session info
        return redirect(url_for('predict_form', patient_id=patient.id)) # Redirect to 'predict.html' page
    else:
        flash('Invalid username or password', 'error')
        return redirect(url_for('login'))  # Redirect back to login page if credentials are wrong


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        date_of_birth = request.form['date_of_birth']

        print(f"Registering patient with username: {username}")  # Debugging line

        # Validate required fields
        if not all([name, username, email, password, date_of_birth]):
            flash('All fields are required.')
            return redirect(url_for('register'))

        # Check for existing username or email
        existing_patient = Patient.query.filter((Patient.username == username) | (Patient.email == email)).first()
        if existing_patient:
            flash('Username or Email already exists')
            return redirect(url_for('register'))

        # Create new patient
        try:
            new_patient = Patient(
                name=name,
                username=username,
                email=email,
                password=generate_password_hash(password),
                date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d')
            )
            db.session.add(new_patient)
            db.session.commit()
            print(f"Patient {name} registered successfully.")  # Debugging line
            flash('Registration successful! You can now log in.')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()  # Rollback in case of an error
            print(f"Error during registration: {str(e)}")  # Debugging line
            flash('Error during registration. Please try again.')

    return render_template('register.html')

@app.route('/dashboard')
@login_required  # Protect the register route
def dashboard():
    all_patients = Patient.query.all()
    return render_template('dashboard.html', patients=all_patients)

@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    return redirect(url_for('login'))

@app.route('/predict_form')
def predict_form():
    # Get patient_id from query parameters
    patient_id = request.args.get('patient_id')
    
    # Retrieve the record from the Parameters table
    if patient_id:
        parameter_record = Parameters.query.filter_by(patient_id=patient_id).first()
        
        if parameter_record:
            # Pass the retrieved data to the template
            return render_template('predict.html', parameter_record=parameter_record)
    
    # If no record found, render the template with a message
    return render_template('predict.html', message="No data found for this patient.")

@app.route('/result', methods=['POST'])
def predict():
    try:
        features = [float(request.form.get(key, 0)) for key in [
            'MDVP_Fo', 'MDVP_Fhi', 'MDVP_Flo', 'MDVP_Jitter', 'MDVP_Jitter_Abs',
            'MDVP_RAP', 'MDVP_PPQ', 'Jitter_DDP', 'MDVP_Shimmer', 'MDVP_Shimmer_dB',
            'Shimmer_APQ3', 'Shimmer_APQ5', 'MDVP_APQ', 'Shimmer_DDA', 'NHR', 'HNR',
            'RPDE', 'DFA', 'spread1', 'spread2', 'D2', 'PPE'
        ]]
        input_df = pd.DataFrame([features], columns=[
            'MDVP:Fo(Hz)', 'MDVP:Fhi(Hz)', 'MDVP:Flo(Hz)',
            'MDVP:Jitter(%)', 'MDVP:Jitter(Abs)', 'MDVP:RAP',
            'MDVP:PPQ', 'Jitter:DDP', 'MDVP:Shimmer',
            'MDVP:Shimmer(dB)', 'Shimmer:APQ3', 'Shimmer:APQ5',
            'MDVP:APQ', 'Shimmer:DDA', 'NHR', 'HNR',
            'RPDE', 'DFA', 'spread1', 'spread2', 'D2', 'PPE'
        ])
        prediction_result = loaded_model.predict(input_df)[0]
        prediction = "Parkinson's Disease Detected" if prediction_result == 1 else "No Parkinson's Disease"
        save_or_update_parameters(session.get('patient_id'), features)
    except Exception as e:
        flash(f"An error occurred during prediction: {e}")
    return render_template('predict.html', prediction=prediction)

def save_or_update_parameters(patient_id, features):
    param_record = Parameters.query.filter_by(patient_id=patient_id).first()
    if param_record:
        for i, col in enumerate(Parameters.__table__.columns.keys()[2:]):
            setattr(param_record, col, features[i])
    else:
        param_record = Parameters(patient_id=patient_id, **dict(zip(Parameters.__table__.columns.keys()[2:], features)))
        db.session.add(param_record)
    db.session.commit()

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)