#!/usr/bin/env python3
import sys
import os

# Disable interactive mode
sys.argv = [sys.argv[0]]
"""
Initialize database with sample transactions for the Intelligent Query Engine
"""
import sys
import random
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from app.database import engine, SessionLocal
from app.models import Base, Transaction

def init_database():
    """Create all database tables"""
    print("🗄️  Creating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully")
    return True

def seed_sample_data():
    """Populate database with sample transactions"""
    print("\n📊 Seeding sample data...")
    db = SessionLocal()
    
    categories = ['food', 'transport', 'entertainment', 'shopping', 'bills', 'health']
    merchants = {
        'food': ['McDonalds', 'Pizza Hut', 'Starbucks', 'Whole Foods', 'Local Cafe', 'Chipotle', 'Subway'],
        'transport': ['Uber', 'Lyft', 'Metro', 'Gas Station', 'Parking', 'Taxi', 'Bus'],
        'entertainment': ['Netflix', 'Spotify', 'Cinema', 'Concert', 'Steam', 'Disney+', 'HBO Max'],
        'shopping': ['Amazon', 'Walmart', 'Target', 'Best Buy', 'Zara', 'Nike', 'Apple Store'],
        'bills': ['Electric Co', 'Water Dept', 'Internet Provider', 'Phone Bill', 'Rent', 'Insurance'],
        'health': ['Pharmacy', 'Gym', 'Doctor Visit', 'Dental Care', 'CVS', 'Walgreens']
    }
    
    transactions = []
    
    # Generate 3 months of data for user 1 (active user)
    print("   Generating data for User 1...")
    for days_ago in range(90):
        date = datetime.now() - timedelta(days=days_ago)
        
        # 3-7 transactions per day for user 1 (active)
        num_transactions = random.randint(3, 7)
        for _ in range(num_transactions):
            category = random.choice(categories)
            merchant = random.choice(merchants[category])
            amount = round(random.uniform(5, 200), 2)
            
            transactions.append(Transaction(
                user_id=1,
                amount=amount,
                category=category,
                merchant=merchant,
                transaction_date=date
            ))
    
    # Generate 1 month of data for user 2 (less active)
    print("   Generating data for User 2...")
    for days_ago in range(30):
        date = datetime.now() - timedelta(days=days_ago)
        
        # 1-3 transactions per day for user 2
        num_transactions = random.randint(1, 3)
        for _ in range(num_transactions):
            category = random.choice(categories)
            merchant = random.choice(merchants[category])
            amount = round(random.uniform(10, 300), 2)
            
            transactions.append(Transaction(
                user_id=2,
                amount=amount,
                category=category,
                merchant=merchant,
                transaction_date=date
            ))
    
    # Generate 2 weeks of data for user 3 (new user)
    print("   Generating data for User 3...")
    for days_ago in range(14):
        date = datetime.now() - timedelta(days=days_ago)
        
        # 2-4 transactions per day for user 3
        num_transactions = random.randint(2, 4)
        for _ in range(num_transactions):
            category = random.choice(categories)
            merchant = random.choice(merchants[category])
            amount = round(random.uniform(5, 150), 2)
            
            transactions.append(Transaction(
                user_id=3,
                amount=amount,
                category=category,
                merchant=merchant,
                transaction_date=date
            ))
    
    # Bulk insert
    db.bulk_save_objects(transactions)
    db.commit()
    
    print(f"✅ Inserted {len(transactions)} sample transactions")
    return len(transactions)

def show_sample_data():
    """Display sample data for verification"""
    db = SessionLocal()
    
    print("\n📋 Sample data preview:")
    print("-" * 60)
    
    for user_id in [1, 2, 3]:
        print(f"\n👤 User {user_id} (last 3 transactions):")
        sample = db.query(Transaction)\
            .filter(Transaction.user_id == user_id)\
            .order_by(Transaction.transaction_date.desc())\
            .limit(3)\
            .all()
        
        for t in sample:
            print(f"   📅 {t.transaction_date.strftime('%Y-%m-%d')} | "
                  f"🏷️  {t.category:12} | "
                  f"🏪 {t.merchant[:15]:15} | "
                  f"💰 ${t.amount:8.2f}")
    
    db.close()

