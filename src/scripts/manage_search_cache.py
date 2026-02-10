"""
Command-line tool to manage and analyze search cache.

Usage:
    python scripts/manage_search_cache.py stats
    python scripts/manage_search_cache.py cleanup --days 90
    python scripts/manage_search_cache.py export --output domains.json
    python scripts/manage_search_cache.py query "Polish folk art"
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.search_cache import SearchCache


def format_bytes(bytes_val: int) -> str:
    """Format bytes as human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.2f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.2f} TB"


def cmd_stats(cache: SearchCache):
    """Display cache statistics."""
    stats = cache.get_statistics()
    
    print("\n" + "="*60)
    print("SEARCH CACHE STATISTICS")
    print("="*60)
    
    print(f"\nTotal Queries: {stats['total_queries']:,}")
    print(f"Total API Cost: ${stats['total_cost_dollars']:.2f}")
    
    print("\n--- By API ---")
    for api, data in stats['by_api'].items():
        cost = data['cost_cents'] / 100
        print(f"  {api}: {data['count']:,} queries (${cost:.2f})")
    
    print("\n--- Storage ---")
    storage = stats['storage']
    print(f"  Database Size: {format_bytes(storage['database_bytes'])}")
    print(f"  Uncompressed: {format_bytes(storage['uncompressed_bytes'])}")
    print(f"  Compressed: {format_bytes(storage['compressed_bytes'])}")
    print(f"  Compression: {storage['compression_ratio_percent']:.1f}% reduction")
    
    print("\n--- Top Domains ---")
    for domain in stats['top_domains'][:10]:
        category = f"[{domain['category']}]" if domain['category'] else ""
        print(f"  {domain['domain']:30} {category:15} {domain['queries']:>5} queries")
    
    print("\n" + "="*60)


def cmd_cleanup(cache: SearchCache, days: int):
    """Clean up old cache entries."""
    print(f"\nCleaning up entries older than {days} days...")
    
    removed = cache.cleanup_old_entries(days)
    
    print(f"✓ Removed {removed} old entries")
    
    # Show new stats
    stats = cache.get_statistics()
    print(f"  Remaining: {stats['total_queries']} queries")
    print(f"  Database size: {format_bytes(stats['storage']['database_bytes'])}")


def cmd_export(cache: SearchCache, output: str):
    """Export domains to JSON."""
    print(f"\nExporting domains to {output}...")
    
    domains = cache.export_domains()
    
    with open(output, 'w', encoding='utf-8') as f:
        json.dump({
            'exported_at': datetime.now().isoformat(),
            'count': len(domains),
            'domains': domains
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Exported {len(domains)} domains")


def cmd_query(cache: SearchCache, query: str, search_type: str):
    """Check if query is cached."""
    print(f"\nChecking cache for: {query}")
    print(f"Type: {search_type}")
    
    result = cache.get_cached_search(query, search_type)
    
    if result:
        record, results = result
        print("\n✓ FOUND IN CACHE")
        print(f"  Query Hash: {record.query_hash}")
        print(f"  Results: {record.result_count}")
        print(f"  API: {record.api_name}")
        print(f"  Domain: {record.domain or 'All'}")
        print(f"  Cached: {record.timestamp}")
        print(f"  Cost: ${record.cost_cents/100:.2f}")
    else:
        print("\n✗ NOT FOUND IN CACHE")
        print("  This query would require a new API call")


def main():
    parser = argparse.ArgumentParser(
        description='Manage search cache database',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--db',
        default='data/search_cache.db',
        help='Path to cache database (default: data/search_cache.db)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Stats command
    subparsers.add_parser('stats', help='Show cache statistics')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Remove old entries')
    cleanup_parser.add_argument(
        '--days',
        type=int,
        default=90,
        help='Remove entries older than N days (default: 90)'
    )
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export domains to JSON')
    export_parser.add_argument(
        '--output',
        default='data/domains_export.json',
        help='Output file path'
    )
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Check if query is cached')
    query_parser.add_argument('text', help='Query text to check')
    query_parser.add_argument(
        '--type',
        default='text',
        choices=['text', 'image', 'reverse_image'],
        help='Search type (default: text)'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Initialize cache
    cache = SearchCache(args.db)
    
    # Execute command
    if args.command == 'stats':
        cmd_stats(cache)
    elif args.command == 'cleanup':
        cmd_cleanup(cache, args.days)
    elif args.command == 'export':
        cmd_export(cache, args.output)
    elif args.command == 'query':
        cmd_query(cache, args.text, args.type)


if __name__ == '__main__':
    main()
