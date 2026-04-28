# add_food_data.py
from app.database import SessionLocal
from app.models import Transaction
from datetime import datetime, timedelta
from sqlalchemy import text

def add_food_transactions():
    db = SessionLocal()
    
    # Get current date and last month
    now = datetime.now()
    last_month = now - timedelta(days=30)
    
    # Food transactions for last month
    food_transactions = [
        Transaction(
            user_id=1,
            amount=25.50,
            category='food',
            merchant='Pizza Hut',
            transaction_date=last_month - timedelta(days=5)
        ),
        Transaction(
            user_id=1,
            amount=15.75,
            category='food',
            merchant='Starbucks',
            transaction_date=last_month - timedelta(days=8)
        ),
        Transaction(
            user_id=1,
            amount=45.00,
            category='food',
            merchant='Whole Foods',
            transaction_date=last_month - timedelta(days=12)
        ),
        Transaction(
            user_id=1,
            amount=32.50,
            category='food',
            merchant='Chipotle',
            transaction_date=last_month - timedelta(days=15)
        ),
        Transaction(
            user_id=1,
            amount=68.30,
            category='food',
            merchant='Local Restaurant',
            transaction_date=last_month - timedelta(days=20)
        ),
        Transaction(
            user_id=1,
            amount=12.99,
            category='food',
            merchant='Starbucks',
            transaction_date=last_month - timedelta(days=25)
        ),
    ]
    
    # Add transactions
    db.add_all(food_transactions)
    db.commit()
    
    total = sum(t.amount for t in food_transactions)
    print(f"✅ Added {len(food_transactions)} food transactions")
    print(f"💰 Total added: ${total:.2f}")
    print(f"📅 Date range: {last_month - timedelta(days=25)} to {last_month - timedelta(days=5)}")
    
    db.close()

if __name__ == "__main__":
    add_food_transactions()