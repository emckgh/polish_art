# Image Missing Issue - Root Cause Analysis

## Issue
"After the Waters Have Receded" artwork displays "No Image" in the UI despite having an `image_url` in the database.

## Root Cause

The image URL `http://lootedart.gov.pl/image?zdjecie_id=33614&dzielo_id=36371&size=big` returns **HTML instead of image data**.

### Evidence
```bash
Status Code: 200
Content-Type: text/html; charset=utf-8
Content-Length: 30718 bytes
Content starts with: <!DOCTYPE html>
```

The Polish government website is returning an error page or redirect page as HTML instead of serving the actual image file.

## How It's Handled

### ✅ Correct Behavior (Working as Designed)

The `ImageDownloadService` **correctly rejects** this invalid response:

1. **Content-Type Validation** - Service checks `Content-Type` header
2. **Rejection Logic** - Returns `None` if content type is not `image/*`
3. **Graceful Degradation** - Artwork is imported WITHOUT image data
4. **Data Integrity** - No HTML is stored in the `image_data` field

### Code Location
`src/services/image_download_service.py` lines 67-70:
```python
# Validate content type is actually an image
if not content_type.startswith('image/'):
    print(f"Invalid content type {content_type} for {url}")
    return None
```

## Why This Happens

Possible reasons the Polish site returns HTML:
1. **Access restrictions** - Image endpoint may require authentication or session
2. **Rate limiting** - Too many requests triggered protection
3. **Broken link** - Image ID no longer valid in their database
4. **JavaScript requirement** - URL may need to be accessed via browser with cookies

## Test Coverage

Created comprehensive test suite in `tests/unit/test_image_download_validation.py`:

### Tests (12 total - All Passing ✓)

**Content Validation:**
- ✓ `test_rejects_html_content_type` - Confirms HTML responses rejected
- ✓ `test_rejects_json_content_type` - Confirms JSON responses rejected  
- ✓ `test_accepts_valid_image_content_types` - Confirms valid MIME types accepted

**Error Handling:**
- ✓ `test_handles_404_errors` - 404 Not Found handled gracefully
- ✓ `test_handles_500_errors` - Server errors handled gracefully
- ✓ `test_handles_network_errors` - Network exceptions handled gracefully

**Integration:**
- ✓ `test_artwork_without_image_data_when_url_invalid` - Artwork imported without image
- ✓ `test_artwork_with_image_data_when_valid` - Valid images stored correctly
- ✓ `test_real_lootedart_url_validation` - **Confirms actual URL returns HTML**
- ✓ `test_database_should_not_have_html_as_image_data` - **Verifies no HTML in DB**
- ✓ `test_artworks_without_images_still_have_metadata` - **Confirms metadata preserved**

**Size Limits:**
- ✓ `test_enforces_size_limit` - Images over 10MB rejected

## Current Database State

- **Total artworks:** 7
- **With images:** 6 (86% success rate)
- **Without images:** 1 ("After the Waters Have Receded")
- **HTML stored as images:** 0 ✓

## Impact

### ✅ Positive
- Data integrity maintained
- No invalid data in database
- Artwork metadata still searchable
- System handles edge cases gracefully

### ⚠️ User Experience
- One artwork shows "No Image" placeholder in UI
- User can still see title, artist, year, and description
- Image URL is preserved in database for future retry

## Recommendations

### Short Term (Current Approach)
✓ **Keep current validation** - Prevents data corruption
✓ **Display placeholder** - UI shows "No Image" gracefully
✓ **Preserve metadata** - All other artwork data remains searchable

### Future Enhancements

1. **Retry Mechanism**
   - Periodic background job to retry failed image downloads
   - Exponential backoff for rate-limited URLs

2. **Alternative Image Sources**
   - Try different size parameters (`size=medium`, `size=small`)
   - Attempt multiple image IDs if available
   - Fallback to thumbnail versions

3. **Browser Simulation**
   - Use Selenium/Playwright for JavaScript-dependent sites
   - Handle cookie-based authentication
   - Respect session requirements

4. **Manual Override**
   - Allow admin to upload images manually for failed URLs
   - UI to flag artworks needing manual image upload

5. **Source Diversification**
   - Cross-reference with other art databases
   - Use reverse image search on successfully downloaded images
   - Integrate with museum APIs

## Testing

Run validation tests:
```bash
pytest tests/unit/test_image_download_validation.py -v
```

All tests pass (12/12) ✓

## Conclusion

**The missing image is NOT a bug** - it's the system working correctly by rejecting invalid data. The Polish government website is returning HTML error pages instead of images, and our validation layer properly detects and rejects this to maintain data integrity.

The artwork remains fully searchable with complete metadata (title, artist, year, description), just without the visual component.
