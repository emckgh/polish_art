import requests
import urllib3
from bs4 import BeautifulSoup

urllib3.disable_warnings()

# Check advanced search page
url = 'http://lootedart.gov.pl/en/product-war-losses/advanced-search'
print(f"=== EXAMINING {url} ===\n")
r = requests.get(url, verify=False)
print(f"Status: {r.status_code}")
print(f"Content length: {len(r.text)}")

soup = BeautifulSoup(r.content, 'html.parser')

# Print title
title = soup.find('title')
print(f"Title: {title.get_text() if title else 'None'}")

# Print first 3000 characters to see structure
print("\n--- First 3000 chars of HTML ---")
print(r.text[:3000])

# Look for forms
print("\n--- FORMS on page ---")
forms = soup.find_all('form')
print(f"Found {len(forms)} forms")
for i, form in enumerate(forms, 1):
    print(f"\nForm {i}:")
    print(f"  Action: {form.get('action', 'None')}")
    print(f"  Method: {form.get('method', 'None')}")
    inputs = form.find_all('input')
    print(f"  Inputs: {len(inputs)}")
    for inp in inputs[:5]:
        print(f"    - {inp.get('name', 'unnamed')}: {inp.get('type', 'text')}")

# Check all links
print("\n--- ALL LINKS ---")
all_links = [a.get('href') for a in soup.find_all('a', href=True)]
unique_links = set(all_links)
print(f"Total links: {len(all_links)}, Unique: {len(unique_links)}")
for link in sorted(unique_links):
    print(f"  {link}")
