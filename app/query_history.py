from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any
from app.database import SessionLocal
from app.models import QueryHistory as QueryHistoryModel

class QueryHistoryManager:
    @staticmethod
    async def save(user_id: int, question: str, sql: str, results: List[Dict], execution_time: float):
        """Save query to history"""
        db = SessionLocal()
        try:
            history = QueryHistoryModel(
                user_id=user_id,
                question=question,
                sql_generated=sql,
                result_summary=f"Found {len(results)} records",
                result_count=len(results),
                execution_time_ms=execution_time
            )
            db.add(history)
            db.commit()
            return history.id
        except Exception as e:
            print(f"Failed to save history: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    @staticmethod
    async def get_history(user_id: int, limit: int = 10, offset: int = 0) -> List[Dict]:
        """Get query history for a user"""
        db = SessionLocal()
        try:
            queries = db.query(QueryHistoryModel)\
                .filter(QueryHistoryModel.user_id == user_id)\
                .order_by(desc(QueryHistoryModel.created_at))\
                .limit(limit)\
                .offset(offset)\
                .all()
            
            return [q.to_dict() for q in queries]
        finally:
            db.close()
    
    @staticmethod
    async def get_analytics(user_id: int) -> Dict[str, Any]:
        """Get query analytics for a user"""
        db = SessionLocal()
        try:
            # Total queries
            total_queries = db.query(func.count(QueryHistoryModel.id))\
                .filter(QueryHistoryModel.user_id == user_id)\
                .scalar() or 0
            
            # Average execution time
            avg_exec_time = db.query(func.avg(QueryHistoryModel.execution_time_ms))\
                .filter(QueryHistoryModel.user_id == user_id)\
                .scalar() or 0
            
            # Most common query patterns (by result count)
            common_queries = db.query(
                QueryHistoryModel.question,
                func.count(QueryHistoryModel.id).label('frequency')
            ).filter(QueryHistoryModel.user_id == user_id)\
             .group_by(QueryHistoryModel.question)\
             .order_by(func.count(QueryHistoryModel.id).desc())\
             .limit(5)\
             .all()
            
            # Average result count per query
            avg_results = db.query(func.avg(QueryHistoryModel.result_count))\
                .filter(QueryHistoryModel.user_id == user_id)\
                .scalar() or 0
            
            # Last 7 days activity
            seven_days_ago = func.datetime('now', '-7 days')
            recent_activity = db.query(func.count(QueryHistoryModel.id))\
                .filter(QueryHistoryModel.user_id == user_id)\
                .filter(QueryHistoryModel.created_at >= seven_days_ago)\
                .scalar() or 0
            
            return {
                "user_id": user_id,
                "total_queries": total_queries,
                "average_execution_time_ms": round(float(avg_exec_time), 2),
                "average_results_per_query": round(float(avg_results), 2),
                "queries_last_7_days": recent_activity,
                "most_frequent_queries": [
                    {"question": q[0], "frequency": q[1]} 
                    for q in common_queries
                ]
            }
        finally:
            db.close()
    
    @staticmethod
    async def delete_old_history(user_id: int, days: int = 30):
        """Delete queries older than specified days"""
        db = SessionLocal()
        try:
            cutoff_date = func.datetime('now', f'-{days} days')
            deleted = db.query(QueryHistoryModel)\
                .filter(QueryHistoryModel.user_id == user_id)\
                .filter(QueryHistoryModel.created_at < cutoff_date)\
                .delete()
            db.commit()
            return deleted
        except Exception as e:
            print(f"Failed to delete old history: {e}")
            db.rollback()
            return 0
        finally:
            db.close()