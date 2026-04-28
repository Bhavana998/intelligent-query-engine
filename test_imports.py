"""Test imports to identify the exact error"""
import sys
print("Python version:", sys.version)
print("\nTesting imports...")

try:
    print("1. Testing config...")
    from app.config import get_config
    config = get_config()
    print(f"   ✓ Config loaded. Model: {config.LLM_MODEL}")
except Exception as e:
    print(f"   ✗ Config error: {e}")
    sys.exit(1)

try:
    print("2. Testing database...")
    from app.database import engine
    print("   ✓ Database loaded")
except Exception as e:
    print(f"   ✗ Database error: {e}")

try:
    print("3. Testing models...")
    from app.models import Transaction
    print("   ✓ Models loaded")
except Exception as e:
    print(f"   ✗ Models error: {e}")

try:
    print("4. Testing SQL generator...")
    from app.sql_generator import SQLGenerator
    print("   ✓ SQL generator loaded")
except Exception as e:
    print(f"   ✗ SQL generator error: {e}")
    import traceback
    traceback.print_exc()

try:
    print("5. Testing LLM insights...")
    from app.llm_insights import LLMInsights
    print("   ✓ LLM insights loaded")
except Exception as e:
    print(f"   ✗ LLM insights error: {e}")

try:
    print("6. Testing cache...")
    from app.cache import CacheManager
    print("   ✓ Cache loaded")
except Exception as e:
    print(f"   ✗ Cache error: {e}")

try:
    print("7. Testing history...")
    from app.query_history import QueryHistoryManager
    print("   ✓ History loaded")
except Exception as e:
    print(f"   ✗ History error: {e}")

print("\n✅ All imports tested!")