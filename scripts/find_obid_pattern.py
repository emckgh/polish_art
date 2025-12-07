"""
Since pagination doesn't work and there are 7341 artworks,
let's try to scrape by iterating through possible obid values.
We'll test a range to find valid obids.
"""
import requests
import urllib3
from bs4 import BeautifulSoup
import time
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_obid_range(start, end, sample_size=100):
    """Test a range of obids to find valid ones."""
    session = requests.Session()
    session.verify = False
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    
    # Get cookies
    session.get('http://lootedart.gov.pl/en/product-war-losses/advanced-search')
    
    valid_obids = []
    tested = 0
    
    print(f"Testing obids from {start} to {end} (sampling every {(end-start)//sample_size})...")
    
    step = max(1, (end - start) // sample_size)
    for obid in range(start, end, step):
        if tested >= sample_size:
            break
            
        url = f'http://lootedart.gov.pl/en/product-war-losses/object?obid={obid}'
        try:
            r = session.get(url, timeout=5)
            if r.status_code == 200:
                soup = BeautifulSoup(r.content, 'html.parser')
                # Check if it's a valid artwork page (has title or card number)
                title = soup.find('h1') or soup.find('h2')
                if title and title.get_text(strip=True):
                    valid_obids.append(obid)
                    print(f"  ✓ {obid}: {title.get_text(strip=True)[:50]}")
                else:
                    print(f"  - {obid}: empty", end='\r')
            tested += 1
            time.sleep(0.1)
        except:
            pass
    
    print(f"\n\nFound {len(valid_obids)} valid obids out of {tested} tested")
    print(f"Valid obids: {valid_obids[:20]}")
    
    if len(valid_obids) > 1:
        gaps = [valid_obids[i+1] - valid_obids[i] for i in range(len(valid_obids)-1)]
        print(f"Average gap between obids: {sum(gaps)/len(gaps):.1f}")
        print(f"Min gap: {min(gaps)}, Max gap: {max(gaps)}")
    
    return valid_obids

# Test different ranges
print("Testing low range (1-10000)...")
low_range = test_obid_range(1, 10000, sample_size=50)

print("\n" + "="*80)
print("Testing mid range (30000-40000)...")
mid_range = test_obid_range(30000, 40000, sample_size=50)

print("\n" + "="*80)
print("Testing high range (60000-70000)...")
high_range = test_obid_range(60000, 70000, sample_size=50)

print("\n" + "="*80)
print(f"\nTotal valid obids found: {len(low_range) + len(mid_range) + len(high_range)}")
