# End-to-End Testing with Playwright

This directory contains end-to-end (E2E) tests for the Polish Looted Art Database using Playwright.

## Setup

1. **Install Playwright dependencies:**
   ```powershell
   pip install -r tests/e2e/requirements.txt
   ```

2. **Install Playwright browsers:**
   ```powershell
   playwright install chromium
   ```

## Running Tests

### Prerequisites
- Ensure the FastAPI server is running on `http://localhost:8000`:
  ```powershell
  python -m src.main
  ```

### Run the walkthrough test
```powershell
python tests/e2e/test_walkthrough.py
```

The test will:
- Launch a visible browser window (headless=False)
- Run slower (slow_mo=500ms) so you can see the interactions
- Perform 14 different test scenarios covering all major functionality

## What Gets Tested

### 1. **Main Page**
- Page loads correctly
- Title displays
- Table structure (8 columns including Vision API)

### 2. **Vision API Status**
- Status icons load (🔍 for searched, 🔥 for interesting)
- Status data fetched from API

### 3. **Search Functionality**
- Search input works
- Results update
- Clear button resets search

### 4. **Filtering**
- Vision API Searched filter
- Interesting Results filter
- Filters reset pagination
- Multiple filters work together

### 5. **Artwork Detail Page**
- Navigation from table row
- Back button works
- All tabs accessible:
  - Details
  - Perceptual Features
  - Similar Artworks
  - Vision API Results

### 6. **Vision API Results**
- Interesting results section at top
- Regular results section below
- Auto-expanded details
- Match categories displayed
- Web entities shown
- Full URLs for pages and images

### 7. **Similar Artworks**
- Method selector works
- Refresh button updates results
- Different algorithms selectable

### 8. **Perceptual Features**
- Color swatches display
- Feature sections load

### 9. **Pagination**
- Next/Previous buttons work
- Page info updates
- Navigation maintains state

## Test Output

The test provides detailed console output:
```
🚀 Starting walkthrough test...

📋 Test 1: Loading main page...
✅ Main page loaded successfully

📋 Test 2: Verifying table structure...
✅ Table has 8 columns: Image, Title, Artist, Year, Status, Location, Description, Vision API

...

🎉 Walkthrough test completed successfully!
```

## Customization

### Run in headless mode (no visible browser):
Edit `test_walkthrough.py` and change:
```python
browser = await p.chromium.launch(headless=True)
```

### Adjust speed:
Change the `slow_mo` parameter (in milliseconds):
```python
browser = await p.chromium.launch(headless=False, slow_mo=100)
```

### Use different browser:
Replace `chromium` with `firefox` or `webkit`:
```python
browser = await p.firefox.launch(...)
```

## Troubleshooting

### Server not running
```
Error: net::ERR_CONNECTION_REFUSED at http://localhost:8000
```
**Solution:** Start the FastAPI server first:
```powershell
python -m src.main
```

### Playwright not installed
```
ModuleNotFoundError: No module named 'playwright'
```
**Solution:** Install dependencies:
```powershell
pip install -r tests/e2e/requirements.txt
playwright install chromium
```

### Timeout errors
If tests timeout, increase wait times in the script or ensure your machine can run the application smoothly.

## CI/CD Integration

To run in CI/CD pipelines, use headless mode and install browsers:
```bash
# Install
pip install -r tests/e2e/requirements.txt
playwright install --with-deps chromium

# Run
python tests/e2e/test_walkthrough.py
```

## Future Enhancements

Potential additions:
- Screenshot capture on failures
- Video recording of test runs
- Multiple artwork testing
- Performance metrics
- Network request validation
- Accessibility testing
