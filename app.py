from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import joblib
import pandas as pd
from datetime import datetime
import os
import logging
from flask import jsonify, redirect

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

# Ensure the database is initialized when the app starts
initialize_database()
from functools import wraps
from flask import flash, redirect, url_for, session

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_id' not in session:
            # Only flash the message if it's not already in session
            if 'message_shown' not in session:
                flash("Please log in to access this page as ADMIN only.")
                session['message_shown'] = True  # Mark message as shown
            return redirect(url_for('login'))
        # Clear the message_shown flag upon successful login
        session.pop('message_shown', None)
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
    
    # If patient_id exists in query parameters, store it in session
    if patient_id:
        session['patient_id'] = patient_id
        logging.debug(f"Patient ID {patient_id} set in session.")
    else:
        logging.warning("No patient ID provided in the request.")

    # Log the current session patient_id
    current_patient_id = session.get('patient_id')
    logging.debug(f"Current patient ID in session: {current_patient_id}")
    
    # If there is no patient_id in the session, log and redirect
    if not current_patient_id:
        logging.error("No patient_id found in the session. Redirecting to dashboard.")
        flash("No patient selected. Please select a patient.")
        return redirect(url_for('dashboard'))  # Redirect to the patient selection page

    # Retrieve the record from the Parameters table for the selected patient_id
    parameter_record = Parameters.query.filter_by(patient_id=current_patient_id).first()
    
    # Define default values for each field if parameter_record is None
    default_values = {
        'MDVP_Fo': 0,
        'MDVP_Fhi': 0,
        'MDVP_Flo': 0,
        'MDVP_Jitter': 0,
        'MDVP_Jitter_Abs': 0,
        'MDVP_RAP': 0,
        'MDVP_PPQ': 0,
        'Jitter_DDP': 0,
        'MDVP_Shimmer': 0,
        'MDVP_Shimmer_dB': 0,
        'Shimmer_APQ3': 0,
        'Shimmer_APQ5': 0,
        'MDVP_APQ': 0,
        'Shimmer_DDA': 0,
        'NHR': 0,
        'HNR': 0,
        'RPDE': 0,
        'DFA': 0,
        'spread1': 0,
        'spread2': 0,
        'D2': 0,
        'PPE': 0
    }
    
    # If parameter_record is None, use default values
    parameter_data = parameter_record.__dict__ if parameter_record else default_values
    logging.debug(f"Parameter data for patient_id {current_patient_id}: {parameter_data}")
    
    return render_template('predict.html', parameter_record=parameter_data)


# Set up basic logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  # Logs will be saved to this file
        logging.StreamHandler()  # Also log to the console
    ]
)

@app.route('/result', methods=['POST'])
def predict():
    prediction = ""
    try:
        # Get patient_id from session
        patient_id = session.get('patient_id')
        logging.debug(f"Patient ID retrieved from session: {patient_id}")
        if not patient_id:
            flash("No patient ID found in session. Please log in again.")
            return redirect(url_for('patient_login'))

        # Collect features from the form
        feature_keys = [
            'MDVP_Fo', 'MDVP_Fhi', 'MDVP_Flo', 'MDVP_Jitter', 'MDVP_Jitter_Abs',
            'MDVP_RAP', 'MDVP_PPQ', 'Jitter_DDP', 'MDVP_Shimmer', 'MDVP_Shimmer_dB',
            'Shimmer_APQ3', 'Shimmer_APQ5', 'MDVP_APQ', 'Shimmer_DDA', 'NHR', 'HNR',
            'RPDE', 'DFA', 'spread1', 'spread2', 'D2', 'PPE'
        ]
        
        # Collect features from the form and ensure the default is 0 if not found
        features = [float(request.form.get(key, 0)) for key in feature_keys]

        # Log the incoming features to verify they are passed correctly
        logging.debug(f"Incoming features: {features}")

        # Log the form data to verify all submitted fields
        logging.debug(f"Form data: {request.form}")

        # Prepare input data for prediction
        input_df = pd.DataFrame([features], columns=[
            'MDVP:Fo(Hz)', 'MDVP:Fhi(Hz)', 'MDVP:Flo(Hz)', 'MDVP:Jitter(%)', 
            'MDVP:Jitter(Abs)', 'MDVP:RAP', 'MDVP:PPQ', 'Jitter:DDP', 
            'MDVP:Shimmer', 'MDVP:Shimmer(dB)', 'Shimmer:APQ3', 'Shimmer:APQ5',
            'MDVP:APQ', 'Shimmer:DDA', 'NHR', 'HNR', 'RPDE', 'DFA', 'spread1',
            'spread2', 'D2', 'PPE'
        ])
        
        # Log the DataFrame used for prediction
        logging.debug(f"Prepared input DataFrame for prediction: {input_df}")

        # Get prediction result
        prediction_result = loaded_model.predict(input_df)[0]
        prediction = "Parkinson's Disease Detected" if prediction_result == 1 else "No Parkinson's Disease"

        # Save or update parameters in the database
        save_or_update_parameters(patient_id, features)
        
        # Retrieve parameter record to show in UI
        parameter_record = Parameters.query.filter_by(patient_id=patient_id).first()
        if parameter_record is None:
            logging.warning(f"Parameter record for patient_id {patient_id} not found after save.")
        
    except Exception as e:
        flash(f"An error occurred during prediction: {e}")
        parameter_record = None
        logging.error(f"Prediction error: {e}")

    return render_template('predict.html', prediction=prediction, parameter_record=parameter_record)


def save_or_update_parameters(patient_id, features):
    try:
        # Find the existing parameter record for the patient
        param_record = Parameters.query.filter_by(patient_id=patient_id).first()
        
        if param_record:
            # If a record exists, update it
            for i, col in enumerate(Parameters.__table__.columns.keys()[2:]):  # Skip first column, patient_id
                logging.debug(f"Updating {col} with value {features[i]}")
                setattr(param_record, col, features[i])
        else:
            # If no record exists, create a new one
            param_record = Parameters(patient_id=patient_id, **dict(zip(Parameters.__table__.columns.keys()[2:], features)))
            db.session.add(param_record)

        # Commit the changes
        db.session.flush()  # Ensures data is sent to DB without waiting for commit.
        db.session.commit()
        logging.debug("Parameters saved successfully.")

    except Exception as e:
        logging.error(f"Error saving/updating parameters: {e}")
        db.session.rollback()  # Rollback in case of error
        flash(f"Error while saving parameters: {e}")

@app.route('/delete_patient/<int:patient_id>', methods=['DELETE'])
def delete_patient(patient_id):
    # Find the patient by ID
    patient = Patient.query.get(patient_id)
    
    # If the patient exists, delete them
    if patient:
        db.session.delete(patient)  # This will also delete the associated Parameters due to cascade
        db.session.commit()
        return jsonify({'success': True, 'message': 'Patient deleted successfully'}), 200
    else:
        return jsonify({'success': False, 'message': 'Patient not found'}), 404

@app.route('/logout_and_home')
def logout_and_home():
    session.clear()  # Clear all session data
    return redirect(url_for('home'))  # Redirect to the home page

if __name__ == '__main__':
    initialize_database()
    app.run(debug=True)