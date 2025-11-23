"""End-to-end tests for artwork detail page UI using Playwright."""
import re
import pytest
from playwright.sync_api import Page, expect, BrowserContext


@pytest.fixture(scope="session")
def base_url():
    """Base URL for the application."""
    return "http://localhost:8001"


@pytest.fixture(scope="session")
def sample_artwork_id(base_url):
    """Get a sample artwork ID for testing."""
    import requests
    response = requests.get(f"{base_url}/api/artworks?page=1&limit=1")
    if response.status_code == 200:
        data = response.json()
        if data.get("items"):
            return data["items"][0]["id"]
    return "28e08eea-e820-4c75-904d-d57c36c5482d"  # Fallback ID


@pytest.fixture
def context(browser):
    """Create a new context for each test to ensure isolation."""
    context = browser.new_context()
    yield context
    context.close()


@pytest.fixture
def page(context):
    """Create a new page for each test with clean state."""
    page = context.new_page()
    # Set reasonable timeouts
    page.set_default_timeout(10000)
    page.set_default_navigation_timeout(10000)
    yield page
    # Close page
    try:
        page.close()
    except Exception:
        pass  # Ignore close errors


def test_detail_page_navigation(page: Page, base_url: str):
    """Test navigating from main page to detail page by clicking a row."""
    # Navigate to main page
    page.goto(base_url, wait_until="domcontentloaded")
    
    # Wait for artworks to load
    page.wait_for_selector("#artworkTableBody tr", timeout=5000)
    
    # Verify table has rows (at least 1, could be up to 10 based on page size)
    rows = page.locator("#artworkTableBody tr")
    assert rows.count() > 0, "Table should have at least one row"
    
    # Get the first artwork's title for later verification
    first_row = rows.nth(0)
    artwork_title = first_row.locator(".artwork-title-cell").text_content()
    
    # Click the first row
    first_row.click()
    
    # Wait for detail page to load
    page.wait_for_url(re.compile(r"/static/detail\.html\?id="), timeout=3000)
    
    # Verify we're on the detail page
    expect(page).to_have_url(re.compile(r"/static/detail\.html\?id=[a-f0-9-]+"))
    
    # Verify the artwork title matches
    page_title = page.locator("#artworkTitle")
    expect(page_title).to_contain_text(artwork_title)


def test_general_information_tab(page: Page, base_url: str):
    """Test that general information tab displays correct data."""
    # Navigate directly to detail page (get first artwork ID from API)
    page.goto(base_url, wait_until="domcontentloaded")
    page.wait_for_selector("#artworkTableBody tr", timeout=5000)
    
    # Click first row
    page.locator("#artworkTableBody tr").nth(0).click()
    page.wait_for_url(re.compile(r"/static/detail\.html\?id="), timeout=3000)
    
    # Verify General Information tab is active by default
    general_tab = page.locator('[data-tab="general"]')
    expect(general_tab).to_have_class(re.compile(r"active"))
    
    # Verify general tab content is visible
    general_content = page.locator("#general-tab")
    expect(general_content).to_be_visible(timeout=2000)
    expect(general_content).to_have_class(re.compile(r"active"))
    
    # Verify sections exist
    expect(page.locator("#basicInfo")).to_be_visible(timeout=2000)
    expect(page.locator("#artistInfo")).to_be_visible()
    expect(page.locator("#statusInfo")).to_be_visible()
    expect(page.locator("#descriptionInfo")).to_be_visible()
    expect(page.locator("#metadataInfo")).to_be_visible()
    
    # Verify basic info contains title
    basic_info = page.locator("#basicInfo")
    expect(basic_info).to_contain_text("Title")
    
    # Verify metadata contains artwork ID
    metadata_info = page.locator("#metadataInfo")
    expect(metadata_info).to_contain_text("Artwork ID")


