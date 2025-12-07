# Polish Looted Art Discovery Engine

A cost-effective, scalable system for discovering images of looted Polish art online using web scraping, computer vision, and machine learning techniques.

## Overview

This engine helps identify potentially looted Polish artwork by:
- Scraping auction houses, galleries, and online marketplaces
- Processing and analyzing artwork images
- Matching discovered images against known looted art databases
- Tracking provenance gaps and suspicious ownership patterns

## Architecture

### Project Structure

```
polish_art/
├── README.md                   # This file (only file in root)
├── data/
│   └── artworks.db            # SQLite database
├── src/
│   ├── main.py                # FastAPI application entry point
│   ├── domain/                # Core business entities
│   ├── repositories/          # Data access layer
│   ├── services/              # Business logic orchestration
│   ├── scrapers/              # Web scraping implementations
│   ├── cv_pipeline/           # Computer vision processing pipeline
│   ├── matching/              # Similarity matching algorithms
│   ├── api/                   # FastAPI REST endpoints
│   └── infrastructure/        # Cross-cutting concerns
├── scripts/
│   ├── scrape_lootedart_gov_pl.py   # Polish Ministry scraper
│   ├── scrape_all_obids.py          # Comprehensive obid scraper
│   ├── import_looted_art.py         # Import from JSON to database
│   └── extract_features.py          # CV feature extraction
├── static/                    # Frontend HTML/CSS/JS
├── tests/                     # Test files
└── temp/                      # Temporary/test artifacts (not in git)
```

### Core Principles

- **Componentization**: Single responsibility, separation of concerns
- **Testability**: Dependency injection, interface-driven design
- **Minimal Coupling**: Layer isolation, event-driven communication
- **No Magic Values**: All constants externalized
- **Size Constraints**: Functions ≤20 lines, modules ≤250 lines

See `.cursorrules` for complete architectural guidelines.

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (or SQLite for development)
- Redis 7+ (optional, for task queue)

### Installation

1. **Clone and navigate to project**
```powershell
cd C:\Users\msft\Documents\polish-art-engine
```

2. **Create virtual environment**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. **Install dependencies**
```powershell
pip install -r requirements.txt
```

4. **Configure environment**
```powershell
cp .env.example .env
# Edit .env with your configuration
```

5. **Initialize database**
```powershell
# Coming soon: alembic upgrade head
```

### Development Setup

**Install development dependencies:**
```powershell
pip install -e ".[dev]"
```

**Run tests:**
```powershell
pytest
```

**Code formatting:**
```powershell
black src/ tests/
isort src/ tests/
```

**Type checking:**
```powershell
mypy src/
```

**Linting:**
```powershell
flake8 src/
pylint src/
```

## Project Phases

### Phase 1: Foundation (Current)
- ✅ Project structure and configuration
- ⏳ Reference database schema
- ⏳ Base interfaces and domain models
- ⏳ Image preprocessing pipeline

### Phase 2: Web Scraping
- Targeted website scrapers (auction houses, galleries)
- Social media monitoring
- Reverse image search integration
- Rate limiting and respectful crawling

### Phase 3: Intelligent Matching
- Perceptual hash comparison
- Feature vector similarity (CLIP embeddings)
- OCR for metadata extraction
- Similarity scoring system

### Phase 4: Expansion
- Dark web monitoring
- NLP for description parsing
- Fine-tuned CV models for Polish art
- Network analysis of sellers

### Phase 5: Advanced Intelligence
- Blockchain/NFT tracking
- Law enforcement integration
- Public reporting interface

## Usage

### Start API Server
```powershell
python -m src.main
```

### Run Scraper
```powershell
# Coming soon
python -m src.scrapers.auction_scraper
```

### Process Images
```powershell
# Coming soon
python -m src.cv_pipeline.batch_processor
```

## Configuration

All configuration in `config/` or environment variables:

- `config/settings.py` - Application settings
- `config/constants.py` - Business constants
- `.env` - Secrets and environment-specific values

## Testing

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/services/test_artwork_service.py

# Run integration tests only
pytest tests/integration/
```

## Contributing

### Code Standards

- Follow architectural guidelines in `.cursorrules`
- All public APIs must have type hints and docstrings
- Test coverage required for new code (80%+ for critical paths)
- No magic numbers or strings
- Functions ≤20 lines, modules ≤250 lines

### Commit Guidelines

- Atomic commits (one logical change)
- Descriptive messages (imperative mood)
- Branch naming: `feature/`, `bugfix/`, `hotfix/`

## Cost Optimization

- Uses free API tiers (Google Custom Search, TinEye)
- Local processing with pre-trained models
- Efficient caching and batch operations
- Minimal cloud infrastructure requirements

Estimated monthly cost: **<$50** for initial deployment

## License

[Choose appropriate license]

## Contact

[Your contact information]

## Acknowledgments

Built to support the recovery of cultural heritage looted during WWII and subsequent periods.
