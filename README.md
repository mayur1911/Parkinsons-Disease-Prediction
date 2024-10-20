
# Parkinson's Disease Prediction

This project uses machine learning to predict the presence of Parkinson's Disease based on vocal measurements. The model is built using the XGBoost algorithm, and the application is developed with Flask.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Running the Application](#running-the-application)
- [Contributing](#contributing)
- [License](#license)

## Features
- Predicts the presence of Parkinson's Disease based on input vocal parameters.
- Easy-to-use web interface for making predictions.

## Requirements
To run this project, you'll need:
- Python 3.x
- Flask
- scikit-learn
- joblib
- XGBoost
- Pandas

## Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/mayur1911/Parkinsons-Disease-Prediction.git
   cd Parkinsons-Disease-Prediction
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - On **Windows:**
     ```bash
     venv\Scripts\activate
     ```
   - On **macOS/Linux:**
     ```bash
     source venv/bin/activate
     ```

4. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage
Once the installation is complete, you can run the application and make predictions based on the input vocal parameters.

## Running the Application
1. Start the Flask server:
   ```bash
   python app.py
   ```

2. Open your web browser and navigate to `http://127.0.0.1:5000/` to access the application.

## Contributing
Contributions are welcome! Please feel free to submit a pull request or open an issue.

## License
This project is licensed under the MIT License. See the LICENSE file for more information.
