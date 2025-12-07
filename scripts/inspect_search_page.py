import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

session = requests.Session()
session.verify = False
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

# Get cookies and submit search
session.get('http://lootedart.gov.pl/en/product-war-losses/advanced-search')
response = session.post('http://lootedart.gov.pl/en/product-war-losses/advanced-search', data={
    'tytul': '', 'autor': '', 'nr_karty': '', 'sygnatura': '',
    'wysokosc': '', 'szerokosc': '', 'glebokosc': '', 'dlugosc': '', 'srednica': '', 'waga': ''
}, timeout=10)

soup = BeautifulSoup(response.content, 'html.parser')

# Save HTML for inspection
with open('search_results.html', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())

print("Saved search results to search_results.html")

# Look for pagination elements
print("\nSearching for pagination elements...")
for tag in ['ul', 'div', 'nav']:
    for elem in soup.find_all(tag, class_=lambda x: x and any(p in str(x).lower() for p in ['pag', 'navigation', 'page'])):
        print(f"\n{tag}.{elem.get('class')}:")
        print(f"  {str(elem)[:200]}")

# Look for "next" links
print("\nLooking for 'next' or 'forward' links...")
for link in soup.find_all('a'):
    text = link.get_text(strip=True).lower()
    if any(word in text for word in ['next', 'forward', '>', 'następna', 'dalej']):
        print(f"  Text: '{link.get_text(strip=True)}' -> {link.get('href')}")
