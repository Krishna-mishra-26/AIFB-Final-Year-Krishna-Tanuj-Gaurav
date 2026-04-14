import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import joblib

# Load dataset
df = pd.read_csv("transactions_dataset.csv")

# Ensure correct column names
if "Transaction" not in df.columns or "Category" not in df.columns:
    raise KeyError("CSV must have 'Transaction' and 'Category' columns.")

# Feature (Transaction description) and target (Category)
X = df["Transaction"]  # Transaction descriptions
y = df["Category"]     # Categories

# Convert text into numerical features using TF-IDF Vectorizer
vectorizer = TfidfVectorizer()
X_transformed = vectorizer.fit_transform(X)

# Train a Naive Bayes classifier
classifier = MultinomialNB()
classifier.fit(X_transformed, y)

# Save model and vectorizer
joblib.dump(classifier, "transaction_classifier.pkl")
joblib.dump(vectorizer, "transaction_vectorizer.pkl")

print("✅ Model trained and saved successfully!")