def test_perceptual_hash_tab_navigation(page: Page, base_url: str, sample_artwork_id: str):
    """Test navigating to perceptual hash tab."""
    # Navigate directly to detail page
    page.goto(f"{base_url}/static/detail.html?id={sample_artwork_id}", wait_until="domcontentloaded")
    
    # Wait for general tab to be active
    page.wait_for_selector("#general-tab.active", timeout=3000)
    
    # Click on Perceptual Hash Analysis tab
    perceptual_tab_button = page.locator('[data-tab="perceptual"]')
    perceptual_tab_button.click()
    
    # Wait for tab to become active
    page.wait_for_timeout(200)  # Give animation time to complete
    
    # Verify tab is now active
    expect(perceptual_tab_button).to_have_class(re.compile(r"active"))
    
    # Verify perceptual content is visible
    perceptual_content = page.locator("#perceptual-tab")
    expect(perceptual_content).to_be_visible()
    expect(perceptual_content).to_have_class(re.compile(r"active"))
    
    # Verify general tab is no longer visible
    general_content = page.locator("#general-tab")
    expect(general_content).not_to_have_class(re.compile(r"active"))


def test_perceptual_hash_data_display(page: Page, base_url: str, sample_artwork_id: str):
    """Test that perceptual hash tab displays all CV feature data."""
    # Navigate directly to detail page
    page.goto(f"{base_url}/static/detail.html?id={sample_artwork_id}", wait_until="domcontentloaded")
    
    # Switch to perceptual hash tab
    page.locator('[data-tab="perceptual"]').click()
    page.wait_for_timeout(200)
    
    # Wait for features to load (might take a moment)
    page.wait_for_selector("#hashValues", timeout=3000)
    
    # Check if features are available or show "not extracted" message
    hash_values = page.locator("#hashValues")
    
    # Test both scenarios: features available or not
    if "No feature data available" in hash_values.text_content():
        # Features not extracted - verify appropriate message
        expect(hash_values).to_contain_text("No feature data available")
        expect(hash_values).to_contain_text("Computer vision features have not been extracted")
    else:
        # Features extracted - verify all sections are present
        
        # 1. Hash Values section
        expect(hash_values).to_be_visible()
        expect(hash_values).to_contain_text("pHash")
        expect(hash_values).to_contain_text("dHash")
        expect(hash_values).to_contain_text("aHash")
        
        # Verify hash descriptions
        expect(hash_values).to_contain_text("DCT-based")
        expect(hash_values).to_contain_text("Gradient-based")
        expect(hash_values).to_contain_text("Average-based")
        
        # 2. Image Properties section
        image_props = page.locator("#imageProps")
        expect(image_props).to_be_visible()
        expect(image_props).to_contain_text("Dimensions")
        
        # 3. Quality Metrics section
        quality_metrics = page.locator("#qualityMetrics")
        expect(quality_metrics).to_be_visible()
        expect(quality_metrics).to_contain_text("Sharpness Score")
        expect(quality_metrics).to_contain_text("Contrast Score")
        expect(quality_metrics).to_contain_text("Brightness Average")
        
        # Verify quality bars exist
        quality_bars = page.locator(".quality-bar")
        expect(quality_bars).to_have_count(3)
        
        # 4. Dominant Colors section
        dominant_colors = page.locator("#dominantColors")
        expect(dominant_colors).to_be_visible()
        
        # Check for color swatches (should be 5)
        color_swatches = page.locator(".color-swatch")
        if color_swatches.count() > 0:
            expect(color_swatches).to_have_count(5)
            
            # Verify color boxes have background colors
            color_boxes = page.locator(".color-box")
            expect(color_boxes).to_have_count(5)
        
        # 5. CLIP Embedding section
        clip_embedding = page.locator("#clipEmbedding")
        expect(clip_embedding).to_be_visible()
        
        # Verify embedding stats are present
        embedding_stats = page.locator(".embedding-stats")
        if embedding_stats.count() > 0:
            expect(embedding_stats).to_contain_text("Dimensions")
            expect(embedding_stats).to_contain_text("512")  # CLIP embedding size
            expect(embedding_stats).to_contain_text("Mean")
            expect(embedding_stats).to_contain_text("Std Dev")
            expect(embedding_stats).to_contain_text("Min")
            expect(embedding_stats).to_contain_text("Max")


