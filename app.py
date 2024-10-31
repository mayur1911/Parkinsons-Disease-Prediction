from flask import Flask, render_template, request, redirect, url_for, flash, session
import pandas as pd
import joblib
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import os
from datetime import datetime 
import logging

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

# Define the Parameters model
class Parameters(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'), nullable=False, unique=True)  # Ensure unique patient_id
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

@app.route('/predict_form')
def predict_form():
    patient_id = request.args.get('patient_id')
    if patient_id:
        session['patient_id'] = patient_id  # Save patient ID in session
    return render_template('predict.html')  # Or your actual prediction form template

@app.route('/result', methods=['GET', 'POST'])
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
        prediction_result = loaded_model.predict(input_df)
        if prediction_result[0] == 1:
            prediction = "Parkinson's Disease Detected"
        else:
            prediction = "No Parkinson's Disease"

        # Save parameters to the database
        patient_id = session.get('patient_id')  # Get the logged-in patient ID from the session
        
        # Check if a record exists and update it or create a new one
        params = Parameters.query.filter_by(patient_id=patient_id).first()  # Check if a record exists

        if params:
            # Update existing parameters
            params.MDVP_Fo = features[0]
            params.MDVP_Fhi = features[1]
            params.MDVP_Flo = features[2]
            params.MDVP_Jitter = features[3]
            params.MDVP_Jitter_Abs = features[4]
            params.MDVP_RAP = features[5]
            params.MDVP_PPQ = features[6]
            params.Jitter_DDP = features[7]
            params.MDVP_Shimmer = features[8]
            params.MDVP_Shimmer_dB = features[9]
            params.Shimmer_APQ3 = features[10]
            params.Shimmer_APQ5 = features[11]
            params.MDVP_APQ = features[12]
            params.Shimmer_DDA = features[13]
            params.NHR = features[14]
            params.HNR = features[15]
            params.RPDE = features[16]
            params.DFA = features[17]
            params.spread1 = features[18]
            params.spread2 = features[19]
            params.D2 = features[20]
            params.PPE = features[21]

            db.session.commit()  # Commit the changes
        else:
            # Create new parameters record if it does not exist
            new_params = Parameters(
                patient_id=patient_id,
                MDVP_Fo=features[0],
                MDVP_Fhi=features[1],
                MDVP_Flo=features[2],
                MDVP_Jitter=features[3],
                MDVP_Jitter_Abs=features[4],
                MDVP_RAP=features[5],
                MDVP_PPQ=features[6],
                Jitter_DDP=features[7],
                MDVP_Shimmer=features[8],
                MDVP_Shimmer_dB=features[9],
                Shimmer_APQ3=features[10],
                Shimmer_APQ5=features[11],
                MDVP_APQ=features[12],
                Shimmer_DDA=features[13],
                NHR=features[14],
                HNR=features[15],
                RPDE=features[16],
                DFA=features[17],
                spread1=features[18],
                spread2=features[19],
                D2=features[20],
                PPE=features[21]
            )
            db.session.add(new_params)  # Add the new record
            db.session.commit()  # Commit the changes

    except Exception as e:
        flash(f"An error occurred during prediction: {e}")

    return render_template('predict.html', prediction=prediction)

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)