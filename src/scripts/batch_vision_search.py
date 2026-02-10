"""
Batch reverse image search script for artworks with Vision API tracking.

This script searches for artwork images on the web using Google Vision API,
automatically tracking all API usage and flagging interesting results.

Usage:
    # Search all artworks
    python scripts/batch_vision_search.py --all

    # Search specific artwork
    python scripts/batch_vision_search.py --artwork-id UUID

    # Search artworks without prior searches
    python scripts/batch_vision_search.py --unsearched

    # Limit number of artworks
    python scripts/batch_vision_search.py --all --limit 100

    # Show cost summary
    python scripts/batch_vision_search.py --cost-summary
"""
import argparse
import sys
from pathlib import Path
from uuid import UUID
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.repositories.sqlite_repository import SQLiteArtworkRepository
from src.repositories.vision_repository import VisionAPIRepository
from src.services.vision_tracking_service import VisionAPITrackingService
from src.utils.google_vision_search import VisionSearch


def main():
    parser = argparse.ArgumentParser(
        description='Batch reverse image search with Vision API tracking',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Search all artworks (be careful - costs money!)
  python scripts/batch_vision_search.py --all --limit 10

  # Search specific artwork by ID
  python scripts/batch_vision_search.py --artwork-id "123e4567-e89b-12d3-a456-426614174000"

  # Search only artworks that haven't been searched yet
  python scripts/batch_vision_search.py --unsearched --limit 50

  # View cost summary
  python scripts/batch_vision_search.py --cost-summary

  # View interesting findings
  python scripts/batch_vision_search.py --show-findings --limit 20
        """
    )
    
    # Search modes
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        '--all',
        action='store_true',
        help='Search all artworks (WARNING: costs API credits)'
    )
    mode_group.add_argument(
        '--artwork-id',
        help='Search specific artwork by UUID'
    )
    mode_group.add_argument(
        '--unsearched',
        action='store_true',
        help='Search only artworks without prior Vision API searches'
    )
    mode_group.add_argument(
        '--cost-summary',
        action='store_true',
        help='Show API cost summary and exit'
    )
    mode_group.add_argument(
        '--show-findings',
        action='store_true',
        help='Show interesting findings and exit'
    )
    
    # Options
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Maximum number of artworks to search'
    )
    parser.add_argument(
        '--database',
        default='sqlite:///data/artworks.db',
        help='Database connection string'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between requests in seconds (default: 1.0)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt'
    )
    
    args = parser.parse_args()
    
    # Initialize repositories
    artwork_repo = SQLiteArtworkRepository(args.database)
    vision_repo = VisionAPIRepository(args.database)
    tracking_service = VisionAPITrackingService(vision_repo)
    
    # Handle cost summary
    if args.cost_summary:
        print_cost_summary(tracking_service)
        return
    
    # Handle show findings
    if args.show_findings:
        print_findings(tracking_service, args.limit or 20)
        return
    
    # Initialize Vision Search
    try:
        searcher = VisionSearch(
            enable_tracking=True,
            database_url=args.database
        )
        if args.verbose:
            print("✓ Vision API initialized")
    except Exception as e:
        print(f"✗ Failed to initialize Vision API: {e}")
        print("\nMake sure you've set up authentication:")
        print("  1. Set GOOGLE_APPLICATION_CREDENTIALS environment variable, or")
        print("  2. Run: gcloud auth application-default login")
        sys.exit(1)
    
    # Get artworks to search
    if args.artwork_id:
        artwork = artwork_repo.find_by_id(args.artwork_id)
        if not artwork:
            print(f"✗ Artwork not found: {args.artwork_id}")
            sys.exit(1)
        artworks = [artwork]
    elif args.unsearched:
        # Get all artworks and filter out those already searched
        all_artworks = artwork_repo.find_all(limit=10000, offset=0)
        artworks = []
        for artwork in all_artworks:
            searches = tracking_service.get_artwork_search_history(artwork.id, limit=1)
            if not searches:
                artworks.append(artwork)
                if args.limit and len(artworks) >= args.limit:
                    break
    else:  # --all
        limit = args.limit or 10000
        artworks = artwork_repo.find_all(limit=limit, offset=0)
    
    if not artworks:
        print("No artworks to search")
        return
    
    print(f"\n{'='*80}")
    print(f"BATCH VISION API SEARCH")
    print(f"{'='*80}")
    print(f"Artworks to search: {len(artworks)}")
    print(f"Estimated cost: {len(artworks)} API units")
    print(f"Delay between requests: {args.delay}s")
    print(f"{'='*80}\n")
    
    # Confirm if searching many artworks
    if len(artworks) > 10 and not args.yes:
        response = input(f"This will use {len(artworks)} API credits. Continue? (y/N): ")
        if response.lower() != 'y':
            print("Cancelled")
            return
    
    # Search each artwork
    successful = 0
    failed = 0
    interesting = 0
    
    for i, artwork in enumerate(artworks, 1):
        print(f"\n[{i}/{len(artworks)}] Searching: {artwork.title[:50]}")
        print(f"  ID: {artwork.id}")
        
        try:
            # Check if artwork has already been searched
            existing_searches = tracking_service.get_artwork_search_history(artwork.id, limit=1)
            if existing_searches:
                print(f"  ⚠ Already searched ({existing_searches[0].request_timestamp}) - skipping")
                print(f"     Use --unsearched to only search new artworks")
                continue
            
            # Check if artwork has image data
            if not artwork.image_data:
                print("  ⚠ No image data - skipping")
                failed += 1
                continue
            
            # Perform search
            result = searcher.reverse_image_search(
                artwork_id=artwork.id,
                image_bytes=artwork.image_data
            )
            
            # Get tracking info
            searches = tracking_service.get_artwork_search_history(artwork.id, limit=1)
            if searches and searches[0].has_interesting_results:
                interesting += 1
                print(f"  🔥 INTERESTING RESULTS FOUND!")
                print(f"     Full matches: {searches[0].total_full_matches}")
                print(f"     Partial matches: {searches[0].total_partial_matches}")
                print(f"     Pages: {searches[0].total_pages_with_image}")
            else:
                print(f"  ✓ Search completed (no interesting results)")
            
            successful += 1
            
            # Delay between requests
            if i < len(artworks):
                time.sleep(args.delay)
        
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user")
            break
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed += 1
            continue
    
    # Final summary
    print(f"\n{'='*80}")
    print(f"SEARCH COMPLETE")
    print(f"{'='*80}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Interesting results: {interesting}")
    print(f"Total API cost: {successful} units")
    print(f"{'='*80}\n")
    
    # Show cost summary
    print_cost_summary(tracking_service)
    
    # Show any interesting findings
    if interesting > 0:
        print(f"\n💡 Found {interesting} artworks with interesting results!")
        print("   View them with: python scripts/batch_vision_search.py --show-findings\n")


def print_cost_summary(tracking_service: VisionAPITrackingService):
    """Print API cost summary."""
    total_cost = tracking_service.get_total_api_cost()
    
    print(f"\n{'='*80}")
    print(f"API COST SUMMARY")
    print(f"{'='*80}")
    print(f"Total API units used: {total_cost}")
    print(f"Estimated cost: ${total_cost * 0.0015:.2f} USD")
    print(f"  (Based on $1.50 per 1,000 requests after free tier)")
    print(f"{'='*80}\n")


def print_findings(tracking_service: VisionAPITrackingService, limit: int):
    """Print interesting findings."""
    findings = tracking_service.get_interesting_findings(limit=limit)
    
    print(f"\n{'='*80}")
    print(f"INTERESTING FINDINGS ({len(findings)} results)")
    print(f"{'='*80}\n")
    
    if not findings:
        print("No interesting findings yet.")
        print("Run searches with: python scripts/batch_vision_search.py --all")
        return
    
    for i, finding in enumerate(findings, 1):
        print(f"{i}. Artwork ID: {finding.artwork_id}")
        print(f"   Searched: {finding.request_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   Full matches: {finding.total_full_matches}")
        print(f"   Partial matches: {finding.total_partial_matches}")
        print(f"   Pages with image: {finding.total_pages_with_image}")
        
        # Show top matches by category
        if finding.matches:
            auction_matches = [m for m in finding.matches if m.domain_category == 'auction']
            marketplace_matches = [m for m in finding.matches if m.domain_category == 'marketplace']
            
            if auction_matches:
                print(f"   🔥 AUCTION SITES: {len(auction_matches)}")
                for match in auction_matches[:3]:
                    print(f"      - {match.domain}: {match.page_url or match.image_url}")
            
            if marketplace_matches:
                print(f"   🛒 MARKETPLACES: {len(marketplace_matches)}")
                for match in marketplace_matches[:3]:
                    print(f"      - {match.domain}: {match.page_url or match.image_url}")
        
        print()
    
    print(f"{'='*80}\n")
    
    # Show suspicious domains
    suspicious = tracking_service.get_suspicious_domains()
    if suspicious:
        print(f"SUSPICIOUS DOMAINS ({len(suspicious)} flagged)")
        print(f"{'='*80}\n")
        for domain in suspicious[:10]:
            print(f"  {domain.domain}")
            print(f"    Category: {domain.category}")
            print(f"    Appearances: {domain.total_appearances}")
            print(f"    Artworks found: {len(domain.artworks_found)}")
            print()


if __name__ == "__main__":
    main()
