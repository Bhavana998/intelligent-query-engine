"""Test if the fix worked"""
import sys
print("Testing imports...")

try:
    from app.config import get_config
    config = get_config()
    print("✓ Config loaded")
    print("  API Key:", config.OPENROUTER_API_KEY[:20] + "...")
    print("  Model:", config.LLM_MODEL)
except Exception as e:
    print("✗ Config error:", e)
    sys.exit(1)

try:
    from app.sql_generator import SQLGenerator
    print("✓ SQL generator loaded")
except Exception as e:
    print("✗ SQL generator error:", e)
    sys.exit(1)

try:
    from app.llm_insights import LLMInsights
    print("✓ LLM insights loaded")
except Exception as e:
    print("✗ LLM insights error:", e)
    sys.exit(1)

try:
    from app.main import app
    print("✓ Main app loaded")
except Exception as e:
    print("✗ Main app error:", e)
    sys.exit(1)

print("\n✅ All imports successful! You can now run the server.")