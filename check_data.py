# check_data.py
from app.database import SessionLocal
from sqlalchemy import text
from datetime import datetime, timedelta

db = SessionLocal()

print("=== Checking Database Content ===\n")

# 1. Check all transactions for user 1
result = db.execute(text("SELECT COUNT(*) as count FROM transactions WHERE user_id = 1"))
count = result.fetchone()
print(f"📊 Total transactions for user 1: {count[0]}")

# 2. Check date range
result = db.execute(text("""
    SELECT MIN(transaction_date) as min_date, MAX(transaction_date) as max_date 
    FROM transactions WHERE user_id = 1
"""))
row = result.fetchone()
print(f"📅 Date range: {row[0]} to {row[1]}")

# 3. Check food transactions specifically
result = db.execute(text("""
    SELECT 
        COUNT(*) as food_count,
        SUM(amount) as food_total,
        MIN(transaction_date) as first_food,
        MAX(transaction_date) as last_food
    FROM transactions 
    WHERE user_id = 1 AND category = 'food'
"""))
row = result.fetchone()
print(f"\n🍔 Food transactions for user 1:")
print(f"   Count: {row[0]}")
print(f"   Total: ${row[1] if row[1] else 0}")
print(f"   Date range: {row[2]} to {row[3]}")

# 4. Check what "last month" means in SQLite
result = db.execute(text("""
    SELECT 
        date('now') as today,
        date('now', '-1 month') as one_month_ago,
        strftime('%Y-%m', 'now', '-1 month') as last_month_ym
"""))
row = result.fetchone()
print(f"\n📆 Date calculations:")
print(f"   Today: {row[0]}")
print(f"   One month ago: {row[1]}")
print(f"   Last month (YYYY-MM): {row[2]}")

# 5. Check food transactions in the last 30 days
result = db.execute(text("""
    SELECT 
        COUNT(*) as count_30days,
        SUM(amount) as total_30days
    FROM transactions 
    WHERE user_id = 1 
        AND category = 'food'
        AND transaction_date >= date('now', '-30 days')
"""))
row = result.fetchone()
print(f"\n🍕 Food transactions (last 30 days):")
print(f"   Count: {row[0]}")
print(f"   Total: ${row[1] if row[1] else 0}")

# 6. Sample food transactions
result = db.execute(text("""
    SELECT transaction_date, amount, merchant
    FROM transactions 
    WHERE user_id = 1 AND category = 'food'
    ORDER BY transaction_date DESC
    LIMIT 5
"""))
food_transactions = result.fetchall()
print(f"\n🔍 Sample food transactions:")
for t in food_transactions:
    print(f"   {t[0]} - ${t[1]} at {t[2]}")

db.close()