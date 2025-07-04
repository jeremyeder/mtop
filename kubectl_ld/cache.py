"""Caching and performance optimization for kubectl-ld."""

import asyncio
import time
import weakref
from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar, Union
from threading import RLock
from pathlib import Path

from .interfaces import Logger
from .container import inject, singleton

T = TypeVar('T')


@dataclass
class CacheEntry(Generic[T]):
    """Cache entry with metadata."""
    value: T
    created_at: float
    accessed_at: float
    access_count: int
    ttl: Optional[float] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if entry is expired."""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def touch(self) -> None:
        """Update access time and count."""
        self.accessed_at = time.time()
        self.access_count += 1


class LRUCache(Generic[T]):
    """Least Recently Used cache with TTL support."""
    
    def __init__(self, max_size: int = 128, default_ttl: Optional[float] = None) -> None:
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry[T]] = {}
        self._access_order: Dict[str, int] = {}
        self._counter = 0
        self._lock = RLock()
    
    def get(self, key: str) -> Optional[T]:
        """Get value from cache."""
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if entry.is_expired:
                del self._cache[key]
                if key in self._access_order:
                    del self._access_order[key]
                return None
            
            entry.touch()
            self._access_order[key] = self._counter
            self._counter += 1
            
            return entry.value
    
    def put(self, key: str, value: T, ttl: Optional[float] = None) -> None:
        """Put value in cache."""
        with self._lock:
            # Use default TTL if not specified
            effective_ttl = ttl if ttl is not None else self.default_ttl
            
            entry = CacheEntry(
                value=value,
                created_at=time.time(),
                accessed_at=time.time(),
                access_count=1,
                ttl=effective_ttl
            )
            
            self._cache[key] = entry
            self._access_order[key] = self._counter
            self._counter += 1
            
            # Evict if over capacity
            if len(self._cache) > self.max_size:
                self._evict_lru()
    
    def invalidate(self, key: str) -> bool:
        """Remove key from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                if key in self._access_order:
                    del self._access_order[key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all entries."""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
            self._counter = 0
    
    def _evict_lru(self) -> None:
        """Evict least recently used entry."""
        if not self._access_order:
            return
        
        # Find LRU key
        lru_key = min(self._access_order.keys(), key=lambda k: self._access_order[k])
        del self._cache[lru_key]
        del self._access_order[lru_key]
    
    @property
    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_accesses = sum(entry.access_count for entry in self._cache.values())
            return {
                'size': len(self._cache),
                'max_size': self.max_size,
                'total_accesses': total_accesses,
                'entries': {
                    key: {
                        'access_count': entry.access_count,
                        'age': time.time() - entry.created_at,
                        'ttl': entry.ttl
                    }
                    for key, entry in self._cache.items()
                }
            }


class AsyncCache(Generic[T]):
    """Async-aware cache for concurrent operations."""
    
    def __init__(self, max_size: int = 128, default_ttl: Optional[float] = None) -> None:
        self._cache = LRUCache[T](max_size, default_ttl)
        self._pending: Dict[str, asyncio.Future[T]] = {}
        self._lock = asyncio.Lock()
    
    async def get_or_compute(
        self, 
        key: str, 
        compute_func: Any,  # Coroutine[Any, Any, T] but simplified for compatibility
        ttl: Optional[float] = None
    ) -> T:
        """Get value from cache or compute it."""
        # Check cache first
        cached_value = self._cache.get(key)
        if cached_value is not None:
            return cached_value
        
        async with self._lock:
            # Check if computation is already pending
            if key in self._pending:
                return await self._pending[key]
            
            # Check cache again (might have been populated while waiting for lock)
            cached_value = self._cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Start computation
            future = asyncio.create_task(compute_func)
            self._pending[key] = future
            
            try:
                result = await future
                self._cache.put(key, result, ttl)
                return result
            finally:
                del self._pending[key]
    
    def invalidate(self, key: str) -> bool:
        """Remove key from cache."""
        return self._cache.invalidate(key)
    
    def clear(self) -> None:
        """Clear all entries."""
        self._cache.clear()
    
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            **self._cache.stats(),
            'pending_computations': len(self._pending)
        }


@singleton(object)  # Using object as placeholder for CacheManager interface
class CacheManager:
    """Global cache manager."""
    
    def __init__(self, logger: Optional[Logger] = None) -> None:
        self.logger = logger or inject(Logger)
        self._caches: Dict[str, Union[LRUCache[Any], AsyncCache[Any]]] = {}
        self._memory_limit = 100 * 1024 * 1024  # 100MB default
    
    def get_cache(self, name: str, async_cache: bool = False, **kwargs: Any) -> Union[LRUCache[Any], AsyncCache[Any]]:
        """Get or create a named cache."""
        if name not in self._caches:
            if async_cache:
                self._caches[name] = AsyncCache(**kwargs)
            else:
                self._caches[name] = LRUCache(**kwargs)
        
        return self._caches[name]
    
    def clear_all(self) -> None:
        """Clear all caches."""
        for cache in self._caches.values():
            cache.clear()
        self.logger.info("Cleared all caches")
    
    def stats(self) -> Dict[str, Any]:
        """Get statistics for all caches."""
        return {
            name: cache.stats()
            for name, cache in self._caches.items()
        }
    
    def cleanup_expired(self) -> None:
        """Cleanup expired entries from all caches."""
        # This is handled automatically by the cache implementations
        # But we can add periodic cleanup here if needed
        pass


class MemoryOptimizedList(Generic[T]):
    """Memory-optimized list that uses weak references when possible."""
    
    def __init__(self, use_weak_refs: bool = False) -> None:
        self._items: list[Union[T, weakref.ref[T]]] = []
        self._use_weak_refs = use_weak_refs
    
    def append(self, item: T) -> None:
        """Add item to list."""
        if self._use_weak_refs and hasattr(item, '__weakref__'):
            try:
                weak_item = weakref.ref(item)
                self._items.append(weak_item)
            except TypeError:
                # Object doesn't support weak references
                self._items.append(item)
        else:
            self._items.append(item)
    
    def __iter__(self):
        """Iterate over live items."""
        for item in self._items:
            if isinstance(item, weakref.ref):
                live_item = item()
                if live_item is not None:
                    yield live_item
            else:
                yield item
    
    def __len__(self) -> int:
        """Get count of live items."""
        return sum(1 for _ in self)
    
    def cleanup_dead_refs(self) -> int:
        """Remove dead weak references and return count removed."""
        if not self._use_weak_refs:
            return 0
        
        live_items = []
        removed_count = 0
        
        for item in self._items:
            if isinstance(item, weakref.ref):
                if item() is not None:
                    live_items.append(item)
                else:
                    removed_count += 1
            else:
                live_items.append(item)
        
        self._items = live_items
        return removed_count


class StreamingJSONParser:
    """Memory-efficient JSON parser for large datasets."""
    
    def __init__(self, max_memory: int = 50 * 1024 * 1024) -> None:  # 50MB
        self.max_memory = max_memory
        self._buffer_size = 8192
    
    def parse_large_json_file(self, file_path: Path):
        """Parse large JSON file in chunks."""
        import ijson
        
        try:
            with open(file_path, 'rb') as f:
                # Use ijson for streaming parsing
                parser = ijson.parse(f)
                
                current_object = {}
                objects = []
                path_stack = []
                
                for prefix, event, value in parser:
                    # Simple streaming parser - can be enhanced based on JSON structure
                    if event == 'start_map':
                        path_stack.append(prefix)
                    elif event == 'end_map':
                        if path_stack:
                            path_stack.pop()
                        if len(path_stack) == 0 and current_object:
                            objects.append(current_object)
                            current_object = {}
                    elif event in ('string', 'number', 'boolean', 'null'):
                        if len(path_stack) == 1:  # Top-level object
                            current_object[prefix.split('.')[-1]] = value
                
                return objects
        except ImportError:
            # Fallback to regular JSON parsing
            import json
            with open(file_path, 'r') as f:
                return json.load(f)