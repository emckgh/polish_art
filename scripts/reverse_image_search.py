"""
Command-line script for reverse image search using Google Vision API.

Usage:
    python scripts/reverse_image_search.py image.jpg
    python scripts/reverse_image_search.py image.jpg --json results.json
    python scripts/reverse_image_search.py --batch data/artworks/*.jpg
    python scripts/reverse_image_search.py image.jpg --find-hires

Setup:
1. Enable Vision API: https://console.cloud.google.com/apis/library/vision.googleapis.com
2. Set GOOGLE_APPLICATION_CREDENTIALS to your JSON key file
3. Or run: gcloud auth application-default login
"""

import argparse
import json
import sys
from pathlib import Path
from glob import glob

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.google_vision_search import (
    VisionSearch,
    format_search_results
)


def main():
    parser = argparse.ArgumentParser(
        description='Reverse image search using Google Vision API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search single image
  python scripts/reverse_image_search.py data/artworks/painting.jpg

  # Find higher resolution versions
  python scripts/reverse_image_search.py image.jpg --find-hires

  # Identify source/provenance
  python scripts/reverse_image_search.py image.jpg --identify-source

  # Search multiple images
  python scripts/reverse_image_search.py --batch "data/artworks/*.jpg"

  # Export to JSON
  python scripts/reverse_image_search.py image.jpg --json results.json

  # Search from URL
  python scripts/reverse_image_search.py --url "https://example.com/image.jpg"
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        'image',
        nargs='?',
        help='Path to image file'
    )
    input_group.add_argument(
        '--url',
        help='URL to image'
    )
    input_group.add_argument(
        '--batch',
        help='Process multiple images (glob pattern)'
    )
    
    # Search options
    parser.add_argument(
        '--max-results',
        type=int,
        default=50,
        help='Maximum results per category (default: 50)'
    )
    
    # Analysis modes
    parser.add_argument(
        '--find-hires',
        action='store_true',
        help='Find higher resolution versions'
    )
    parser.add_argument(
        '--identify-source',
        action='store_true',
        help='Identify image source/provenance'
    )
    
    # Output options
    parser.add_argument(
        '--json', '-j',
        help='Export results to JSON file'
    )
    parser.add_argument(
        '--output-dir', '-o',
        help='Output directory for batch results'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize Vision Search
        if args.verbose:
            print("Initializing Google Vision API...")
        
        searcher = VisionSearch()
        
        if args.verbose:
            print("✓ Vision API ready\n")
        
        # Batch processing
        if args.batch:
            image_paths = glob(args.batch)
            if not image_paths:
                print(f"No images found matching: {args.batch}", file=sys.stderr)
                sys.exit(1)
            
            print(f"Found {len(image_paths)} images")
            
            results = searcher.batch_search(
                image_paths=image_paths,
                output_dir=args.output_dir
            )
            
            print(f"\n✓ Processed {len(results)} images")
            print(f"API requests made: {searcher.get_request_count()}")
            
            return
        
        # Single image processing
        if args.find_hires:
            # Find higher resolution versions
            print("Searching for higher resolution versions...")
            
            matches = searcher.find_higher_resolution(
                image_path=args.image,
                min_width=1000
            )
            
            print(f"\nFound {len(matches)} potential higher-res versions:\n")
            for i, match in enumerate(matches, 1):
                print(f"{i}. {match.url}")
            
        elif args.identify_source:
            # Identify source/provenance
            print("Identifying image source...")
            
            source_info = searcher.identify_source(args.image)
            
            print(f"\n--- Source Analysis ---")
            print(f"Best Guess: {source_info['best_guess'] or 'Unknown'}")
            print(f"Total Matches: {source_info['total_matches']}")
            print(f"Total Pages: {source_info['total_pages']}")
            
            if source_info['museum_sources']:
                print(f"\nMuseum Sources ({len(source_info['museum_sources'])}):")
                for domain in source_info['museum_sources'][:5]:
                    print(f"  • {domain}")
            
            if source_info['auction_sources']:
                print(f"\nAuction Sources ({len(source_info['auction_sources'])}):")
                for domain in source_info['auction_sources'][:5]:
                    print(f"  • {domain}")
            
            if source_info['academic_sources']:
                print(f"\nAcademic Sources ({len(source_info['academic_sources'])}):")
                for domain in source_info['academic_sources'][:5]:
                    print(f"  • {domain}")
            
            if source_info['web_entities']:
                print(f"\nRelated Concepts:")
                for entity in source_info['web_entities']:
                    desc = entity.get('description', 'N/A')
                    score = entity.get('score', 0)
                    print(f"  • {desc} ({score:.2f})")
        
        else:
            # Standard reverse image search
            if args.image:
                result = searcher.reverse_image_search(
                    image_path=args.image,
                    max_results=args.max_results
                )
            else:  # --url
                result = searcher.reverse_image_search(
                    image_url=args.url,
                    max_results=args.max_results
                )
            
            # Display results
            print(format_search_results(result))
            
            # Export to JSON
            if args.json:
                with open(args.json, 'w', encoding='utf-8') as f:
                    json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
                
                print(f"\n✓ Results exported to {args.json}")
        
        # Show API usage
        if args.verbose:
            print(f"\nAPI requests made: {searcher.get_request_count()}")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        
        if "credentials" in str(e).lower() or "authentication" in str(e).lower():
            print("\nAuthentication failed. Try:", file=sys.stderr)
            print("  1. Set GOOGLE_APPLICATION_CREDENTIALS to your JSON key", file=sys.stderr)
            print("     $env:GOOGLE_APPLICATION_CREDENTIALS = 'path/to/key.json'", file=sys.stderr)
            print("  2. Or run: gcloud auth application-default login", file=sys.stderr)
        
        sys.exit(1)


if __name__ == '__main__':
    main()
