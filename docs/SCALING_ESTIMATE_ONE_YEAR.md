# One-year data estimate: full Polish database + monthly Vision scans

Rough sizing if you scale to **all artworks** in the Polish looted-art web database and run **monthly** Google Vision API scans for a year, with **extra focus on auction sites**.

---

## Inputs (from your current DB and public sources)

| Input | Value |
|--------|--------|
| **Current DB** | 1,376 artworks, 620 MB |
| **Per artwork (with image)** | ~455 KB (image BLOB dominates) |
| **Per Vision request stored** | ~4.9 KB (request + matches + entities; only “interesting” results get full detail) |
| **Vision rows per request** | ~13 matches, ~4 entities (when stored); domain_stats aggregated |

**Polish database scale (public sources):**

- **~63,000** object records (“sites”) in the electronic DB (Division for Looted Art, Ministry of Culture).
- **516,000+** total moveable cultural losses (not all in the same DB).

Estimates below use **65,000** as “full web DB” and **100,000** as a slightly higher scenario.

**Scan cadence:**

- **Monthly** = 12 Vision requests per artwork per year.
- **Auction focus** = assume ~20–25% of artworks get extra rescans (e.g. when auction hits exist).  
  → **~15 Vision requests per artwork per year** on average.

---

## Storage (disk) for one year

| Scenario | Artworks (N) | Base (artworks + images) | Vision (1 year, ~15 req/artwork) | Domain stats + overhead | **Total (approx)** |
|----------|---------------|---------------------------|----------------------------------|--------------------------|---------------------|
| Full web DB | 65,000 | ~30 GB | ~5 GB | ~0.5 GB | **~35 GB** |
| Upper | 100,000 | ~46 GB | ~7.5 GB | ~0.5 GB | **~54 GB** |
| If DB ever ~500k items | 500,000 | ~227 GB | ~37 GB | ~2 GB | **~265 GB** |

**Formulas:**

- Base: `N × 455 KB` (artworks + image BLOBs).
- Vision per year: `N × 15 × 4.9 KB ≈ N × 73.5 KB`.
- Domain_stats and indexes: add ~5–10% of Vision storage.

So for **one year**, scaling to the full Polish web database and monthly scans with auction focus:

- **~65k artworks → ~35 GB**
- **~100k artworks → ~54 GB**

Recommend planning **50–60 GB** for the 65k case (indexes, growth, backups) and **~70 GB** for 100k.

---

## Vision API usage (cost) for one year

- **Requests/year** ≈ N × 15 (e.g. 65,000 × 15 = **975,000** requests).
- Google Vision API “Product Search” / reverse image is billed per **unit** (often 1 unit per request). Check current pricing; at roughly $3.50 / 1,000 units that’s about **$3,400/year** for 975k requests (order-of-magnitude only).

Auction-focused rescans only add a small fraction of that if limited to a subset of artworks.

---

## Summary

| Item | Estimate (65k artworks, 1 year) |
|------|----------------------------------|
| **Disk** | **~35 GB** (plan **50–60 GB** with headroom) |
| **Vision API requests** | **~975k/year** |
| **DB rows (order of magnitude)** | ~65k artworks + ~1M vision_api_requests + ~13M vision_api_matches + ~4M vision_api_entities; domain_stats ~20–30k rows |

If you scale to **100k** artworks: **~54 GB** storage, **~1.5M** Vision requests/year.