def test_hash_values_format(page: Page, base_url: str, sample_artwork_id: str):
    """Test that hash values are displayed in correct format (hexadecimal)."""
    # Navigate directly to detail page
    page.goto(f"{base_url}/static/detail.html?id={sample_artwork_id}", wait_until="domcontentloaded")
    
    # Switch to perceptual hash tab
    page.locator('[data-tab="perceptual"]').click()
    page.wait_for_timeout(200)
    page.wait_for_selector("#hashValues", timeout=3000)
    
    hash_values_text = page.locator("#hashValues").text_content()
    
    # Only test format if features are available
    if "No feature data available" not in hash_values_text:
        # Check for hash value patterns (16 hex characters)
        hash_value_elements = page.locator(".hash-value")
        expect(hash_value_elements).to_have_count(3)
        
        # Verify each hash is hexadecimal format
        for i in range(3):
            hash_text = hash_value_elements.nth(i).text_content()
            # Should be 16 hexadecimal characters (64-bit hash)
            assert re.match(r'^[a-f0-9]{16}$', hash_text.strip()), \
                f"Hash value should be 16 hex chars, got: {hash_text}"


def test_back_to_main_page(page: Page, base_url: str, sample_artwork_id: str):
    """Test navigating back to main page from detail page."""
    # Navigate directly to detail page
    page.goto(f"{base_url}/static/detail.html?id={sample_artwork_id}", wait_until="domcontentloaded")
    
    # Verify back link exists
    back_link = page.locator(".back-link")
    expect(back_link).to_be_visible(timeout=2000)
    expect(back_link).to_contain_text("Back to Database")
    
    # Click back link
    back_link.click()
    
    # Verify we're back on main page
    page.wait_for_url(f"{base_url}/static/index.html", timeout=3000)
    expect(page).to_have_url(f"{base_url}/static/index.html")
    
    # Verify table is visible
    expect(page.locator("#artworkTable")).to_be_visible()


def test_image_display_in_detail_page(page: Page, base_url: str, sample_artwork_id: str):
    """Test that artwork image is displayed in detail page."""
    # Navigate directly to detail page
    page.goto(f"{base_url}/static/detail.html?id={sample_artwork_id}", wait_until="domcontentloaded")
    
    # Wait for image container
    image_container = page.locator("#imageContainer")
    expect(image_container).to_be_visible(timeout=2000)
    
    # Check if image loaded or placeholder shown
    page.wait_for_timeout(500)  # Give image time to load
    
    # Either image or "no image" placeholder should be visible
    img = image_container.locator("img")
    placeholder = image_container.locator(".no-image-large")
    
    # One of them should exist
    assert img.count() > 0 or placeholder.count() > 0, \
        "Either image or placeholder should be present"


def test_responsive_tab_switching(page: Page, base_url: str, sample_artwork_id: str):
    """Test switching between tabs multiple times."""
    # Navigate directly to detail page
    page.goto(f"{base_url}/static/detail.html?id={sample_artwork_id}", wait_until="domcontentloaded")
    
    general_tab = page.locator('[data-tab="general"]')
    perceptual_tab = page.locator('[data-tab="perceptual"]')
    
    # Initially on general tab
    expect(general_tab).to_have_class(re.compile(r"active"))
    
    # Switch to perceptual
    perceptual_tab.click()
    page.wait_for_timeout(150)
    expect(perceptual_tab).to_have_class(re.compile(r"active"))
    expect(general_tab).not_to_have_class(re.compile(r"active"))
    
    # Switch back to general
    general_tab.click()
    page.wait_for_timeout(150)
    expect(general_tab).to_have_class(re.compile(r"active"))
    expect(perceptual_tab).not_to_have_class(re.compile(r"active"))
    
    # Switch to perceptual again
    perceptual_tab.click()
    page.wait_for_timeout(150)
    expect(perceptual_tab).to_have_class(re.compile(r"active"))
    expect(general_tab).not_to_have_class(re.compile(r"active"))
