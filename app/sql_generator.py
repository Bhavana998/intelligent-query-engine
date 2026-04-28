import re
import httpx
from app.config import get_config

config = get_config()

class SQLGenerator:
    @staticmethod
    async def generate(question: str, user_id: int) -> str:
        """Convert natural language to SQL query using OpenRouter"""
        
        prompt = f"""You are a SQL expert. Convert this question into a SQL query.

Question: "{question}"
User ID: {user_id}

Table schema:
- transactions: id (INT), user_id (INT), amount (FLOAT), category (VARCHAR), merchant (VARCHAR), transaction_date (TIMESTAMP)

Requirements:
1. Always filter by user_id = {user_id}
2. Use proper date filtering (last month, last week, this year, etc.)
3. Use appropriate aggregations (SUM, COUNT, AVG, MAX, MIN)
4. Use COALESCE for aggregations that might return NULL
5. Return ONLY the SQL query, no explanations or markdown

Examples:
Q: "How much did I spend on food last month?"
A: SELECT COALESCE(SUM(amount), 0) as total_spent FROM transactions WHERE user_id = {user_id} AND category = 'food' AND strftime('%Y-%m', transaction_date) = strftime('%Y-%m', 'now', '-1 month')

Q: "What's my average transaction amount?"
A: SELECT COALESCE(AVG(amount), 0) as average_amount FROM transactions WHERE user_id = {user_id}

Q: "Where did I spend the most money?"
A: SELECT merchant, SUM(amount) as total FROM transactions WHERE user_id = {user_id} GROUP BY merchant ORDER BY total DESC LIMIT 1

Q: "How many transactions did I make last week?"
A: SELECT COUNT(*) as transaction_count FROM transactions WHERE user_id = {user_id} AND transaction_date >= date('now', '-7 days')

Q: "What are my top 3 spending categories?"
A: SELECT category, SUM(amount) as total FROM transactions WHERE user_id = {user_id} GROUP BY category ORDER BY total DESC LIMIT 3

Now generate SQL for: {question}

SQL Query:"""
        
        try:
            # Build URL and headers without f-strings that might contain API key
            url = config.OPENROUTER_BASE_URL + "/chat/completions"
            headers = {
                "Authorization": "Bearer " + config.OPENROUTER_API_KEY,
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",
                "X-Title": "Intelligent Query Engine"
            }
            
            payload = {
                "model": config.LLM_MODEL,
                "messages": [
                    {"role": "system", "content": "You are a SQL expert. Generate only SQL queries, no explanations."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 500
            }
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code != 200:
                    error_detail = response.text
                    raise Exception("OpenRouter API error (status " + str(response.status_code) + "): " + error_detail)
                
                result = response.json()
                sql = result['choices'][0]['message']['content'].strip()
                sql = SQLGenerator._clean_sql(sql)
                SQLGenerator._validate_sql(sql)
                
                return sql
                
        except httpx.TimeoutException:
            raise Exception("OpenRouter API timeout - please try again")
        except Exception as e:
            raise Exception("SQL generation failed: " + str(e))
    
    @staticmethod
    def _clean_sql(sql: str) -> str:
        """Remove markdown and clean SQL"""
        # Remove markdown code blocks
        sql = re.sub(r'```sql\n?', '', sql)
        sql = re.sub(r'```\n?', '', sql)
        sql = re.sub(r'^SQL:\s*', '', sql, flags=re.IGNORECASE)
        sql = re.sub(r'^sql\s*', '', sql, flags=re.IGNORECASE)
        
        # Remove trailing semicolon if present
        sql = sql.rstrip(';')
        
        return sql.strip()
    
    @staticmethod
    def _validate_sql(sql: str):
        """Validate SQL for safety"""
        if not sql:
            raise ValueError("Generated SQL is empty")
        
        sql_upper = sql.upper()
        
        # Block dangerous operations
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 
                             'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE', 'MERGE',
                             'REPLACE', 'EXEC', 'EXECUTE']
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValueError("Dangerous SQL operation detected: " + keyword)
        
        # Ensure it's a SELECT query
        if not sql_upper.strip().startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed. Got: " + sql[:50])
        
        # Check for multiple statements
        if ';' in sql and sql.count(';') > 1:  # Allow trailing semicolon but not multiple
            raise ValueError("Multiple SQL statements are not allowed")