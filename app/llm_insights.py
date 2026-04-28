import httpx
import json
from typing import List, Dict, Any
from app.config import get_config

config = get_config()

class LLMInsights:
    @staticmethod
    async def generate(question: str, results: List[Dict[str, Any]]) -> str:
        """Generate human-readable insights from query results using OpenRouter"""
        
        if not results:
            return "No data found for your query. Try adjusting your question or date range."
        
        # Convert results to readable format (limit to 10 results)
        results_str = json.dumps(results[:10], indent=2, default=str)
        result_count = len(results)
        
        # Get the first result keys for context
        result_keys = list(results[0].keys()) if results else []
        
        prompt = f"""Based on the query results, provide a brief, natural language insight.

User Question: "{question}"
Number of results: {result_count}
Result fields: {', '.join(result_keys)}
Sample results: {results_str}

Generate a 1-2 sentence insight that:
1. Directly answers the user's question
2. Uses conversational language
3. Includes specific numbers when relevant
4. Provides context if the data is interesting or unusual

Insight:"""
        
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
                    {"role": "system", "content": "You are a financial analyst providing concise, helpful insights."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.5,
                "max_tokens": 150
            }
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code != 200:
                    raise Exception("OpenRouter API error: " + response.text)
                
                result = response.json()
                insight = result['choices'][0]['message']['content'].strip()
                
                # Ensure insight is not empty
                if not insight:
                    return LLMInsights._fallback_insight(question, results)
                
                return insight
                
        except Exception as e:
            # Fallback to simple insight generation
            print(f"LLM insight generation failed, using fallback: {e}")
            return LLMInsights._fallback_insight(question, results)
    
    @staticmethod
    def _fallback_insight(question: str, results: List[Dict[str, Any]]) -> str:
        """Simple fallback when LLM fails"""
        if not results:
            return "No transactions found matching your criteria."
        
        # Try to extract meaningful numbers from results
        if len(results) == 1 and isinstance(results[0], dict):
            row = results[0]
            # Look for common field names
            for key in ['total', 'total_spent', 'sum', 'amount', 'average', 'avg', 'count']:
                if key in row and isinstance(row[key], (int, float)):
                    value = row[key]
                    if 'total' in key or 'sum' in key:
                        return f"Your total is ${value:.2f} based on {len(results)} record(s)."
                    elif 'average' in key or 'avg' in key:
                        return f"Your average is ${value:.2f}."
                    elif 'count' in key:
                        return f"Found {int(value)} transaction(s) matching your query."
        
        # General case
        if "spend" in question.lower() or "total" in question.lower():
            return f"Based on {len(results)} records, your total spending is summarized in the results."
        
        if "average" in question.lower():
            return f"Based on {len(results)} records, your average transaction is shown in the results."
        
        if "count" in question.lower() or "how many" in question.lower():
            return f"Found {len(results)} transaction(s) matching your query."
        
        return f"Found {len(results)} matching result(s) for your query."