# Google Image Search API Setup Guide

This guide explains how to set up and use the Google Custom Search API integration for discovering artwork images.

## Prerequisites

- Google Account
- Active Google Cloud Project

## Setup Steps

### 1. Get Google Custom Search API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Custom Search API**:
   - Navigate to **APIs & Services** > **Library**
   - Search for "Custom Search API"
   - Click **Enable**
4. Create API credentials:
   - Go to **APIs & Services** > **Credentials**
   - Click **Create Credentials** > **API Key**
   - Copy your API key
   - (Optional) Restrict the key to Custom Search API only

### 2. Create Custom Search Engine

1. Go to [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Click **Add** to create a new search engine
3. Configure your search engine:
   - **Search engine name**: Polish Art Database Search
   - **What to search**: Search the entire web
   - **Image search**: ON (enable this!)
   - **SafeSearch**: OFF (for art images)
4. After creation, click **Customize** > **Basic** to get your **Search Engine ID**
5. Copy the Search Engine ID (looks like: `a1b2c3d4e5f6g7h8`)

### 3. Configure Environment Variables

**Windows PowerShell:**
```powershell
# Set for current session
$env:GOOGLE_API_KEY = "your-api-key-here"
$env:GOOGLE_SEARCH_ENGINE_ID = "your-search-engine-id"

# Set permanently (system-wide)
[System.Environment]::SetEnvironmentVariable('GOOGLE_API_KEY', 'your-api-key', 'User')
[System.Environment]::SetEnvironmentVariable('GOOGLE_SEARCH_ENGINE_ID', 'your-search-engine-id', 'User')
```

**Linux/Mac:**
```bash
export GOOGLE_API_KEY="your-api-key-here"
export GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id"

# Add to ~/.bashrc or ~/.zshrc for persistence
echo 'export GOOGLE_API_KEY="your-api-key"' >> ~/.bashrc
echo 'export GOOGLE_SEARCH_ENGINE_ID="your-search-engine-id"' >> ~/.bashrc
```

### 4. Install Dependencies

The required `requests` library should already be installed, but if not:

```powershell
pip install requests
```

## Usage Examples

### Basic Command Line Search

```powershell
# Simple search
python scripts/search_google_images.py --query "Polish folk art" --num 10

# Search with filters
python scripts/search_google_images.py `
    --query "Polish painting 19th century" `
    --size large `
    --type photo `
    --format jpg `
    --num 20

# Search for specific artist
python scripts/search_google_images.py `
    --artist "Jan Matejko" `
    --style "historical painting" `
    --num 15

# Download images
python scripts/search_google_images.py `
    --query "Polish pottery folk art" `
    --download `
    --output data/pottery_images `
    --num 20

# Export results to JSON
python scripts/search_google_images.py `
    --query "Warsaw uprising art" `
    --json results/warsaw_uprising.json `
    --num 30
```

### Programmatic Usage

```python
from src.utils.google_image_search import GoogleImageSearch

# Initialize
searcher = GoogleImageSearch()

# Search for images
results = searcher.search_artwork_images(
    query="Polish folk art painting",
    num_results=10,
    image_size='large',
    file_type='jpg'
)

# Process results
for result in results:
    print(f"Title: {result.title}")
    print(f"URL: {result.link}")
    print(f"Size: {result.width}x{result.height}")
    print(f"Source: {result.display_link}")
    print()

# Specialized Polish art search
polish_results = searcher.search_polish_art(
    artist="Stanisław Wyspiański",
    style="portrait",
    period="Art Nouveau",
    num_results=20
)

# Download an image
from src.utils.google_image_search import download_image

success = download_image(
    url=results[0].link,
    output_path='downloads/image.jpg'
)
```

### Integration with Artwork Database

```python
from src.utils.google_image_search import GoogleImageSearch, download_image
from src.repositories.artwork_repository import SQLiteArtworkRepository
from uuid import uuid4
import os

searcher = GoogleImageSearch()
artwork_repo = SQLiteArtworkRepository("sqlite:///artworks.db")

# Search for artwork
results = searcher.search_polish_art(
    artist="Jan Matejko",
    style="historical painting",
    num_results=10
)

# Download and add to database
for result in results:
    artwork_id = str(uuid4())
    image_path = f"data/images/{artwork_id}.jpg"
    
    # Download image
    if download_image(result.link, image_path):
        # Create artwork entry
        artwork = {
            'id': artwork_id,
            'title': result.title,
            'artist': {'name': 'Jan Matejko'},
            'description': result.snippet,
            'source_url': result.context_link,
            'image_path': image_path
        }
        
        # Add to database
        # artwork_repo.create(artwork)
        print(f"Added: {result.title}")
```

## API Limits and Costs

### Free Tier
- **100 queries per day** (free)
- **10 results per query** maximum
- Suitable for development and small-scale use

### Paid Tier
- **$5 per 1,000 queries** after free tier
- Up to **10,000 queries per day**
- Enable billing in Google Cloud Console

## Command Line Options

```
Search Parameters:
  --query, -q          Search query string
  --artist             Artist name to search for
  --period             Time period (e.g., "19th century")
  --style              Art style (e.g., "folk art", "portrait")
  --num, -n            Number of results (default: 10, max: 100)

Filters:
  --size               Image size: huge, icon, large, medium, small, xlarge, xxlarge
  --type               Image type: clipart, face, lineart, stock, photo, animated
  --format             File format: jpg, png, gif, bmp, svg, webp, ico
  --rights             Usage rights: cc_publicdomain, cc_attribute, cc_sharealike, etc.
  --country            Country code (default: pl for Poland)

Output Options:
  --download, -d       Download images to local directory
  --output, -o         Output directory for downloads
  --json, -j           Export results to JSON file
  --verbose, -v        Verbose output
```

## Troubleshooting

### "Google API key not found" error
- Make sure environment variables are set correctly
- Restart your terminal/IDE after setting variables
- Check spelling of variable names

### "403 Forbidden" error
- Verify your API key is correct
- Check that Custom Search API is enabled in your project
- Ensure billing is enabled (after free tier)

### "Invalid Search Engine ID" error
- Verify your Search Engine ID is correct
- Make sure image search is enabled in your search engine settings

### No results returned
- Try broader search terms
- Remove restrictive filters
- Check that your search engine is set to "Search the entire web"

## Best Practices

1. **Cache results**: Store search results to avoid repeated API calls
2. **Rate limiting**: The utility includes 1-second delays between requests
3. **Error handling**: Always handle potential download failures
4. **Attribution**: Keep track of image sources for proper attribution
5. **Respect quotas**: Monitor your daily API usage

## Next Steps

1. Set up API credentials following steps above
2. Test with a simple search command
3. Integrate with your artwork ingestion pipeline
4. Consider building a batch import tool for larger collections
