# Quick Start: Run the E2E Walkthrough Test

## 1. Install Playwright
```powershell
.venv\Scripts\python.exe -m pip install playwright pytest-playwright pytest-asyncio
.venv\Scripts\python.exe -m playwright install chromium
```

## 2. Start the Server (if not running)
```powershell
.venv\Scripts\python.exe -m src.main
```

## 3. Run the Test
```powershell
.venv\Scripts\python.exe tests/e2e/test_walkthrough.py
```

The test will open a browser window and automatically walk through all features of the site!

## What Gets Tested
✅ Main page loads with 8-column table  
✅ Vision API status icons (🔍 🔥)  
✅ Search functionality  
✅ Filtering (Vision searched, Interesting results)  
✅ Navigation to detail pages  
✅ All 4 tabs (Details, Perceptual, Similar, Vision API)  
✅ Interesting results section at top of Vision API tab  
✅ Similar artworks with method selector  
✅ Pagination  
✅ Back navigation  

Total: **14 automated test scenarios**
