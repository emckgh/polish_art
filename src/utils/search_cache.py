"""
Efficient search cache for tracking API queries and results.

Uses SQLite for fast lookups with minimal disk space:
- Query hashes for deduplication
- Compressed JSON for results
- Domain normalization for aggregation
- Automatic expiration for stale data

Storage optimization:
- Hash-based keys (~32 bytes vs 100s for full query)
- ZLIB compression on result JSON (~70% reduction)
- Indexed lookups (O(1) hash table performance)
- Automatic cleanup of old/unused entries
"""

import sqlite3
import hashlib
import json
import zlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from pathlib import Path
from urllib.parse import urlparse
from dataclasses import dataclass, asdict


@dataclass
class SearchRecord:
    """Represents a cached search query and results."""
    query_hash: str
    query_text: str
    search_type: str  # 'text', 'image', 'reverse_image'
    domain_hash: str  # Normalized domain identifier
    domain: str  # Original domain for display
    result_count: int
    timestamp: str
    api_name: str  # 'google_custom_search', 'vision_api', etc.
    cost_cents: int  # Track API cost in cents
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SearchCache:
    """
    Efficient search cache with hash-based deduplication.
    
    Storage format:
    - queries table: query metadata, indexed by hash
    - results table: compressed result JSON
    - domains table: normalized domain lookup
    """
    
    def __init__(self, db_path: str = "data/search_cache.db"):
        """
        Initialize search cache.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Create database schema if not exists."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Domains table - normalized domain names
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS domains (
                domain_hash TEXT PRIMARY KEY,
                domain TEXT NOT NULL,
                category TEXT,  -- 'museum', 'auction', 'archive', etc.
                added_date TEXT NOT NULL
            )
        """)
        
        # Queries table - search metadata
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS queries (
                query_hash TEXT PRIMARY KEY,
                query_text TEXT NOT NULL,
                search_type TEXT NOT NULL,
                domain_hash TEXT,
                api_name TEXT NOT NULL,
                result_count INTEGER DEFAULT 0,
                cost_cents INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                last_accessed TEXT NOT NULL,
                access_count INTEGER DEFAULT 1,
                FOREIGN KEY (domain_hash) REFERENCES domains(domain_hash)
            )
        """)
        
        # Results table - compressed JSON blobs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS results (
                query_hash TEXT PRIMARY KEY,
                compressed_data BLOB NOT NULL,
                uncompressed_size INTEGER NOT NULL,
                compressed_size INTEGER NOT NULL,
                FOREIGN KEY (query_hash) REFERENCES queries(query_hash)
            )
        """)
        
        # Indexes for fast lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queries_created 
            ON queries(created_at)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queries_domain 
            ON queries(domain_hash)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_queries_api 
            ON queries(api_name)
        """)
        
        conn.commit()
        conn.close()
    
    @staticmethod
    def _hash_query(query: str, search_type: str, domain: Optional[str] = None) -> str:
        """
        Generate deterministic hash for query.
        
        Args:
            query: Search query text
            search_type: Type of search
            domain: Optional domain restriction
        
        Returns:
            16-character hex hash (64 bits)
        """
        # Normalize query
        normalized = query.lower().strip()
        
        # Create hash input
        hash_input = f"{normalized}|{search_type}|{domain or ''}"
        
        # Use first 64 bits of SHA256 (16 hex chars)
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
    
    @staticmethod
    def _hash_domain(domain: str) -> str:
        """
        Generate hash for domain name.
        
        Args:
            domain: Domain name (e.g., 'polona.pl')
        
        Returns:
            8-character hex hash (32 bits)
        """
        normalized = domain.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()[:8]
    
    @staticmethod
    def _normalize_domain(url_or_domain: str) -> str:
        """
        Extract and normalize domain from URL or domain string.
        
        Args:
            url_or_domain: URL or domain string
        
        Returns:
            Normalized domain (e.g., 'polona.pl')
        """
        if '://' in url_or_domain:
            parsed = urlparse(url_or_domain)
            domain = parsed.netloc
        else:
            domain = url_or_domain
        
        # Remove www prefix
        if domain.startswith('www.'):
            domain = domain[4:]
        
        return domain.lower().strip()
    
    @staticmethod
    def _compress_json(data: Any) -> Tuple[bytes, int, int]:
        """
        Compress JSON data using zlib.
        
        Args:
            data: Data to compress
        
        Returns:
            (compressed_bytes, uncompressed_size, compressed_size)
        """
        json_str = json.dumps(data, separators=(',', ':'))  # Compact JSON
        json_bytes = json_str.encode('utf-8')
        compressed = zlib.compress(json_bytes, level=9)  # Max compression
        
        return compressed, len(json_bytes), len(compressed)
    
    @staticmethod
    def _decompress_json(compressed: bytes) -> Any:
        """
        Decompress JSON data.
        
        Args:
            compressed: Compressed bytes
        
        Returns:
            Original data
        """
        json_bytes = zlib.decompress(compressed)
        json_str = json_bytes.decode('utf-8')
        return json.loads(json_str)
    
    def store_search(
        self,
        query: str,
        search_type: str,
        results: List[Dict[str, Any]],
        api_name: str,
        domain: Optional[str] = None,
        cost_cents: int = 0,
        domain_category: Optional[str] = None
    ) -> str:
        """
        Store search query and results.
        
        Args:
            query: Search query text
            search_type: Type of search ('text', 'image', 'reverse_image')
            results: List of result dictionaries
            api_name: API used ('google_custom_search', 'vision_api')
            domain: Optional domain restriction
            cost_cents: API cost in cents
            domain_category: Category for domain ('museum', 'auction', etc.)
        
        Returns:
            Query hash
        """
        query_hash = self._hash_query(query, search_type, domain)
        timestamp = datetime.now().isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Store domain if provided
            domain_hash = None
            if domain:
                normalized_domain = self._normalize_domain(domain)
                domain_hash = self._hash_domain(normalized_domain)
                
                cursor.execute("""
                    INSERT OR IGNORE INTO domains (domain_hash, domain, category, added_date)
                    VALUES (?, ?, ?, ?)
                """, (domain_hash, normalized_domain, domain_category, timestamp))
            
            # Store query metadata
            cursor.execute("""
                INSERT OR REPLACE INTO queries 
                (query_hash, query_text, search_type, domain_hash, api_name, 
                 result_count, cost_cents, created_at, last_accessed, access_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            """, (
                query_hash, query, search_type, domain_hash, api_name,
                len(results), cost_cents, timestamp, timestamp
            ))
            
            # Compress and store results
            compressed, orig_size, comp_size = self._compress_json(results)
            
            cursor.execute("""
                INSERT OR REPLACE INTO results 
                (query_hash, compressed_data, uncompressed_size, compressed_size)
                VALUES (?, ?, ?, ?)
            """, (query_hash, compressed, orig_size, comp_size))
            
            conn.commit()
            return query_hash
            
        finally:
            conn.close()
    
    def get_cached_search(
        self,
        query: str,
        search_type: str,
        domain: Optional[str] = None,
        max_age_days: Optional[int] = None
    ) -> Optional[Tuple[SearchRecord, List[Dict[str, Any]]]]:
        """
        Retrieve cached search results.
        
        Args:
            query: Search query text
            search_type: Type of search
            domain: Optional domain restriction
            max_age_days: Maximum age of cached results (None = no limit)
        
        Returns:
            (SearchRecord, results_list) or None if not found/expired
        """
        query_hash = self._hash_query(query, search_type, domain)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Fetch query metadata
            cursor.execute("""
                SELECT q.*, d.domain
                FROM queries q
                LEFT JOIN domains d ON q.domain_hash = d.domain_hash
                WHERE q.query_hash = ?
            """, (query_hash,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            # Check age if specified
            if max_age_days:
                created_at = datetime.fromisoformat(row[6])
                age = datetime.now() - created_at
                if age > timedelta(days=max_age_days):
                    return None
            
            # Create record
            record = SearchRecord(
                query_hash=row[0],
                query_text=row[1],
                search_type=row[2],
                domain_hash=row[3] or '',
                domain=row[10] or '',
                result_count=row[5],
                timestamp=row[6],
                api_name=row[4],
                cost_cents=row[6]
            )
            
            # Fetch compressed results
            cursor.execute("""
                SELECT compressed_data FROM results WHERE query_hash = ?
            """, (query_hash,))
            
            compressed_row = cursor.fetchone()
            if not compressed_row:
                return None
            
            # Decompress results
            results = self._decompress_json(compressed_row[0])
            
            # Update access tracking
            cursor.execute("""
                UPDATE queries 
                SET last_accessed = ?, access_count = access_count + 1
                WHERE query_hash = ?
            """, (datetime.now().isoformat(), query_hash))
            
            conn.commit()
            
            return record, results
            
        finally:
            conn.close()
    
    def is_cached(
        self,
        query: str,
        search_type: str,
        domain: Optional[str] = None
    ) -> bool:
        """
        Check if query is cached (fast lookup without loading results).
        
        Args:
            query: Search query text
            search_type: Type of search
            domain: Optional domain restriction
        
        Returns:
            True if cached
        """
        query_hash = self._hash_query(query, search_type, domain)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT 1 FROM queries WHERE query_hash = ? LIMIT 1
            """, (query_hash,))
            
            return cursor.fetchone() is not None
            
        finally:
            conn.close()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Total queries
            cursor.execute("SELECT COUNT(*) FROM queries")
            total_queries = cursor.fetchone()[0]
            
            # Total API cost
            cursor.execute("SELECT SUM(cost_cents) FROM queries")
            total_cost = cursor.fetchone()[0] or 0
            
            # By API
            cursor.execute("""
                SELECT api_name, COUNT(*), SUM(cost_cents)
                FROM queries
                GROUP BY api_name
            """)
            by_api = {row[0]: {'count': row[1], 'cost_cents': row[2]} 
                     for row in cursor.fetchall()}
            
            # By domain
            cursor.execute("""
                SELECT d.domain, d.category, COUNT(q.query_hash)
                FROM domains d
                LEFT JOIN queries q ON d.domain_hash = q.domain_hash
                GROUP BY d.domain_hash
                ORDER BY COUNT(q.query_hash) DESC
                LIMIT 20
            """)
            top_domains = [
                {'domain': row[0], 'category': row[1], 'queries': row[2]}
                for row in cursor.fetchall()
            ]
            
            # Storage efficiency
            cursor.execute("""
                SELECT SUM(uncompressed_size), SUM(compressed_size)
                FROM results
            """)
            storage = cursor.fetchone()
            uncompressed = storage[0] or 0
            compressed = storage[1] or 0
            compression_ratio = (1 - compressed / uncompressed) * 100 if uncompressed > 0 else 0
            
            # Database file size
            db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
            
            return {
                'total_queries': total_queries,
                'total_cost_cents': total_cost,
                'total_cost_dollars': total_cost / 100,
                'by_api': by_api,
                'top_domains': top_domains,
                'storage': {
                    'database_bytes': db_size,
                    'database_mb': db_size / (1024 * 1024),
                    'uncompressed_bytes': uncompressed,
                    'compressed_bytes': compressed,
                    'compression_ratio_percent': compression_ratio
                }
            }
            
        finally:
            conn.close()
    
    def cleanup_old_entries(self, days: int = 90) -> int:
        """
        Remove entries older than specified days.
        
        Args:
            days: Age threshold in days
        
        Returns:
            Number of entries removed
        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get old query hashes
            cursor.execute("""
                SELECT query_hash FROM queries WHERE created_at < ?
            """, (cutoff,))
            old_hashes = [row[0] for row in cursor.fetchall()]
            
            if not old_hashes:
                return 0
            
            # Delete results
            cursor.execute(f"""
                DELETE FROM results 
                WHERE query_hash IN ({','.join('?' * len(old_hashes))})
            """, old_hashes)
            
            # Delete queries
            cursor.execute(f"""
                DELETE FROM queries 
                WHERE query_hash IN ({','.join('?' * len(old_hashes))})
            """, old_hashes)
            
            # Clean up orphaned domains
            cursor.execute("""
                DELETE FROM domains 
                WHERE domain_hash NOT IN (SELECT DISTINCT domain_hash FROM queries)
            """)
            
            conn.commit()
            
            # Vacuum to reclaim space
            cursor.execute("VACUUM")
            
            return len(old_hashes)
            
        finally:
            conn.close()
    
    def export_domains(self) -> List[Dict[str, Any]]:
        """
        Export all domains for analysis.
        
        Returns:
            List of domain records
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT d.domain, d.category, d.added_date, COUNT(q.query_hash) as query_count
                FROM domains d
                LEFT JOIN queries q ON d.domain_hash = q.domain_hash
                GROUP BY d.domain_hash
                ORDER BY query_count DESC
            """)
            
            return [
                {
                    'domain': row[0],
                    'category': row[1],
                    'added_date': row[2],
                    'query_count': row[3]
                }
                for row in cursor.fetchall()
            ]
            
        finally:
            conn.close()
