import hashlib
import json
from typing import Optional, Any
from datetime import datetime, timedelta
from app.config import get_config

config = get_config()

# Try to import Redis
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

class CacheManager:
    def __init__(self):
        self.in_memory_cache = {}
        self.redis_client = None
        
        if config.USE_REDIS and REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(config.REDIS_URL, decode_responses=True)
                print("✅ Redis cache initialized")
            except Exception as e:
                print(f"⚠️ Redis connection failed: {e}, using in-memory cache")
                self.redis_client = None
        else:
            print("📦 Using in-memory cache")
    
    def _get_key(self, user_id: int, question: str) -> str:
        """Generate cache key"""
        content = f"{user_id}:{question.lower().strip()}"
        return f"query_cache:{hashlib.md5(content.encode()).hexdigest()}"
    
    async def get(self, user_id: int, question: str) -> Optional[Any]:
        """Get cached response"""
        key = self._get_key(user_id, question)
        
        if self.redis_client:
            try:
                cached = self.redis_client.get(key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                print(f"Redis get error: {e}")
        
        # Check in-memory cache
        elif key in self.in_memory_cache:
            entry = self.in_memory_cache[key]
            if datetime.now() < entry['expires_at']:
                return entry['data']
            else:
                del self.in_memory_cache[key]
        
        return None
    
    async def set(self, user_id: int, question: str, data: Any):
        """Cache the response"""
        key = self._get_key(user_id, question)
        
        if self.redis_client:
            try:
                self.redis_client.setex(
                    key, 
                    config.CACHE_TTL, 
                    json.dumps(data, default=str)
                )
            except Exception as e:
                print(f"Redis set error: {e}")
        
        # Store in memory cache
        self.in_memory_cache[key] = {
            'data': data,
            'expires_at': datetime.now() + timedelta(seconds=config.CACHE_TTL)
        }
    
    async def clear(self, user_id: int = None):
        """Clear cache (optionally for specific user)"""
        if self.redis_client:
            try:
                if user_id:
                    # Pattern delete for user
                    pattern = f"query_cache:{hashlib.md5(f'{user_id}:'.encode()).hexdigest()[:10]}*"
                    keys = self.redis_client.keys(pattern)
                    if keys:
                        self.redis_client.delete(*keys)
                else:
                    self.redis_client.flushdb()
            except Exception as e:
                print(f"Redis clear error: {e}")
        
        # Clear in-memory cache
        if user_id:
            pattern = hashlib.md5(f"{user_id}:".encode()).hexdigest()[:10]
            to_delete = [k for k in self.in_memory_cache if pattern in k]
            for k in to_delete:
                del self.in_memory_cache[k]
        else:
            self.in_memory_cache.clear()
    
    async def get_stats(self) -> dict:
        """Get cache statistics"""
        if self.redis_client:
            try:
                keys = self.redis_client.keys("query_cache:*")
                return {
                    "type": "redis",
                    "total_keys": len(keys),
                    "ttl_seconds": config.CACHE_TTL
                }
            except:
                pass
        
        return {
            "type": "in_memory",
            "total_keys": len(self.in_memory_cache),
            "ttl_seconds": config.CACHE_TTL
        }