#!/usr/bin/env python3
"""
Check and analyze database content for the Intelligent Query Engine
"""
from app.database import SessionLocal
from sqlalchemy import text, func
from app.models import Transaction
from datetime import datetime, timedelta

def check_database():
    """Main function to check database content"""
    db = SessionLocal()
    
    print("=" * 70)
    print("📊 INTELLIGENT QUERY ENGINE - DATABASE ANALYSIS")
    print("=" * 70)
    
    # 1. Basic Database Statistics
    print("\n📈 1. BASIC DATABASE STATISTICS")
    print("-" * 70)
    
    total_transactions = db.query(Transaction).count()
    total_users = db.query(Transaction.user_id).distinct().count()
    
    print(f"   📝 Total Transactions: {total_transactions}")
    print(f"   👥 Total Users: {total_users}")
    
    # 2. Date Range
    print("\n📅 2. DATE RANGE")
    print("-" * 70)
    
    result = db.execute(text("""
        SELECT 
            MIN(transaction_date) as first_date,
            MAX(transaction_date) as last_date,
            JULIANDAY(MAX(transaction_date)) - JULIANDAY(MIN(transaction_date)) as days_span
        FROM transactions
    """))
    date_range = result.fetchone()
    
    if date_range[0] and date_range[1]:
        print(f"   📅 First Transaction: {date_range[0]}")
        print(f"   📅 Last Transaction: {date_range[1]}")
        print(f"   📆 Days Span: {int(date_range[2])} days")
    
    # 3. Per User Statistics
    print("\n👤 3. PER USER STATISTICS")
    print("-" * 70)
    
    for user_id in [1, 2, 3]:
        count = db.query(Transaction).filter(Transaction.user_id == user_id).count()
        total = db.query(func.sum(Transaction.amount)).filter(Transaction.user_id == user_id).scalar() or 0
        avg = db.query(func.avg(Transaction.amount)).filter(Transaction.user_id == user_id).scalar() or 0
        min_amount = db.query(func.min(Transaction.amount)).filter(Transaction.user_id == user_id).scalar() or 0
        max_amount = db.query(func.max(Transaction.amount)).filter(Transaction.user_id == user_id).scalar() or 0
        
        print(f"\n   👤 USER {user_id}:")
        print(f"      📊 Transactions: {count}")
        print(f"      💰 Total Spent: ${total:.2f}")
        print(f"      📈 Average Transaction: ${avg:.2f}")
        print(f"      📉 Minimum Amount: ${min_amount:.2f}")
        print(f"      📈 Maximum Amount: ${max_amount:.2f}")
    
    # 4. Category Breakdown for User 1
    print("\n🍕 4. CATEGORY BREAKDOWN (User 1)")
    print("-" * 70)
    
    result = db.execute(text("""
        SELECT 
            category,
            COUNT(*) as count,
            SUM(amount) as total,
            AVG(amount) as avg,
            MIN(amount) as min,
            MAX(amount) as max
        FROM transactions
        WHERE user_id = 1
        GROUP BY category
        ORDER BY total DESC
    """))
    
    print(f"\n   {'Category':15} {'Count':>6} {'Total':>12} {'Average':>10} {'Min':>8} {'Max':>8}")
    print(f"   {'-'*15} {'-'*6} {'-'*12} {'-'*10} {'-'*8} {'-'*8}")
    
    for row in result:
        print(f"   {row[0]:15} {row[1]:6} ${row[2]:11.2f} ${row[3]:9.2f} ${row[4]:7.2f} ${row[5]:7.2f}")
    
    # 5. Food Spending Analysis (User 1)
    print("\n🍔 5. FOOD SPENDING ANALYSIS (User 1)")
    print("-" * 70)
    
    # Get last 3 months of food spending
    for months_ago in range(3):
        result = db.execute(text(f"""
            SELECT 
                strftime('%Y-%m', transaction_date) as month,
                COUNT(*) as count,
                SUM(amount) as total,
                AVG(amount) as avg,
                GROUP_CONCAT(DISTINCT merchant) as merchants
            FROM transactions
            WHERE user_id = 1 
                AND category = 'food'
                AND transaction_date >= date('now', '-{months_ago + 1} months')
                AND transaction_date < date('now', '-{months_ago} months')
        """))
        
        row = result.fetchone()
        if row and row[1] > 0:
            month_name = get_month_name(row[0])
            print(f"\n   📆 {month_name} ({row[0]}):")
            print(f"      🍽️  Transactions: {row[1]}")
            print(f"      💰 Total Spent: ${row[2]:.2f}")
            print(f"      📊 Average: ${row[3]:.2f}")
            if row[4]:
                merchants_list = row[4].split(',')[:3]
                print(f"      🏪 Top Merchants: {', '.join(merchants_list)}")
        else:
            month_name = get_month_name_for_offset(months_ago + 1)
            print(f"\n   📆 {month_name}: No food transactions found")
    
    # 6. Current Month Spending
    print("\n📆 6. CURRENT MONTH SPENDING (User 1)")
    print("-" * 70)
    
    result = db.execute(text("""
        SELECT 
            category,
            COUNT(*) as count,
            SUM(amount) as total
        FROM transactions
        WHERE user_id = 1 
            AND strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now')
        GROUP BY category
        ORDER BY total DESC
    """))
    
    print(f"\n   {'Category':15} {'Count':>6} {'Total':>12}")
    print(f"   {'-'*15} {'-'*6} {'-'*12}")
    
    for row in result:
        print(f"   {row[0]:15} {row[1]:6} ${row[2]:11.2f}")
    
    # 7. Last Week Spending
    print("\n📆 7. LAST 7 DAYS SPENDING (User 1)")
    print("-" * 70)
    
    result = db.execute(text("""
        SELECT 
            DATE(transaction_date) as day,
            COUNT(*) as count,
            SUM(amount) as total
        FROM transactions
        WHERE user_id = 1 
            AND transaction_date >= DATE('now', '-7 days')
        GROUP BY DATE(transaction_date)
        ORDER BY day DESC
    """))
    
    print(f"\n   {'Day':12} {'Transactions':>12} {'Total Spent':>12}")
    print(f"   {'-'*12} {'-'*12} {'-'*12}")
    
    for row in result:
        print(f"   {row[0]:12} {row[1]:12} ${row[2]:11.2f}")
    
    # 8. Top Merchants (User 1)
    print("\n🏪 8. TOP 10 MERCHANTS BY SPENDING (User 1)")
    print("-" * 70)
    
    result = db.execute(text("""
        SELECT 
            merchant,
            category,
            COUNT(*) as count,
            SUM(amount) as total
        FROM transactions
        WHERE user_id = 1
        GROUP BY merchant
        ORDER BY total DESC
        LIMIT 10
    """))
    
    print(f"\n   {'Merchant':20} {'Category':12} {'Count':>6} {'Total':>12}")
    print(f"   {'-'*20} {'-'*12} {'-'*6} {'-'*12}")
    
    for row in result:
        print(f"   {row[0]:20} {row[1]:12} {row[2]:6} ${row[3]:11.2f}")
    
    # 9. Daily Average Spending
    print("\n📊 9. DAILY AVERAGE SPENDING (User 1)")
    print("-" * 70)
    
    result = db.execute(text("""
        SELECT 
            AVG(daily_total) as avg_daily_spend
        FROM (
            SELECT 
                DATE(transaction_date) as day,
                SUM(amount) as daily_total
            FROM transactions
            WHERE user_id = 1
            GROUP BY DATE(transaction_date)
        )
    """))
    
    avg_daily = result.fetchone()[0] or 0
    print(f"\n   💰 Average Daily Spend: ${avg_daily:.2f}")
    
    # 10. Sample Transactions
    print("\n🔍 10. SAMPLE TRANSACTIONS (User 1 - Last 10)")
    print("-" * 70)
    
    result = db.execute(text("""
        SELECT 
            transaction_date,
            category,
            merchant,
            amount
        FROM transactions
        WHERE user_id = 1
        ORDER BY transaction_date DESC
        LIMIT 10
    """))
    
    print(f"\n   {'Date':20} {'Category':12} {'Merchant':20} {'Amount':>10}")
    print(f"   {'-'*20} {'-'*12} {'-'*20} {'-'*10}")
    
    for row in result:
        print(f"   {row[0]} {row[1]:12} {row[2]:20} ${row[3]:9.2f}")
    
    # 11. Data Quality Check
    print("\n✅ 11. DATA QUALITY CHECK")
    print("-" * 70)
    
    # Check for null values
    null_checks = [
        ("user_id", Transaction.user_id.is_(None)),
        ("amount", Transaction.amount.is_(None)),
        ("category", Transaction.category.is_(None)),
        ("merchant", Transaction.merchant.is_(None)),
        ("transaction_date", Transaction.transaction_date.is_(None)),
    ]
    
    for field, condition in null_checks:
        count = db.query(Transaction).filter(condition).count()
        if count == 0:
            print(f"   ✅ No NULL values in {field}")
        else:
            print(f"   ⚠️  Found {count} NULL values in {field}")
    
    # 12. Recommendations
    print("\n💡 12. RECOMMENDATIONS")
    print("-" * 70)
    
    # Check if user 1 has food data
    food_count = db.query(Transaction).filter(
        Transaction.user_id == 1, 
        Transaction.category == 'food'
    ).count()
    
    if food_count == 0:
        print("   ⚠️  User 1 has NO food transactions!")
        print("      → Run 'python add_food_data.py' to add food transactions")
    else:
        print(f"   ✅ User 1 has {food_count} food transactions")
    
    # Check current month data
    current_month_count = db.query(Transaction).filter(
        Transaction.user_id == 1,
        func.strftime('%Y-%m', Transaction.transaction_date) == datetime.now().strftime('%Y-%m')
    ).count()
    
    if current_month_count == 0:
        print("   ⚠️  No transactions found for current month")
    else:
        print(f"   ✅ Found {current_month_count} transactions for current month")
    
    print("\n" + "=" * 70)
    print("✅ DATABASE ANALYSIS COMPLETE")
    print("=" * 70)
    
    db.close()

