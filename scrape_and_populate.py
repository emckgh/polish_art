"""Script to scrape artworks from lootedart.gov.pl and populate database."""
from src.repositories.sqlite_repository import SQLiteArtworkRepository
from src.scrapers.polish_ministry_scraper import PolishMinistryWebScraper
from src.services.data_transformer import ArtworkDataTransformer
from src.services.import_service import ArtworkImportService
from src.services.image_download_service import ImageDownloadService
from config.scraper_config import PolishMinistryScraperConfig

config = PolishMinistryScraperConfig()


def main():
    """Scrape and import artworks from lootedart.gov.pl."""
    print("Initializing scraper for lootedart.gov.pl...")
    
    scraper = PolishMinistryWebScraper()
    transformer = ArtworkDataTransformer()
    repository = SQLiteArtworkRepository("sqlite:///artworks.db")
    image_service = ImageDownloadService()
    import_service = ArtworkImportService(repository=repository)
    
    categories = config.ALL_CATEGORIES
    print(f"\nScraping {len(categories)} categories...")
    print("This may take several minutes due to rate limiting (2 seconds between requests).\n")
    
    total_imported = 0
    total_failed = 0
    
    # Scrape more categories for better sample data
    for i, category_id in enumerate(categories[:8], 1):
        print(f"[{i}/8] Scraping category {category_id}...")
        
        try:
            raw_artworks = scraper.scrape_category(category_id)
            print(f"  Found {len(raw_artworks)} raw artworks")
            
            if raw_artworks:
                artworks = transformer.transform_batch(raw_artworks)
                print(f"  Transformed {len(artworks)} artworks")
                
                # Download images for artworks that have image URLs
                artworks_with_images = []
                for artwork in artworks:
                    if artwork.image_url:
                        try:
                            artwork_with_image = image_service.download_and_attach_image(artwork)
                            artworks_with_images.append(artwork_with_image)
                            print(f"    Downloaded image for: {artwork.title[:50]}...")
                        except Exception as e:
                            print(f"    Failed to download image for {artwork.title[:50]}: {e}")
                            artworks_with_images.append(artwork)
                    else:
                        artworks_with_images.append(artwork)
                
                stats = import_service.import_batch(artworks_with_images)
                total_imported += stats['imported']
                total_failed += stats['failed']
                print(f"  Imported: {stats['imported']}, Failed: {stats['failed']}")
            else:
                print(f"  No artworks found in category {category_id}")
                
        except Exception as e:
            print(f"  Error scraping category {category_id}: {e}")
            continue
    
    print(f"\n{'='*60}")
    print(f"Import Summary:")
    print(f"  Total Imported: {total_imported}")
    print(f"  Total Failed: {total_failed}")
    print(f"  Database now contains: {len(repository.find_all(limit=1000, offset=0))} artworks")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
