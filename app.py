from flask import Flask, render_template, request
import pandas as pd
import joblib

app = Flask(__name__)

# Load the saved model
loaded_model = joblib.load('Model/xgboost_model.pkl')

@app.route('/')
def home():
    return render_template('predict.html')

@app.route('/predict', methods=['POST'])
def predict():
    features = [
        float(request.form['MDVP_Fo']),
        float(request.form['MDVP_Fhi']),
        float(request.form['MDVP_Flo']),
        float(request.form['MDVP_Jitter']),
        float(request.form['MDVP_Jitter_Abs']),
        float(request.form['MDVP_RAP']),
        float(request.form['MDVP_PPQ']),
        float(request.form['Jitter_DDP']),
        float(request.form['MDVP_Shimmer']),
        float(request.form['MDVP_Shimmer_dB']),
        float(request.form['Shimmer_APQ3']),
        float(request.form['Shimmer_APQ5']),
        float(request.form['MDVP_APQ']),
        float(request.form['Shimmer_DDA']),
        float(request.form['NHR']),
        float(request.form['HNR']),
        float(request.form['RPDE']),
        float(request.form['DFA']),
        float(request.form['spread1']),
        float(request.form['spread2']),
        float(request.form['D2']),
        float(request.form['PPE']),
    ]

    input_df = pd.DataFrame([features], columns=[
        'MDVP:Fo(Hz)', 'MDVP:Fhi(Hz)', 'MDVP:Flo(Hz)', 
        'MDVP:Jitter(%)', 'MDVP:Jitter(Abs)', 'MDVP:RAP', 
        'MDVP:PPQ', 'Jitter:DDP', 'MDVP:Shimmer', 
        'MDVP:Shimmer(dB)', 'Shimmer:APQ3', 'Shimmer:APQ5', 
        'MDVP:APQ', 'Shimmer:DDA', 'NHR', 'HNR', 
        'RPDE', 'DFA', 'spread1', 'spread2', 
        'D2', 'PPE'
    ])

    prediction = loaded_model.predict(input_df)
    result = "Parkinson's Disease Detected" if prediction[0] == 1 else "No Parkinson's Disease"
    return render_template('predict.html', prediction=result)

if __name__ == '__main__':
    app.run(debug=True)