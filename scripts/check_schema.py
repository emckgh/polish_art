"""Quick script to check the image_features table schema."""
import sqlite3

conn = sqlite3.connect("artworks.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(image_features)")
columns = cursor.fetchall()

print("Image Features Table Schema:")
print("-" * 80)
print(f"{'#':<3} {'Name':<25} {'Type':<15} {'NotNull':<8} {'Default':<10}")
print("-" * 80)

for col in columns:
    col_id, name, col_type, not_null, default_val, pk = col
    print(f"{col_id:<3} {name:<25} {col_type:<15} {not_null:<8} {str(default_val):<10}")

conn.close()
