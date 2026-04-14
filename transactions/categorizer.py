import joblib
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.naive_bayes import MultinomialNB

# Load trained classifier & vectorizer
classifier = joblib.load("transaction_classifier.pkl")
vectorizer = joblib.load("transaction_vectorizer.pkl")

def categorize_transaction(description):
    """Categorizes a transaction description using the trained model."""
    # Transform input using the vectorizer
    X_new = vectorizer.transform([description])

    # Predict category
    predicted_category = classifier.predict(X_new)[0]
    
    return predicted_category

def update_category(description, correct_category):
    """Updates the model with new data if prediction is incorrect."""
    df = pd.DataFrame([[description, correct_category]], columns=["description", "category"])

    # Transform text data
    X_train = vectorizer.transform(df["description"])
    y_train = df["category"]

    # Retrain the model with new data
    classifier.partial_fit(X_train, y_train, classes=classifier.classes_)

    # Save the updated model
    joblib.dump(classifier, "transaction_classifier.pkl")

    return f"✅ Model updated with new category: {correct_category}"
