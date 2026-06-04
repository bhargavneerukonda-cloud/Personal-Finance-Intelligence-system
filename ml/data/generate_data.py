"""
Synthetic transaction data generator.
Produces realistic transaction data for ML model training without requiring real bank data.
Run: python generate_data.py --n-users 100 --transactions-per-user 500
"""
import argparse
import uuid
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()
random.seed(42)
np.random.seed(42)

CATEGORIES = {
    "Food & Dining": {
        "merchants": ["McDonald's", "Starbucks", "Chipotle", "Subway", "Pizza Hut",
                      "Domino's", "Panera Bread", "Chick-fil-A", "Taco Bell", "Olive Garden",
                      "DoorDash", "Uber Eats", "Grubhub", "Local Restaurant"],
        "amount_range": (3, 150),
        "frequency_weight": 0.28,
    },
    "Shopping": {
        "merchants": ["Amazon", "Walmart", "Target", "Best Buy", "eBay", "Etsy",
                      "Costco", "Home Depot", "IKEA", "Zara", "H&M", "Nike"],
        "amount_range": (10, 500),
        "frequency_weight": 0.18,
    },
    "Transportation": {
        "merchants": ["Uber", "Lyft", "Shell", "Chevron", "BP", "ExxonMobil",
                      "Metro Transit", "Parking Authority", "Enterprise Rent-A-Car"],
        "amount_range": (5, 120),
        "frequency_weight": 0.12,
    },
    "Entertainment": {
        "merchants": ["Netflix", "Spotify", "AMC Theaters", "Steam", "PlayStation",
                      "Disney+", "Hulu", "Apple TV+", "Concert Tickets", "Event Tickets"],
        "amount_range": (5, 200),
        "frequency_weight": 0.10,
    },
    "Healthcare": {
        "merchants": ["CVS Pharmacy", "Walgreens", "Rite Aid", "Doctor's Office",
                      "Dental Clinic", "Eye Care", "Urgent Care", "Hospital"],
        "amount_range": (10, 500),
        "frequency_weight": 0.07,
    },
    "Utilities": {
        "merchants": ["Electric Company", "Gas Company", "Water Authority",
                      "AT&T", "Verizon", "Comcast", "T-Mobile"],
        "amount_range": (30, 300),
        "frequency_weight": 0.08,
    },
    "Housing": {
        "merchants": ["Landlord", "Property Management", "Mortgage Payment",
                      "HOA Fee", "Home Insurance"],
        "amount_range": (500, 3000),
        "frequency_weight": 0.05,
    },
    "Groceries": {
        "merchants": ["Whole Foods", "Trader Joe's", "Kroger", "Safeway",
                      "Publix", "Aldi", "Lidl", "Wegmans", "Stop & Shop"],
        "amount_range": (20, 300),
        "frequency_weight": 0.12,
    },
}


def generate_user_profile():
    income_level = random.choice(["low", "medium", "high"])
    multipliers = {"low": 0.6, "medium": 1.0, "high": 2.0}
    return {
        "user_id": str(uuid.uuid4()),
        "income_level": income_level,
        "spend_multiplier": multipliers[income_level],
    }


def generate_transactions(user_profile: dict, n_transactions: int, start_date: datetime):
    transactions = []
    categories = list(CATEGORIES.keys())
    weights = [CATEGORIES[c]["frequency_weight"] for c in categories]

    for _ in range(n_transactions):
        category = random.choices(categories, weights=weights)[0]
        cat_data = CATEGORIES[category]
        merchant = random.choice(cat_data["merchants"])
        amount_min, amount_max = cat_data["amount_range"]

        # Apply user spend multiplier
        amount = round(
            random.uniform(amount_min, amount_max) * user_profile["spend_multiplier"] *
            np.random.lognormal(0, 0.3),  # log-normal noise
            2
        )

        # Random date within range
        days_offset = random.randint(0, 365)
        tx_date = start_date + timedelta(days=days_offset)

        # Occasional anomaly (2% of transactions)
        is_anomaly = random.random() < 0.02
        if is_anomaly:
            amount *= random.uniform(5, 20)

        transactions.append({
            "transaction_id": str(uuid.uuid4()),
            "user_id": user_profile["user_id"],
            "amount": round(amount, 2),
            "merchant_name": merchant,
            "description": f"{merchant} - {fake.bs()}",
            "category": category,
            "transaction_date": tx_date.strftime("%Y-%m-%d"),
            "day_of_week": tx_date.weekday(),
            "day_of_month": tx_date.day,
            "month": tx_date.month,
            "is_weekend": tx_date.weekday() >= 5,
            "is_anomaly": is_anomaly,
        })

    return transactions


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic transaction data")
    parser.add_argument("--n-users", type=int, default=100)
    parser.add_argument("--transactions-per-user", type=int, default=500)
    parser.add_argument("--output", type=str, default="data/processed/transactions.csv")
    args = parser.parse_args()

    print(f"Generating data for {args.n_users} users, {args.transactions_per_user} transactions each...")
    start_date = datetime(2023, 1, 1)
    all_transactions = []

    for i in range(args.n_users):
        if (i + 1) % 10 == 0:
            print(f"  {i + 1}/{args.n_users} users...")
        profile = generate_user_profile()
        txs = generate_transactions(profile, args.transactions_per_user, start_date)
        all_transactions.extend(txs)

    df = pd.DataFrame(all_transactions)
    df.to_csv(args.output, index=False)
    print(f"\nGenerated {len(df)} transactions → {args.output}")
    print(f"Category distribution:\n{df['category'].value_counts()}")
    print(f"Anomaly rate: {df['is_anomaly'].mean():.2%}")


if __name__ == "__main__":
    main()
