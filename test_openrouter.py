#!/usr/bin/env python3
"""Test script to verify OpenRouter API connection"""
import asyncio
import os
import sys
from dotenv import load_dotenv
import httpx

load_dotenv()

async def test_openrouter():
    """Test OpenRouter API connection and authentication"""
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    model = os.getenv("LLM_MODEL", "openai/gpt-3.5-turbo")
    
    print("🔧 OpenRouter API Test")
    print("=" * 50)
    print(f"📡 API URL: {base_url}")
    print(f"🤖 Model: {model}")
    print(f"🔑 API Key: {'✓ Present' if api_key else '✗ Missing'}")
    
    if not api_key:
        print("\n❌ ERROR: OPENROUTER_API_KEY not found in .env file")
        print("\n💡 To fix:")
        print("   1. Sign up at https://openrouter.ai/")
        print("   2. Get your API key from https://openrouter.ai/keys")
        print("   3. Add it to .env file: OPENROUTER_API_KEY=sk-or-v1-...")
        return False
    
    print("\n🔄 Testing API connection...")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Test with a simple query
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "Intelligent Query Engine Test"
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Say 'OpenRouter connection successful!' in exactly those words."}
                    ],
                    "max_tokens": 20,
                    "temperature": 0
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                message = result['choices'][0]['message']['content']
                print(f"\n✅ SUCCESS! API responded with:")
                print(f"   {message}")
                
                # Show available info
                print("\n📊 Connection Details:")
                print(f"   Status: Connected")
                print(f"   Model: {model}")
                print(f"   Response time: {response.elapsed.total_seconds():.2f}s")
                
                # Test SQL generation
                print("\n🔄 Testing SQL generation capability...")
                sql_test = await test_sql_generation(client, api_key, base_url, model)
                
                return sql_test
                
            else:
                print(f"\n❌ API Error: HTTP {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
                # Provide helpful error messages
                if response.status_code == 401:
                    print("\n💡 Invalid API key. Please check your OPENROUTER_API_KEY in .env")
                elif response.status_code == 402:
                    print("\n💡 Insufficient credits. Please add credits to your OpenRouter account")
                elif response.status_code == 429:
                    print("\n💡 Rate limit exceeded. Please try again later")
                
                return False
                
        except httpx.TimeoutException:
            print("\n❌ Connection timeout. Please check your internet connection")
            return False
        except Exception as e:
            print(f"\n❌ Connection failed: {e}")
            return False

async def test_sql_generation(client, api_key, base_url, model):
    """Test SQL generation capability"""
    
    prompt = """Convert to SQL: "How much did I spend on food?"
Table: transactions with columns (user_id, amount, category, transaction_date)
Return ONLY the SQL query."""
    
    try:
        response = await client.post(
            f"{base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000"
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 150,
                "temperature": 0.1
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            sql = result['choices'][0]['message']['content']
            print(f"\n✅ SQL Generation Test Successful!")
            print(f"   Generated SQL: {sql[:100]}...")
            return True
        else:
            print(f"\n⚠️  SQL Generation Test Failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n⚠️  SQL Generation Test Error: {e}")
        return False

async def test_models_list():
    """Optional: Fetch available models from OpenRouter"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    base_url = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    
    if not api_key:
        return
    
    print("\n📚 Fetching available models...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            
            if response.status_code == 200:
                models = response.json()
                print(f"   Available models: {len(models.get('data', []))} models found")
                
                # Show some popular models
                popular_models = [
                    "openai/gpt-3.5-turbo",
                    "openai/gpt-4-turbo",
                    "anthropic/claude-3-haiku",
                    "meta-llama/llama-3-70b-instruct"
                ]
                
                print("\n   💡 Popular models you can use in .env:")
                for model in popular_models:
                    print(f"      LLM_MODEL={model}")
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_openrouter())
    
    if success:
        print("\n" + "=" * 50)
        print("✅ All tests passed! Your OpenRouter setup is ready.")
        print("\n🚀 You can now start the API:")
        print("   uvicorn app.main:app --reload")
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("❌ Tests failed. Please fix the issues above.")
        sys.exit(1)