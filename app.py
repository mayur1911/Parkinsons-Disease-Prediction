from flask import Flask, render_template, request
import pandas as pd
import joblib

app = Flask(__name__)

# Load the saved model
loaded_model = joblib.load('Model/xgboost_model.pkl')

# Route for the home page
@app.route('/')
def home():
    return render_template('index.html')

# Route for the prediction form page
@app.route('/predict')
def predict_form():
    return render_template('predict.html')

@app.route('/result', methods=['GET','POST'])
def predict():
    prediction = None  # Initialize prediction variable
    try:
        # Get the values from the form and handle errors in conversion
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
        # Set the prediction message based on the output
        if prediction_result[0] == 1:
            prediction = "Parkinson's Disease Detected"
        else:
            prediction = "No Parkinson's Disease"
        
    

    except Exception as e:
                prediction = f"Error: {str(e)}"
    return render_template('predict.html', prediction=prediction)

if __name__ == '__main__':
    app.run(debug=True)