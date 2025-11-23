"""Script to populate database with test artworks for development."""
from src.domain.entities import Artwork, Artist, ArtworkStatus
from src.repositories.sqlite_repository import (
    SQLiteArtworkRepository
)
from src.services.import_service import ArtworkImportService


def create_test_artworks():
    """Create test artwork data for development."""
    return [
        Artwork(
            title="Portrait of a Young Man",
            artist=Artist(
                name="Raphael",
                nationality="Italian",
                birth_year=1483,
                death_year=1520
            ),
            creation_year=1513,
            description="Lost masterpiece by Raphael, looted from Czartoryski Museum in Kraków during WWII. One of the most famous missing paintings in the world.",
            status=ArtworkStatus.KNOWN_LOOTED,
            last_known_location="Kraków, Poland",
            image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/8f/Raphael_-_Portrait_of_a_Young_Man_-_Czartoryski.jpg/400px-Raphael_-_Portrait_of_a_Young_Man_-_Czartoryski.jpg"
        ),
        Artwork(
            title="Lady with an Ermine",
            artist=Artist(
                name="Leonardo da Vinci",
                nationality="Italian",
                birth_year=1452,
                death_year=1519
            ),
            creation_year=1489,
            description="Masterpiece from Czartoryski Museum, looted by Nazis but later recovered and returned to Poland.",
            status=ArtworkStatus.RECOVERED,
            last_known_location="Czartoryski Museum, Kraków",
            image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Lady_with_an_Ermine_-_Leonardo_da_Vinci_-_Google_Art_Project.jpg/400px-Lady_with_an_Ermine_-_Leonardo_da_Vinci_-_Google_Art_Project.jpg"
        ),
        Artwork(
            title="The Battle of Grunwald",
            artist=Artist(
                name="Jan Matejko",
                nationality="Polish",
                birth_year=1838,
                death_year=1893
            ),
            creation_year=1878,
            description="Monumental painting depicting the medieval Battle of Grunwald. Seized by Germans and later found in a castle in Bavaria.",
            status=ArtworkStatus.RECOVERED,
            last_known_location="National Museum, Warsaw",
            image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Battle_of_Grunwald_by_Jan_Matejko.jpg/600px-Battle_of_Grunwald_by_Jan_Matejko.jpg"
        ),
        Artwork(
            title="Jewish Woman with Oranges",
            artist=Artist(
                name="Aleksander Gierymski",
                nationality="Polish",
                birth_year=1850,
                death_year=1901
            ),
            creation_year=1880,
            description="Important Polish painting looted during WWII, still missing.",
            status=ArtworkStatus.KNOWN_LOOTED,
            last_known_location="Warsaw, Poland"
        ),
        Artwork(
            title="Portrait of a Gentleman",
            artist=Artist(
                name="Hans Memling",
                nationality="Flemish",
                birth_year=1430,
                death_year=1494
            ),
            creation_year=1470,
            description="15th century Flemish portrait from Polish collection, looted and never recovered.",
            status=ArtworkStatus.KNOWN_LOOTED,
            last_known_location="Unknown"
        ),
        Artwork(
            title="Storks",
            artist=Artist(
                name="Józef Chełmoński",
                nationality="Polish",
                birth_year=1849,
                death_year=1914
            ),
            creation_year=1900,
            description="Famous Polish landscape painting featuring storks. Stolen during WWII occupation.",
            status=ArtworkStatus.KNOWN_LOOTED,
            last_known_location="Private collection, Warsaw"
        ),
        Artwork(
            title="Madonna and Child with Saints",
            artist=Artist(
                name="Unknown Renaissance Master",
                nationality="Italian"
            ),
            creation_year=1480,
            description="Medieval religious triptych from Wawel Cathedral, disappeared during Nazi occupation.",
            status=ArtworkStatus.KNOWN_LOOTED,
            last_known_location="Wawel Cathedral, Kraków"
        ),
        Artwork(
            title="Portrait of Helena Radziwiłł",
            artist=Artist(
                name="Marcello Bacciarelli",
                nationality="Italian",
                birth_year=1731,
                death_year=1818
            ),
            creation_year=1780,
            description="Court portrait from Royal Castle in Warsaw, recovered after the war and restored.",
            status=ArtworkStatus.RECOVERED,
            last_known_location="Royal Castle, Warsaw"
        ),
        Artwork(
            title="Polish Nobleman on Horseback",
            artist=Artist(
                name="Piotr Michałowski",
                nationality="Polish",
                birth_year=1800,
                death_year=1855
            ),
            creation_year=1835,
            description="Romantic era painting depicting Polish cavalry. Looted from National Museum in Warsaw.",
            status=ArtworkStatus.SUSPECTED,
            last_known_location="National Museum, Warsaw"
        ),
        Artwork(
            title="Self-Portrait in Armor",
            artist=Artist(
                name="Rembrandt van Rijn",
                nationality="Dutch",
                birth_year=1606,
                death_year=1669
            ),
            creation_year=1655,
            description="Rembrandt self-portrait that was part of Polish royal collection. Seized by Nazi forces in 1939.",
            status=ArtworkStatus.KNOWN_LOOTED,
            last_known_location="Royal collection, Warsaw",
            image_url="https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Rembrandt_Harmensz._van_Rijn_135.jpg/400px-Rembrandt_Harmensz._van_Rijn_135.jpg"
        )
    ]


def main():
    """Populate database with test data."""
    print("Creating test artworks database...")
    
    repository = SQLiteArtworkRepository("sqlite:///artworks.db")
    import_service = ArtworkImportService(repository=repository)
    
    artworks = create_test_artworks()
    stats = import_service.import_batch(artworks)
    
    print(f"\nImport complete!")
    print(f"  Imported: {stats['imported']}")
    print(f"  Failed: {stats['failed']}")
    print(f"  Total: {stats['total']}")
    
    all_artworks = repository.find_all(limit=100, offset=0)
    print(f"\nDatabase now contains {len(all_artworks)} artworks")


if __name__ == "__main__":
    main()