def test_queries():
    """Test some example queries to verify setup"""
    db = SessionLocal()
    
    print("\n🔍 Testing example queries:")
    print("-" * 60)
    
    tests = [
        ("Food spending this month (User 1)", 
         "SELECT COALESCE(SUM(amount), 0) as total FROM transactions WHERE user_id = 1 AND category = 'food' AND strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now')"),
        
        ("Top merchant (User 1)",
         "SELECT merchant, SUM(amount) as total FROM transactions WHERE user_id = 1 GROUP BY merchant ORDER BY total DESC LIMIT 1"),
        
        ("Average transaction (User 1)",
         "SELECT AVG(amount) as avg FROM transactions WHERE user_id = 1"),
        
        ("Transaction count last week (User 1)",
         "SELECT COUNT(*) as count FROM transactions WHERE user_id = 1 AND transaction_date >= date('now', '-7 days')"),
        
        ("Total spending by category (User 1)",
         "SELECT category, SUM(amount) as total FROM transactions WHERE user_id = 1 GROUP BY category ORDER BY total DESC LIMIT 3")
    ]
    
    for description, sql in tests:
        try:
            # Wrap SQL with text() function
            result = db.execute(text(sql)).fetchone()
            if result:
                # Convert to dict for display
                if hasattr(result, '_mapping'):
                    result_dict = dict(result._mapping)
                    print(f"   ✅ {description}: {result_dict}")
                else:
                    print(f"   ✅ {description}: {result[0]}")
            else:
                print(f"   ⚠️  {description}: No results")
        except Exception as e:
            print(f"   ❌ {description}: Error - {e}")
    
    db.close()

def get_database_stats():
    """Get database statistics"""
    db = SessionLocal()
    
    total_transactions = db.query(Transaction).count()
    total_users = db.query(Transaction.user_id).distinct().count()
    
    # Get date range using text() for raw SQL
    result = db.execute(text("SELECT MIN(transaction_date), MAX(transaction_date) FROM transactions"))
    date_range = result.fetchone()
    
    print("\n📊 Database Statistics:")
    print("-" * 60)
    print(f"   📝 Total transactions: {total_transactions}")
    print(f"   👥 Total users: {total_users}")
    if date_range[0] and date_range[1]:
        print(f"   📅 Date range: {date_range[0]} to {date_range[1]}")
    
    # Per user stats - FIXED: use func from sqlalchemy import
    for user_id in [1, 2, 3]:
        count = db.query(Transaction).filter(Transaction.user_id == user_id).count()
        total = db.query(func.sum(Transaction.amount)).filter(Transaction.user_id == user_id).scalar() or 0
        print(f"   👤 User {user_id}: {count} transactions, ${total:.2f} total")
    
    # Check food transactions for last month
    result = db.execute(text("""
        SELECT 
            COUNT(*) as count,
            COALESCE(SUM(amount), 0) as total
        FROM transactions 
        WHERE user_id = 1 
            AND category = 'food'
            AND strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now', '-1 month')
    """))
    food_data = result.fetchone()
    print(f"\n   🍔 User 1 Food spending last month: {food_data[0]} transactions, ${food_data[1]:.2f}")
    
    # Also show this month's food spending
    result = db.execute(text("""
        SELECT 
            COUNT(*) as count,
            COALESCE(SUM(amount), 0) as total
        FROM transactions 
        WHERE user_id = 1 
            AND category = 'food'
            AND strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now')
    """))
    food_data_current = result.fetchone()
    print(f"   🍕 User 1 Food spending this month: {food_data_current[0]} transactions, ${food_data_current[1]:.2f}")
    
    db.close()

if __name__ == "__main__":
    print("🚀 Intelligent Query Engine - Database Initialization")
    print("=" * 60)
    
    try:
        # Initialize database
        init_database()
        
        # Seed sample data
        seed_sample_data()
        
        # Show sample data
        show_sample_data()
        
        # Run test queries (fixed version)
        test_queries()
        
        # Show database stats
        get_database_stats()
        
        print("\n" + "=" * 60)
        print("✅ Setup complete!")
        print("\n🎯 Next steps:")
        print("   1. Make sure your .env file has OPENROUTER_API_KEY")
        print("   2. Run: uvicorn app.main:app --reload")
        print("   3. Open: http://localhost:8000/docs")
        print("   4. Test with: POST /query")
        print("\n📝 Example curl command:")
        print('   curl -X POST "http://localhost:8000/query" \\')
        print('        -H "Content-Type: application/json" \\')
        print('        -d \'{"user_id": 1, "question": "How much did I spend on food last month?"}\'')
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)