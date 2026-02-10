"""
Use Playwright to capture network requests on the search page.
This will help us find the AJAX/API endpoint used for loading more results.
"""
from playwright.sync_api import sync_playwright
import json
import time

def capture_network_requests():
    """Capture network requests while scrolling the search page."""
    
    requests_log = []
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        # Listen to all network requests
        def log_request(request):
            requests_log.append({
                'url': request.url,
                'method': request.method,
                'resource_type': request.resource_type,
                'post_data': request.post_data if request.method == 'POST' else None
            })
        
        page.on('request', log_request)
        
        # Navigate to search results page (from earlier testing we know this URL shows results)
        print("Loading search page and submitting form...")
        page.goto('http://lootedart.gov.pl/en/product-war-losses/advanced-search')
        time.sleep(1)
        
        # Submit form by evaluating JavaScript
        print("Submitting search form via JavaScript...")
        page.evaluate('''() => {
            const form = document.querySelector('form.module_content');
            if (form) {
                const formData = new FormData(form);
                fetch(form.action || window.location.href, {
                    method: 'POST',
                    body: formData
                }).then(() => {
                    form.submit();
                });
            }
        }''')
        
        time.sleep(3)
        print(f"Page title: {page.title()}")
        print(f"Current URL: {page.url}")
        
        # Count initial artwork links
        artwork_links = page.locator('a[href*="/object?obid="]')
        initial_count = artwork_links.count()
        print(f"Initial artwork links: {initial_count}")
        
        # Scroll down multiple times to trigger lazy loading
        print("\nScrolling to load more results...")
        for i in range(20):
            prev_height = page.evaluate('document.body.scrollHeight')
            page.evaluate('window.scrollTo(0, document.body.scrollHeight)')
            time.sleep(2)
            new_height = page.evaluate('document.body.scrollHeight')
            
            artwork_links = page.locator('a[href*="/object?obid="]')
            count = artwork_links.count()
            print(f"  Scroll {i+1}/20: {count} links (height: {prev_height} -> {new_height})")
            
            # Stop if no more content loaded
            if new_height == prev_height and count == initial_count:
                print("  No new content loaded, stopping")
                break
            
            initial_count = count
        
        final_count = artwork_links.count()
        print(f"\nFinal count: {final_count} artwork links")
        
        browser.close()
    
    # Filter interesting requests
    print("\n" + "="*80)
    print("NETWORK REQUESTS")
    print("="*80)
    
    interesting_requests = []
    for req in requests_log:
        url = req['url']
        # Filter for likely API/AJAX calls
        if any(term in url.lower() for term in ['search', 'ajax', 'api', 'json', 'product', 'war-losses', 'limitstart']):
            if 'static' not in url and 'css' not in url and 'js' not in url and 'image' not in url:
                interesting_requests.append(req)
    
    for req in interesting_requests:
        print(f"\n{req['method']} {req['url']}")
        if req['post_data']:
            print(f"  POST data: {req['post_data'][:200]}")
    
    # Save all requests to file
    with open('network_requests.json', 'w', encoding='utf-8') as f:
        json.dump(requests_log, f, indent=2)
    print(f"\n✓ Saved all {len(requests_log)} requests to network_requests.json")
    print(f"✓ Found {len(interesting_requests)} interesting requests")

if __name__ == '__main__':
    capture_network_requests()
