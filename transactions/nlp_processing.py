import re


CATEGORY_KEYWORDS = {
    "salary": "Salary",
    "deposit": "Salary",
    "bonus": "Salary",
    "freelance": "Income",
    "food": "Food",
    "restaurant": "Food",
    "dining": "Food",
    "rent": "Rent",
    "shopping": "Shopping",
    "groceries": "Groceries",
    "supermarket": "Groceries",
    "subscription": "Subscription",
    "netflix": "Subscription",
    "spotify": "Subscription",
    "electricity": "Bills",
    "water": "Bills",
    "internet": "Bills",
    "insurance": "Insurance",
    "health": "Health",
    "fuel": "Transport",
    "car": "Transport",
    "bus": "Transport",
    "taxi": "Transport",
    "uber": "Transport",
    "loan": "Loans",
    "emi": "Loans",
    "mortgage": "Loans",
    "gift": "Gift",
    "donation": "Donation",
    "charity": "Donation",
    "entertainment": "Entertainment",
    "movie": "Entertainment",
    "concert": "Entertainment",
    "travel": "Travel",
    "flight": "Travel",
    "hotel": "Travel",
    "vacation": "Travel",
}

INCOME_HINTS = {"salary", "bonus", "deposit", "freelance", "income", "credited", "received"}


def _extract_amount(text: str) -> float:
    matches = re.findall(r"(?:rs\.?|inr|\$|€|₹)?\s*(\d+(?:[\.,]\d{1,2})?)", text, flags=re.IGNORECASE)
    if not matches:
        return 0.0
    try:
        return float(matches[0].replace(",", ""))
    except ValueError:
        return 0.0


def process_voice_transaction(voice_text):
    """Extract transaction amount, type, and category from free text."""
    normalized = (voice_text or "").strip().lower()
    tokens = re.findall(r"[a-zA-Z]+", normalized)

    amount = _extract_amount(normalized)
    category = "General"
    transaction_type = "expense"

    for token in tokens:
        if token in CATEGORY_KEYWORDS:
            category = CATEGORY_KEYWORDS[token]
            break

    if any(token in INCOME_HINTS for token in tokens):
        transaction_type = "income"
    elif category in {"Salary", "Income"}:
        transaction_type = "income"

    return {
        "amount": amount,
        "transaction_type": transaction_type,
        "category": category,
    }
