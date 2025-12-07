"""
Command-line script to search for artwork images using Google Custom Search API.

Usage:
    python scripts/search_google_images.py --query "Polish folk art" --num 10
    python scripts/search_google_images.py --artist "Jan Matejko" --style "painting"
    python scripts/search_google_images.py --query "Warsaw uprising art" --download --output data/images

Setup Instructions:
1. Get Google Custom Search API credentials:
   - API Key: https://console.cloud.google.com/apis/credentials
   - Search Engine: https://programmablesearchengine.google.com/
   
2. Set environment variables:
   $env:GOOGLE_API_KEY = "your-api-key"
   $env:GOOGLE_SEARCH_ENGINE_ID = "your-search-engine-id"

3. Run the script:
   python scripts/search_google_images.py --help
"""

import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.google_image_search import (
    GoogleImageSearch,
    format_results_summary,
    download_image
)


def main():
    parser = argparse.ArgumentParser(
        description='Search for artwork images using Google Custom Search API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic search
  python scripts/search_google_images.py --query "Polish folk art pottery"

  # Search for specific artist
  python scripts/search_google_images.py --artist "Stanisław Wyspiański" --num 20

  # Search with filters
  python scripts/search_google_images.py --query "medieval Polish art" --size large --type photo

  # Download images
  python scripts/search_google_images.py --query "Polish paintings" --download --output data/images

  # Export to JSON
  python scripts/search_google_images.py --query "Polish art" --json results.json
        """
    )
    
    # Search parameters
    search_group = parser.add_argument_group('search parameters')
    search_group.add_argument(
        '--query', '-q',
        help='Search query string'
    )
    search_group.add_argument(
        '--artist',
        help='Artist name to search for'
    )
    search_group.add_argument(
        '--period',
        help='Time period (e.g., "19th century", "medieval")'
    )
    search_group.add_argument(
        '--style',
        help='Art style (e.g., "folk art", "portrait", "landscape")'
    )
    search_group.add_argument(
        '--num', '-n',
        type=int,
        default=10,
        help='Number of results to fetch (default: 10, max: 100)'
    )
    
    # Filters
    filter_group = parser.add_argument_group('filters')
    filter_group.add_argument(
        '--size',
        choices=['huge', 'icon', 'large', 'medium', 'small', 'xlarge', 'xxlarge'],
        help='Filter by image size'
    )
    filter_group.add_argument(
        '--type',
        choices=['clipart', 'face', 'lineart', 'stock', 'photo', 'animated'],
        help='Filter by image type'
    )
    filter_group.add_argument(
        '--format',
        choices=['jpg', 'png', 'gif', 'bmp', 'svg', 'webp', 'ico'],
        help='Filter by file format'
    )
    filter_group.add_argument(
        '--rights',
        choices=['cc_publicdomain', 'cc_attribute', 'cc_sharealike', 
                'cc_noncommercial', 'cc_nonderived'],
        help='Filter by usage rights'
    )
    filter_group.add_argument(
        '--country',
        default='pl',
        help='Country code for results (default: pl for Poland)'
    )
    
    # Output options
    output_group = parser.add_argument_group('output options')
    output_group.add_argument(
        '--download', '-d',
        action='store_true',
        help='Download images to local directory'
    )
    output_group.add_argument(
        '--output', '-o',
        type=str,
        default='data/google_images',
        help='Output directory for downloads (default: data/google_images)'
    )
    output_group.add_argument(
        '--json', '-j',
        type=str,
        help='Export results to JSON file'
    )
    output_group.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.query and not args.artist:
        parser.error('Either --query or --artist must be specified')
    
    try:
        # Initialize searcher
        if args.verbose:
            print("Initializing Google Image Search...")
        
        searcher = GoogleImageSearch()
        
        # Perform search
        if args.artist or args.period or args.style:
            if args.verbose:
                print(f"Searching for Polish artwork...")
                print(f"  Artist: {args.artist or 'Any'}")
                print(f"  Period: {args.period or 'Any'}")
                print(f"  Style: {args.style or 'Any'}")
            
            results = searcher.search_polish_art(
                artist=args.artist,
                period=args.period,
                style=args.style,
                num_results=args.num
            )
        else:
            if args.verbose:
                print(f"Searching for: {args.query}")
            
            # Build kwargs for filters
            kwargs = {}
            if args.size:
                kwargs['image_size'] = args.size
            if args.type:
                kwargs['image_type'] = args.type
            if args.format:
                kwargs['file_type'] = args.format
            if args.rights:
                kwargs['rights'] = args.rights
            if args.country:
                kwargs['country'] = args.country
            
            if args.num > 10:
                results = searcher.search_paginated(
                    query=args.query,
                    total_results=args.num,
                    **kwargs
                )
            else:
                results = searcher.search_artwork_images(
                    query=args.query,
                    num_results=args.num,
                    **kwargs
                )
        
        # Display results
        print(format_results_summary(results))
        
        # Download images
        if args.download:
            output_dir = Path(args.output)
            output_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"\nDownloading images to {output_dir}...")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            successful = 0
            
            for i, result in enumerate(results, 1):
                # Create safe filename
                ext = result.file_format or 'jpg'
                filename = f"{timestamp}_{i:03d}.{ext}"
                filepath = output_dir / filename
                
                if args.verbose:
                    print(f"  [{i}/{len(results)}] Downloading {result.link}...")
                
                if download_image(result.link, str(filepath)):
                    successful += 1
                    if args.verbose:
                        print(f"    ✓ Saved to {filepath}")
                else:
                    if args.verbose:
                        print(f"    ✗ Failed")
            
            print(f"\nDownloaded {successful}/{len(results)} images successfully")
        
        # Export to JSON
        if args.json:
            json_data = {
                'query': args.query or f"{args.artist} {args.style or 'art'}",
                'timestamp': datetime.now().isoformat(),
                'count': len(results),
                'results': [r.to_dict() for r in results]
            }
            
            with open(args.json, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            print(f"\nResults exported to {args.json}")
        
        # Print API usage
        if args.verbose:
            print(f"\nAPI requests made: {searcher.get_request_count()}")
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        print("\nMake sure to set environment variables:", file=sys.stderr)
        print("  $env:GOOGLE_API_KEY = 'your-api-key'", file=sys.stderr)
        print("  $env:GOOGLE_SEARCH_ENGINE_ID = 'your-search-engine-id'", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
