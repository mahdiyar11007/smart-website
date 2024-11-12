import joblib

model = joblib.load('heart_disease_classification_model.pkl')

def predict(features):
    """
    Predict the outcome based on input features.
    """
    prediction = model.predict([features])
    return prediction[0]
