import json

d = json.load(open('data/test_complete_fields.json', encoding='utf-8'))
coin = [a for a in d['artworks'] if 'Ducat' in a.get('title', '')][0]

print(f"Title: {coin['title']}")
print(f"Diameter: {coin.get('diameter', 'NOT FOUND')}")
print(f"Weight: {coin.get('weight', 'NOT FOUND')}")
print(f"Material: {coin.get('material', 'NOT FOUND')}")
print(f"Date: {coin.get('date_of_creation', 'NOT FOUND')}")
print(f"Artist: {coin.get('artist', 'NOT FOUND')}")
print(f"Owner: {coin.get('owner', 'NOT FOUND')}")