def get_month_name(year_month):
    """Convert YYYY-MM to month name"""
    if not year_month:
        return "Unknown"
    try:
        year, month = year_month.split('-')
        month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                      'July', 'August', 'September', 'October', 'November', 'December']
        return f"{month_names[int(month)-1]} {year}"
    except:
        return year_month

def get_month_name_for_offset(months_ago):
    """Get month name for X months ago"""
    current = datetime.now()
    target = current - timedelta(days=30*months_ago)
    return target.strftime('%B %Y')

def quick_check():
    """Quick check for most important info"""
    db = SessionLocal()
    
    print("\n⚡ QUICK CHECK - Most Important Info:")
    print("-" * 50)
    
    # Total food spending for user 1
    result = db.execute(text("""
        SELECT 
            SUM(amount) as total,
            COUNT(*) as count
        FROM transactions
        WHERE user_id = 1 AND category = 'food'
    """))
    row = result.fetchone()
    print(f"🍔 User 1 Total Food: ${row[0] or 0:.2f} ({row[1] or 0} transactions)")
    
    # Food spending last month
    result = db.execute(text("""
        SELECT SUM(amount) as total
        FROM transactions
        WHERE user_id = 1 
            AND category = 'food'
            AND strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now', '-1 month')
    """))
    row = result.fetchone()
    print(f"📆 Food Last Month: ${row[0] or 0:.2f}")
    
    # Food spending this month
    result = db.execute(text("""
        SELECT SUM(amount) as total
        FROM transactions
        WHERE user_id = 1 
            AND category = 'food'
            AND strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now')
    """))
    row = result.fetchone()
    print(f"📆 Food This Month: ${row[0] or 0:.2f}")
    
    db.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--quick':
        quick_check()
    else:
        check_database()
        
        print("\n📌 TIP: Run 'python check_data.py --quick' for a quick summary")