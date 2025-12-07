import sqlite3

conn = sqlite3.connect('artworks.db')
cursor = conn.cursor()
cursor.execute('SELECT id, title, image_url, image_hash FROM artworks LIMIT 3')
for row in cursor.fetchall():
    print(f'ID: {row[0][:8]}...')
    print(f'  Title: {row[1]}')
    print(f'  image_url: {row[2][:60] if row[2] else None}...')
    print(f'  image_hash: {row[3]}')
    print()
conn.close()
