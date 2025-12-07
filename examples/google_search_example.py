"""
Example usage of Google Image Search integration.

This script demonstrates various ways to use the Google Image Search API
to discover and import artwork images into the Polish Art Database.

Before running:
1. Set up Google Custom Search API (see docs/google_image_search_setup.md)
2. Set environment variables:
   $env:GOOGLE_API_KEY = "your-api-key"
   $env:GOOGLE_SEARCH_ENGINE_ID = "your-search-engine-id"
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.google_image_search import (
    GoogleImageSearch,
    format_results_summary,
    download_image
)


def example_basic_search():
    """Example 1: Basic image search."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Search")
    print("="*80)
    
    searcher = GoogleImageSearch()
    
    results = searcher.search_artwork_images(
        query="Polish folk art pottery",
        num_results=5
    )
    
    print(format_results_summary(results))


def example_filtered_search():
    """Example 2: Search with filters."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Filtered Search")
    print("="*80)
    
    searcher = GoogleImageSearch()
    
    results = searcher.search_artwork_images(
        query="Polish painting 19th century",
        num_results=5,
        image_size='large',      # Only large images
        image_type='photo',      # Only photos
        file_type='jpg',         # Only JPEGs
        country='pl'             # Focus on Polish results
    )
    
    print(format_results_summary(results))


def example_artist_search():
    """Example 3: Search for specific artist."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Artist Search")
    print("="*80)
    
    searcher = GoogleImageSearch()
    
    results = searcher.search_polish_art(
        artist="Jan Matejko",
        style="historical painting",
        num_results=5
    )
    
    print(format_results_summary(results))


def example_paginated_search():
    """Example 4: Get more than 10 results with pagination."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Paginated Search (25 results)")
    print("="*80)
    
    searcher = GoogleImageSearch()
    
    results = searcher.search_paginated(
        query="Polish folk art",
        total_results=25,
        image_size='large',
        file_type='jpg'
    )
    
    print(f"\nFetched {len(results)} results total")
    print(f"API requests made: {searcher.get_request_count()}")
    
    # Show first 3 results
    print("\nFirst 3 results:")
    print(format_results_summary(results[:3]))


def example_download_images():
    """Example 5: Download images to local directory."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Download Images")
    print("="*80)
    
    searcher = GoogleImageSearch()
    
    results = searcher.search_artwork_images(
        query="Polish traditional costume",
        num_results=3,
        image_size='large'
    )
    
    print(f"Found {len(results)} images")
    
    # Create output directory
    output_dir = Path('data/examples/downloads')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Download each image
    for i, result in enumerate(results, 1):
        filename = f"costume_{i}.jpg"
        filepath = output_dir / filename
        
        print(f"\nDownloading {i}/{len(results)}: {result.title}")
        print(f"  From: {result.display_link}")
        
        if download_image(result.link, str(filepath)):
            print(f"  ✓ Saved to {filepath}")
        else:
            print(f"  ✗ Download failed")


def example_export_metadata():
    """Example 6: Export search results with metadata."""
    print("\n" + "="*80)
    print("EXAMPLE 6: Export Metadata")
    print("="*80)
    
    searcher = GoogleImageSearch()
    
    results = searcher.search_polish_art(
        artist="Stanisław Wyspiański",
        style="portrait",
        num_results=5
    )
    
    print(f"\nFound {len(results)} results")
    
    # Create structured output
    import json
    from datetime import datetime
    
    output_data = {
        'search_query': 'Stanisław Wyspiański portrait',
        'timestamp': datetime.now().isoformat(),
        'count': len(results),
        'images': []
    }
    
    for result in results:
        output_data['images'].append({
            'title': result.title,
            'url': result.link,
            'thumbnail': result.thumbnail_link,
            'source': result.context_link,
            'domain': result.display_link,
            'description': result.snippet,
            'dimensions': {
                'width': result.width,
                'height': result.height
            },
            'format': result.file_format,
            'mime_type': result.mime_type
        })
    
    # Save to JSON
    output_file = Path('data/examples/search_results.json')
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\nMetadata exported to {output_file}")
    print("\nSample result:")
    print(json.dumps(output_data['images'][0], indent=2, ensure_ascii=False))


def example_search_variations():
    """Example 7: Try different search strategies."""
    print("\n" + "="*80)
    print("EXAMPLE 7: Search Strategy Comparison")
    print("="*80)
    
    searcher = GoogleImageSearch()
    
    strategies = [
        ("Broad search", {"query": "Polish art", "num_results": 3}),
        ("Specific period", {"query": "Polish art 19th century", "num_results": 3}),
        ("Art style", {"query": "Polish folk art", "num_results": 3}),
        ("Artist focus", {"query": "Jan Matejko Battle of Grunwald", "num_results": 3}),
    ]
    
    for name, params in strategies:
        print(f"\n{name}: {params['query']}")
        print("-" * 60)
        
        results = searcher.search_artwork_images(**params)
        print(f"  Found {len(results)} results")
        
        if results:
            print(f"  Example: {results[0].title}")
            print(f"  From: {results[0].display_link}")


def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("GOOGLE IMAGE SEARCH API - EXAMPLES")
    print("="*80)
    
    try:
        # Check if credentials are set
        import os
        if not os.getenv('GOOGLE_API_KEY') or not os.getenv('GOOGLE_SEARCH_ENGINE_ID'):
            print("\n⚠ WARNING: API credentials not set!")
            print("\nPlease set environment variables:")
            print("  $env:GOOGLE_API_KEY = 'your-api-key'")
            print("  $env:GOOGLE_SEARCH_ENGINE_ID = 'your-search-engine-id'")
            print("\nSee docs/google_image_search_setup.md for setup instructions.")
            return
        
        # Run examples
        example_basic_search()
        input("\nPress Enter to continue to next example...")
        
        example_filtered_search()
        input("\nPress Enter to continue to next example...")
        
        example_artist_search()
        input("\nPress Enter to continue to next example...")
        
        example_paginated_search()
        input("\nPress Enter to continue to next example...")
        
        example_download_images()
        input("\nPress Enter to continue to next example...")
        
        example_export_metadata()
        input("\nPress Enter to continue to next example...")
        
        example_search_variations()
        
        print("\n" + "="*80)
        print("All examples completed!")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
