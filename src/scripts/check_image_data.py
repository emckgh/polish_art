import sqlite3

conn = sqlite3.connect('artworks.db')
cursor = conn.cursor()
cursor.execute('SELECT id, title, image_data IS NOT NULL as has_data, LENGTH(image_data) as size FROM artworks LIMIT 10')
print("Image data status:")
for row in cursor.fetchall():
    print(f'  {row[1][:30]:30} | Has data: {bool(row[2])} | Size: {row[3] if row[3] else 0} bytes')
conn.close()
