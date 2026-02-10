"""Print record counts and disk size for data/artworks.db."""
import os
import sqlite3

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(PROJECT_ROOT, "data", "artworks.db")

if not os.path.exists(db_path):
    print("Database not found at", db_path)
    data_dir = os.path.join(PROJECT_ROOT, "data")
    if os.path.isdir(data_dir):
        print("Contents of data/:", os.listdir(data_dir))
    else:
        print("data/ directory does not exist")
    exit(1)

size = os.path.getsize(db_path)
conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
)
tables = [r[0] for r in cur.fetchall()]
counts = {}
for t in tables:
    cur.execute("SELECT COUNT(*) FROM " + '"' + t + '"')
    counts[t] = cur.fetchone()[0]
conn.close()

print("Database file:", db_path)
print("Disk size: {:,} bytes ({:.2f} MB)".format(size, size / (1024 * 1024)))
print()
print("Record counts by table:")
total = 0
for t, c in sorted(counts.items(), key=lambda x: -x[1]):
    print("  {}: {:,}".format(t, c))
    total += c
print("  ---")
print("  TOTAL rows: {:,}".format(total))

# Storage breakdown: image BLOBs vs rest
conn2 = sqlite3.connect(db_path)
cur = conn2.cursor()
cur.execute("SELECT COUNT(*) FROM artworks WHERE image_data IS NOT NULL")
n_with_image = cur.fetchone()[0]
cur.execute("SELECT SUM(LENGTH(image_data)) FROM artworks")
total_image_bytes = cur.fetchone()[0] or 0
conn2.close()
n_art = counts.get("artworks", 0)
vision_requests = max(1, counts.get("vision_api_requests", 0))
vision_rows = (
    counts.get("vision_api_requests", 0)
    + counts.get("vision_api_matches", 0)
    + counts.get("vision_api_entities", 0)
)
artwork_meta_bytes = n_art * 2048  # ~2 KB metadata per row
vision_bytes = max(0, size - total_image_bytes - artwork_meta_bytes)
print()
print("Storage breakdown (approx):")
if n_with_image:
    print("  Artworks image BLOB: {:.1f} MB total, {:.1f} KB/artwork avg".format(
        total_image_bytes / (1024 * 1024), (total_image_bytes / n_with_image) / 1024
    ))
print("  Vision tables: ~{:.1f} MB for {:,} requests (~{:.1f} KB/request)".format(
    vision_bytes / (1024 * 1024), vision_requests, (vision_bytes / 1024) / vision_requests
))
