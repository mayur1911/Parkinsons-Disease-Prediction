from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import joblib
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import os
from datetime import datetime 

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital_admin.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Required for session management
db = SQLAlchemy(app)

# Load the saved model
loaded_model = joblib.load('Model/xgboost_model.pkl')

# Define the Admin model
class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

# Define the Patients model
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)

# Initialize database and add initial admin if it doesn’t exist
def initialize_database():
    with app.app_context():  # Ensure an application context
        db.create_all()
        if not Admin.query.filter_by(username='admin').first():
            hashed_password = generate_password_hash('admin123')  # Hash the password
            admin = Admin(username='admin', password=hashed_password)
            db.session.add(admin)
            db.session.commit()
            print("Database initialized and admin user created.")

# Route for the home page (admin login page)
@app.route('/')
def home():
    return render_template('login.html')

# Route for the admin login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Debugging print statements
        print(f"Username entered: {username}")
        print(f"Password entered: {password}")

        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password, password):
            session['admin_id'] = admin.id
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

# Route for patient registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        date_of_birth = request.form['date_of_birth']

        # Check if the username or email already exists
        if Patient.query.filter((Patient.username == username) | (Patient.email == email)).first():
            flash('Username or Email already exists')
            return redirect(url_for('register'))

        # Hash the password before storing
        hashed_password = generate_password_hash(password)

        # Create a new patient record
        new_patient = Patient(name=name, username=username, email=email,
                              password=hashed_password, date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d'))
        db.session.add(new_patient)
        db.session.commit()
        flash('Registration successful! You can now log in.')
        return redirect(url_for('login'))

    return render_template('register.html')

# Route for the registration page
@app.route('/register')
def show_registration():
    return render_template('register.html')

@app.route('/patient/login', methods=['GET', 'POST'])
def patient_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        patient = Patient.query.filter_by(username=username).first()
        if patient and check_password_hash(patient.password, password):
            session['patient_id'] = patient.id
            return redirect(url_for('predict'))
        else:
            flash('Invalid username or password')

    return render_template('patient_login.html')

# Route for the admin dashboard (prediction form)
@app.route('/dashboard')
def dashboard():
    if 'admin_id' not in session:
        return redirect(url_for('login'))
    
    # Fetch all patients from the database
    all_patients = Patient.query.all()
    
    return render_template('patients.html', patients=all_patients)  # Pass patients to the template


# Route for logging out the admin
@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    return redirect(url_for('login'))

# Route for the prediction form page
@app.route('/predict')
def predict_form():
    return render_template('predict.html')

@app.route('/result', methods=['GET','POST'])
def predict():
    prediction = None
    try:
        features = [
            float(request.form.get('MDVP_Fo', 0)),
            float(request.form.get('MDVP_Fhi', 0)),
            float(request.form.get('MDVP_Flo', 0)),
            float(request.form.get('MDVP_Jitter', 0)),
            float(request.form.get('MDVP_Jitter_Abs', 0)),
            float(request.form.get('MDVP_RAP', 0)),
            float(request.form.get('MDVP_PPQ', 0)),
            float(request.form.get('Jitter_DDP', 0)),
            float(request.form.get('MDVP_Shimmer', 0)),
            float(request.form.get('MDVP_Shimmer_dB', 0)),
            float(request.form.get('Shimmer_APQ3', 0)),
            float(request.form.get('Shimmer_APQ5', 0)),
            float(request.form.get('MDVP_APQ', 0)),
            float(request.form.get('Shimmer_DDA', 0)),
            float(request.form.get('NHR', 0)),
            float(request.form.get('HNR', 0)),
            float(request.form.get('RPDE', 0)),
            float(request.form.get('DFA', 0)),
            float(request.form.get('spread1', 0)),
            float(request.form.get('spread2', 0)),
            float(request.form.get('D2', 0)),
            float(request.form.get('PPE', 0)),
        ]

        # Create DataFrame for model prediction
        input_df = pd.DataFrame([features], columns=[
            'MDVP:Fo(Hz)', 'MDVP:Fhi(Hz)', 'MDVP:Flo(Hz)',
            'MDVP:Jitter(%)', 'MDVP:Jitter(Abs)', 'MDVP:RAP',
            'MDVP:PPQ', 'Jitter:DDP', 'MDVP:Shimmer',
            'MDVP:Shimmer(dB)', 'Shimmer:APQ3', 'Shimmer:APQ5',
            'MDVP:APQ', 'Shimmer:DDA', 'NHR', 'HNR',
            'RPDE', 'DFA', 'spread1', 'spread2',
            'D2', 'PPE'
        ])

        # Predict the result
        prediction_result  = loaded_model.predict(input_df)
        if prediction_result[0] == 1:
            prediction = "Parkinson's Disease Detected"
        else:
            prediction = "No Parkinson's Disease"

    except Exception as e:
        prediction = f"Error: {str(e)}"
    return render_template('predict.html', prediction=prediction)

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)
