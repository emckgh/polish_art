# Screenshots for funding overview PowerPoint

## Automatic capture (recommended)

Run the Playwright script to start the app (optional), open the list and detail pages, and save screenshots here:

```bash
# With server already running:
python scripts/screenshot_for_pptx.py

# Start server automatically, capture, then stop:
python scripts/screenshot_for_pptx.py --start-server
```

Then regenerate the PowerPoint:

```bash
python scripts/create_funding_overview_pptx.py
```

## Manual capture

If you prefer to take screenshots yourself, place PNGs here:

| File | What to capture |
|------|------------------|
| **screenshot_list.png** | Main artwork list (`/static/index.html`) — table with thumbnails, search, filters |
| **screenshot_detail.png** | Artwork detail page (`/static/detail.html?id=...`) — image, metadata, Vision tab if visible |

Recommended size: ~1200×720 px or similar; the PPTX script will scale them to fit the slide.
