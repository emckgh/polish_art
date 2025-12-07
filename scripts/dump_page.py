import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()

s = requests.Session()
s.verify = False
s.headers['User-Agent'] = 'Mozilla/5.0'
s.get('http://lootedart.gov.pl/en/product-war-losses/advanced-search')
r = s.get('http://lootedart.gov.pl/en/product-war-losses?ID=15')

with open('page_dump.html', 'w', encoding='utf-8') as f:
    f.write(r.text)

print(f"Saved page to page_dump.html ({len(r.text)} bytes)")

soup = BeautifulSoup(r.content, 'html.parser')
print("\n=== ALL TEXT (first 2000 chars) ===")
print(soup.get_text()[:2000])
