from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import time
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import asynccontextmanager

from app.database import get_db, engine
from app.models import Base
from app.sql_generator import SQLGenerator
from app.llm_insights import LLMInsights
from app.cache import CacheManager
from app.query_history import QueryHistoryManager
from app.config import get_config

# Create tables on startup
Base.metadata.create_all(bind=engine)

# Initialize components
cache_manager = CacheManager()
config = get_config()

# Request/Response Models
class QueryRequest(BaseModel):
    user_id: int = Field(..., description="User ID to query data for", gt=0)
    question: str = Field(..., description="Natural language question about transactions", min_length=3)

class QueryResponse(BaseModel):
    question: str
    sql: str
    results: List[Dict[str, Any]]
    insights: str
    execution_time_ms: float
    from_cache: bool = False
    result_count: int = 0

class ErrorResponse(BaseModel):
    error: str
    details: Optional[str] = None
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    cache_type: str
    database: str
    llm_model: str

# Create FastAPI app
app = FastAPI(
    title="Intelligent Query Engine",
    description="Convert natural language to SQL and get AI-powered insights from financial transactions",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Helper function for SQL execution
async def execute_sql(db: Session, sql: str) -> List[Dict[str, Any]]:
    """Execute SQL query safely and return results as list of dictionaries"""
    try:
        # Wrap the SQL string with text() function
        sql_statement = text(sql)
        result = db.execute(sql_statement)
        
        # Convert to list of dictionaries
        if result.returns_rows:
            columns = result.keys()
            rows = result.fetchall()
            return [dict(zip(columns, row)) for row in rows]
        else:
            return []
    except Exception as e:
        raise Exception(f"SQL execution failed: {str(e)}")

# API Endpoints
@app.post("/query", response_model=QueryResponse, summary="Process natural language query")
async def process_query(
    request: QueryRequest, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Process a natural language query and return results with AI-generated insights.
    
    Features:
    - Converts English questions to SQL
    - Executes queries safely
    - Caches repeated queries
    - Tracks query history
    - Generates human-readable insights
    """
    start_time = time.time()
    
    try:
        # 1. Check cache
        cached_result = await cache_manager.get(request.user_id, request.question)
        if cached_result:
            execution_time = (time.time() - start_time) * 1000
            cached_result["execution_time_ms"] = execution_time
            cached_result["from_cache"] = True
            return cached_result
        
        # 2. Generate SQL from natural language
        sql = await SQLGenerator.generate(request.question, request.user_id)
        
        # 3. Execute SQL safely
        results = await execute_sql(db, sql)
        
        # 4. Generate insights
        insights = await LLMInsights.generate(request.question, results)
        
        # 5. Prepare response
        execution_time = (time.time() - start_time) * 1000
        
        response = {
            "question": request.question,
            "sql": sql,
            "results": results,
            "insights": insights,
            "execution_time_ms": round(execution_time, 2),
            "from_cache": False,
            "result_count": len(results)
        }
        
        # 6. Cache response (background task)
        background_tasks.add_task(cache_manager.set, request.user_id, request.question, response)
        
        # 7. Save to history (background task)
        background_tasks.add_task(
            QueryHistoryManager.save, 
            request.user_id, 
            request.question, 
            sql, 
            results,
            execution_time
        )
        
        return response
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query processing failed: {str(e)}")

@app.get("/history/{user_id}", response_model=Dict, summary="Get query history")
async def get_history(
    user_id: int, 
    limit: int = 10, 
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get query history for a specific user"""
    try:
        history = await QueryHistoryManager.get_history(user_id, limit, offset)
        return {
            "user_id": user_id,
            "total_returned": len(history),
            "history": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/analytics/{user_id}", response_model=Dict, summary="Get query analytics")
async def get_analytics(user_id: int, db: Session = Depends(get_db)):
    """Get analytics and usage statistics for a user"""
    try:
        analytics = await QueryHistoryManager.get_analytics(user_id)
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/cache/{user_id}", summary="Clear user cache")
async def clear_user_cache(user_id: int):
    """Clear cached queries for a specific user"""
    await cache_manager.clear(user_id)
    return {"message": f"Cache cleared for user {user_id}", "user_id": user_id}

@app.delete("/cache", summary="Clear all cache")
async def clear_all_cache():
    """Clear entire cache"""
    await cache_manager.clear()
    return {"message": "All cache cleared"}

@app.get("/cache/stats", summary="Get cache statistics")
async def get_cache_stats():
    """Get cache statistics"""
    stats = await cache_manager.get_stats()
    return stats

@app.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check():
    """Check API health and configuration"""
    # Test database connection
    db_status = "connected"
    try:
        from app.database import SessionLocal
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
    except:
        db_status = "disconnected"
    
    return HealthResponse(
        status="healthy",
        cache_type="redis" if config.USE_REDIS else "in-memory",
        database=db_status,
        llm_model=config.LLM_MODEL
    )

@app.get("/", summary="Root endpoint")
async def root():
    """API information"""
    return {
        "name": "Intelligent Query Engine",
        "version": "2.0.0",
        "docs": "/docs",
        "endpoints": [
            "POST /query - Process natural language query",
            "GET /history/{user_id} - View query history",
            "GET /analytics/{user_id} - Get usage analytics",
            "DELETE /cache/{user_id} - Clear user cache",
            "GET /health - Health check"
        ]
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            details=str(exc.detail),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        ).dict()
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            details=str(exc),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        ).dict()
    )