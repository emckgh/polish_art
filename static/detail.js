// Polish Looted Art Database - Detail Page JavaScript

const API_BASE = (typeof window !== 'undefined' && window.location?.origin && window.location.protocol !== 'file:')
    ? `${window.location.origin}/api`
    : '/api';
let artworkId = null;
let artworkData = null;
let featuresData = null;

// Get artwork ID from URL
function getArtworkIdFromUrl() {
    const params = new URLSearchParams(window.location.search);
    return params.get('id');
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    artworkId = getArtworkIdFromUrl();
    
    if (!artworkId) {
        showError('No artwork ID provided');
        return;
    }
    
    setupTabs();
    loadArtworkDetails();
});

// Setup tab switching
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabName = button.getAttribute('data-tab');
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    // Update buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
    
    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}-tab`).classList.add('active');
    
    // Load features data if switching to perceptual tab and not loaded yet
    if (tabName === 'perceptual' && !featuresData) {
        loadFeatures();
    }
    
    // Load Vision API results if switching to vision tab
    if (tabName === 'vision') {
        loadVisionResults();
    }
    
    // Load similar artworks if switching to similar tab
    if (tabName === 'similar') {
        loadSimilarArtworks();
    }
}

// Load artwork details
async function loadArtworkDetails() {
    try {
        const response = await fetch(`${API_BASE}/artworks/${artworkId}`);
        
        if (!response.ok) {
            throw new Error(`Failed to load artwork: ${response.status}`);
        }
        
        artworkData = await response.json();
        displayArtworkDetails();
        
    } catch (error) {
        showError(`Error loading artwork: ${error.message}`);
    }
}

// Display artwork details in general tab
function displayArtworkDetails() {
    // Update header
    document.getElementById('artworkTitle').textContent = artworkData.title;
    if (artworkData.artist) {
        document.getElementById('artworkSubtitle').textContent = 
            `by ${artworkData.artist.name}${artworkData.creation_year ? ` (${artworkData.creation_year})` : ''}`;
    }
    
    // Display image
    const imageContainer = document.getElementById('imageContainer');
    if (artworkData.image_hash) {
        imageContainer.innerHTML = `
            <img src="${API_BASE}/artworks/${artworkId}/image" 
                 alt="${escapeHtml(artworkData.title)}"
                 onerror="this.parentElement.innerHTML='<div class=\\'no-image-large\\'>Image not available</div>'">
        `;
    } else {
        imageContainer.innerHTML = '<div class="no-image-large">No image available</div>';
    }
    
    // Basic Information
    document.getElementById('basicInfo').innerHTML = `
        <div class="info-item">
            <div class="info-label">Title</div>
            <div class="info-value">${escapeHtml(artworkData.title)}</div>
        </div>
        ${artworkData.creation_year ? `
            <div class="info-item">
                <div class="info-label">Year Created</div>
                <div class="info-value">${artworkData.creation_year}</div>
            </div>
        ` : ''}
        ${artworkData.image_hash ? `
            <div class="info-item">
                <div class="info-label">Image Available</div>
                <div class="info-value">✓ Yes</div>
            </div>
        ` : ''}
    `;
    
    // Artist Information
    if (artworkData.artist) {
        document.getElementById('artistInfo').innerHTML = `
            <div class="info-item">
                <div class="info-label">Artist Name</div>
                <div class="info-value">${escapeHtml(artworkData.artist.name)}</div>
            </div>
            ${artworkData.artist.birth_year ? `
                <div class="info-item">
                    <div class="info-label">Birth Year</div>
                    <div class="info-value">${artworkData.artist.birth_year}</div>
                </div>
            ` : ''}
            ${artworkData.artist.death_year ? `
                <div class="info-item">
                    <div class="info-label">Death Year</div>
                    <div class="info-value">${artworkData.artist.death_year}</div>
                </div>
            ` : ''}
            ${artworkData.artist.nationality ? `
                <div class="info-item">
                    <div class="info-label">Nationality</div>
                    <div class="info-value">${escapeHtml(artworkData.artist.nationality)}</div>
                </div>
            ` : ''}
        `;
    } else {
        document.getElementById('artistInfo').innerHTML = '<div class="info-value">Artist information not available</div>';
    }
    
    // Status & Location
    document.getElementById('statusInfo').innerHTML = `
        <div class="info-item">
            <div class="info-label">Status</div>
            <div class="info-value">
                <span class="artwork-status ${artworkData.status.toLowerCase().replace('_', '-')}">
                    ${escapeHtml(artworkData.status).replace(/_/g, ' ')}
                </span>
            </div>
        </div>
        ${artworkData.last_known_location ? `
            <div class="info-item">
                <div class="info-label">Last Known Location</div>
                <div class="info-value">${escapeHtml(artworkData.last_known_location)}</div>
            </div>
        ` : ''}
        ${artworkData.last_known_date ? `
            <div class="info-item">
                <div class="info-label">Last Known Date</div>
                <div class="info-value">${new Date(artworkData.last_known_date).toLocaleDateString()}</div>
            </div>
        ` : ''}
    `;
    
    // Description
    if (artworkData.description) {
        document.getElementById('descriptionInfo').innerHTML = `
            <div class="info-value">${escapeHtml(artworkData.description)}</div>
        `;
    } else {
        document.getElementById('descriptionInfo').innerHTML = '<div class="info-value">No description available</div>';
    }
    
    // Database Metadata
    document.getElementById('metadataInfo').innerHTML = `
        <div class="info-item">
            <div class="info-label">Artwork ID</div>
            <div class="info-value"><code>${escapeHtml(artworkData.id)}</code></div>
        </div>
        <div class="info-item">
            <div class="info-label">Added to Database</div>
            <div class="info-value">${new Date(artworkData.created_at).toLocaleString()}</div>
        </div>
        <div class="info-item">
            <div class="info-label">Last Updated</div>
            <div class="info-value">${new Date(artworkData.updated_at).toLocaleString()}</div>
        </div>
        ${artworkData.image_hash ? `
            <div class="info-item">
                <div class="info-label">Image Hash</div>
                <div class="info-value"><code>${escapeHtml(artworkData.image_hash)}</code></div>
            </div>
        ` : ''}
    `;
}

// Load feature data
async function loadFeatures() {
    try {
        const response = await fetch(`${API_BASE}/artworks/${artworkId}/features`);
        
        if (!response.ok) {
            if (response.status === 404) {
                displayNoFeaturesMessage();
                return;
            }
            throw new Error(`Failed to load features: ${response.status}`);
        }
        
        featuresData = await response.json();
        displayFeatures();
        
    } catch (error) {
        document.getElementById('hashValues').innerHTML = 
            `<div class="alert alert-error">Error loading features: ${error.message}</div>`;
    }
}

// Display no features message
function displayNoFeaturesMessage() {
    const message = `
        <div class="alert alert-info">
            <strong>No feature data available</strong><br>
            Computer vision features have not been extracted for this artwork yet. 
            Features can be extracted by running the feature extraction tool on the database.
        </div>
    `;
    
    document.getElementById('hashValues').innerHTML = message;
    document.getElementById('imageProps').innerHTML = message;
    document.getElementById('qualityMetrics').innerHTML = message;
    document.getElementById('dominantColors').innerHTML = message;
    document.getElementById('clipEmbedding').innerHTML = message;
}

// Display features in perceptual tab
function displayFeatures() {
    // Hash Values
    document.getElementById('hashValues').innerHTML = `
        <div class="hash-item">
            <div class="hash-type">pHash (Perceptual Hash)</div>
            <div class="hash-value">${featuresData.phash || 'N/A'}</div>
            <div class="hash-description">
                DCT-based hash, robust to rotation and scaling. Best for finding similar images.
            </div>
        </div>
        <div class="hash-item">
            <div class="hash-type">dHash (Difference Hash)</div>
            <div class="hash-value">${featuresData.dhash || 'N/A'}</div>
            <div class="hash-description">
                Gradient-based hash, detects image transformations and changes.
            </div>
        </div>
        <div class="hash-item">
            <div class="hash-type">aHash (Average Hash)</div>
            <div class="hash-value">${featuresData.ahash || 'N/A'}</div>
            <div class="hash-description">
                Average-based hash, fast duplicate detection method.
            </div>
        </div>
    `;
    
    // Image Properties
    document.getElementById('imageProps').innerHTML = `
        ${featuresData.width_pixels ? `
            <div class="info-item">
                <div class="info-label">Dimensions</div>
                <div class="info-value">${featuresData.width_pixels} × ${featuresData.height_pixels} pixels</div>
            </div>
        ` : ''}
        ${featuresData.aspect_ratio ? `
            <div class="info-item">
                <div class="info-label">Aspect Ratio</div>
                <div class="info-value">${featuresData.aspect_ratio.toFixed(3)}</div>
            </div>
        ` : ''}
        ${featuresData.format ? `
            <div class="info-item">
                <div class="info-label">Format</div>
                <div class="info-value">${featuresData.format.toUpperCase()}</div>
            </div>
        ` : ''}
        ${featuresData.file_size_bytes ? `
            <div class="info-item">
                <div class="info-label">File Size</div>
                <div class="info-value">${formatBytes(featuresData.file_size_bytes)}</div>
            </div>
        ` : ''}
        ${featuresData.color_space ? `
            <div class="info-item">
                <div class="info-label">Color Space</div>
                <div class="info-value">${featuresData.color_space}</div>
            </div>
        ` : ''}
        <div class="info-item">
            <div class="info-label">Grayscale</div>
            <div class="info-value">${featuresData.is_grayscale ? 'Yes' : 'No'}</div>
        </div>
    `;
    
    // Quality Metrics
    document.getElementById('qualityMetrics').innerHTML = `
        ${featuresData.sharpness_score !== null ? `
            <div class="info-item">
                <div class="info-label">Sharpness Score</div>
                <div class="info-value">${featuresData.sharpness_score.toFixed(3)}</div>
                <div class="quality-bar">
                    <div class="quality-bar-bg">
                        <div class="quality-bar-fill" style="width: ${Math.min(featuresData.sharpness_score * 50, 100)}%">
                            ${(featuresData.sharpness_score * 100).toFixed(0)}%
                        </div>
                    </div>
                </div>
            </div>
        ` : ''}
        ${featuresData.contrast_score !== null ? `
            <div class="info-item">
                <div class="info-label">Contrast Score</div>
                <div class="info-value">${featuresData.contrast_score.toFixed(3)}</div>
                <div class="quality-bar">
                    <div class="quality-bar-bg">
                        <div class="quality-bar-fill" style="width: ${Math.min(featuresData.contrast_score * 100, 100)}%">
                            ${(featuresData.contrast_score * 100).toFixed(0)}%
                        </div>
                    </div>
                </div>
            </div>
        ` : ''}
        ${featuresData.brightness_avg !== null ? `
            <div class="info-item">
                <div class="info-label">Brightness Average</div>
                <div class="info-value">${featuresData.brightness_avg.toFixed(1)} / 255</div>
                <div class="quality-bar">
                    <div class="quality-bar-bg">
                        <div class="quality-bar-fill" style="width: ${(featuresData.brightness_avg / 255 * 100)}%">
                            ${((featuresData.brightness_avg / 255) * 100).toFixed(0)}%
                        </div>
                    </div>
                </div>
            </div>
        ` : ''}
    `;
    
    // Dominant Colors
    if (featuresData.dominant_colors && featuresData.dominant_colors.length > 0) {
        document.getElementById('dominantColors').innerHTML = `
            <div class="color-swatches">
                ${featuresData.dominant_colors.map((color, idx) => `
                    <div class="color-swatch">
                        <div class="color-box" style="background-color: rgb(${color[0]}, ${color[1]}, ${color[2]})"></div>
                        <div class="color-rgb">
                            <div><strong>#${idx + 1}</strong></div>
                            <div>RGB(${color[0]}, ${color[1]}, ${color[2]})</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        `;
    } else {
        document.getElementById('dominantColors').innerHTML = '<div class="info-value">No color data available</div>';
    }
    
    // CLIP Embedding
    if (featuresData.clip_embedding && featuresData.clip_embedding.length > 0) {
        const embedding = featuresData.clip_embedding;
        const mean = embedding.reduce((a, b) => a + b, 0) / embedding.length;
        const variance = embedding.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / embedding.length;
        const stdDev = Math.sqrt(variance);
        const min = Math.min(...embedding);
        const max = Math.max(...embedding);
        
        document.getElementById('clipEmbedding').innerHTML = `
            <div class="embedding-stats">
                <div class="embedding-stat">
                    <div class="embedding-stat-label">Dimensions</div>
                    <div class="embedding-stat-value">${embedding.length}</div>
                </div>
                <div class="embedding-stat">
                    <div class="embedding-stat-label">Mean</div>
                    <div class="embedding-stat-value">${mean.toFixed(4)}</div>
                </div>
                <div class="embedding-stat">
                    <div class="embedding-stat-label">Std Dev</div>
                    <div class="embedding-stat-value">${stdDev.toFixed(4)}</div>
                </div>
                <div class="embedding-stat">
                    <div class="embedding-stat-label">Min</div>
                    <div class="embedding-stat-value">${min.toFixed(4)}</div>
                </div>
                <div class="embedding-stat">
                    <div class="embedding-stat-label">Max</div>
                    <div class="embedding-stat-value">${max.toFixed(4)}</div>
                </div>
            </div>
            <div class="info-item" style="margin-top: 20px;">
                <div class="info-label">First 20 values</div>
                <div class="info-value code-block">[${embedding.slice(0, 20).map(v => v.toFixed(4)).join(', ')}...]</div>
            </div>
            <div class="info-item">
                <div class="info-label">Model Version</div>
                <div class="info-value"><code>${featuresData.model_version || 'N/A'}</code></div>
            </div>
            ${featuresData.extraction_timestamp ? `
                <div class="info-item">
                    <div class="info-label">Extracted</div>
                    <div class="info-value">${new Date(featuresData.extraction_timestamp).toLocaleString()}</div>
                </div>
            ` : ''}
        `;
    } else {
        document.getElementById('clipEmbedding').innerHTML = '<div class="info-value">No embedding data available</div>';
    }
}

// Utility functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Load similar artworks
let similarData = null;

async function loadSimilarArtworks() {
    // Set up refresh button if not already done
    const refreshBtn = document.getElementById('refreshSimilar');
    if (refreshBtn && !refreshBtn.dataset.initialized) {
        refreshBtn.addEventListener('click', () => {
            similarData = null; // Clear cache
            loadSimilarArtworks();
        });
        refreshBtn.dataset.initialized = 'true';
    }
    
    // Return cached data if available
    if (similarData) {
        displaySimilarArtworks(similarData);
        return;
    }
    
    const resultsContainer = document.getElementById('similarResults');
    resultsContainer.innerHTML = '<div class="loading-placeholder">Loading similar artworks...</div>';
    
    try {
        const method = document.getElementById('similarityMethod').value;
        const response = await fetch(`${API_BASE}/artworks/${artworkId}/similar?method=${method}&limit=12`);
        
        if (!response.ok) {
            throw new Error(`Failed to load similar artworks: ${response.status}`);
        }
        
        similarData = await response.json();
        displaySimilarArtworks(similarData);
        
    } catch (error) {
        resultsContainer.innerHTML = `
            <div class="alert alert-error">
                <strong>Error loading similar artworks:</strong><br>
                ${error.message}
            </div>
        `;
    }
}

function displaySimilarArtworks(data) {
    const resultsContainer = document.getElementById('similarResults');
    
    if (!data.similar_artworks || data.similar_artworks.length === 0) {
        resultsContainer.innerHTML = `
            <div class="no-similar">
                <h3>No similar artworks found</h3>
                <p>Try adjusting the similarity method or check if features have been extracted.</p>
            </div>
        `;
        return;
    }
    
    // Build grid of similar artworks
    const cardsHtml = data.similar_artworks.map(artwork => {
        const imageUrl = artwork.image_hash 
            ? `${API_BASE}/artworks/${artwork.artwork_id}/image`
            : null;
        
        const scorePercent = (artwork.similarity_score * 100).toFixed(1);
        const scoreWidth = Math.min(artwork.similarity_score * 100, 100);
        
        // Determine method badges
        const methods = artwork.methods || [artwork.method];
        const methodBadges = methods.map(m => {
            const displayName = m === 'perceptual_hash' ? 'Hash' : 
                               m === 'clip_embedding' ? 'CLIP' : m;
            return `<span class="method-badge">${displayName}</span>`;
        }).join('');
        
        return `
            <div class="similar-card" onclick="window.location.href='/static/detail.html?id=${artwork.artwork_id}'">
                ${imageUrl ? 
                    `<img src="${imageUrl}" alt="${escapeHtml(artwork.title)}" class="similar-card-image" onerror="this.parentElement.querySelector('.similar-card-placeholder') ? this.style.display='none' : this.outerHTML='<div class=\\'similar-card-placeholder\\'>No Image</div>'">` :
                    `<div class="similar-card-placeholder">No Image</div>`
                }
                <div class="similar-card-content">
                    <div class="similar-card-title">${escapeHtml(artwork.title)}</div>
                    <div class="similar-card-artist">
                        ${artwork.artist ? escapeHtml(artwork.artist) : 'Unknown Artist'}
                        ${artwork.creation_year ? ` (${artwork.creation_year})` : ''}
                    </div>
                    <div class="similarity-score">
                        <span class="score-label">Match:</span>
                        <div class="score-bar">
                            <div class="score-bar-fill" style="width: ${scoreWidth}%"></div>
                        </div>
                        <span class="score-value">${scorePercent}%</span>
                    </div>
                    <div class="similarity-methods">
                        ${methodBadges}
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    resultsContainer.innerHTML = cardsHtml;
}

// Load Vision API results
async function loadVisionResults() {
    const container = document.getElementById('visionSearches');
    
    try {
        const response = await fetch(`${API_BASE}/vision/artwork/${artworkId}/searches`);
        
        if (!response.ok) {
            if (response.status === 404) {
                displayNoVisionResults(container);
                return;
            }
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        displayVisionResults(container, data);
        
    } catch (error) {
        container.innerHTML = `
            <div class="error-message">
                <p>Error loading Vision API results: ${escapeHtml(error.message)}</p>
            </div>
        `;
    }
}

function displayNoVisionResults(container) {
    container.innerHTML = `
        <div class="no-data-message">
            <p><strong>No Vision API searches performed yet.</strong></p>
            <p>This artwork hasn't been searched using Google Cloud Vision API.</p>
            <p>To search for this artwork online, run:</p>
            <pre>python scripts/batch_vision_search.py --artwork-id "${artworkId}"</pre>
        </div>
    `;
}

async function displayVisionResults(container, data) {
    if (!data.searches || data.searches.length === 0) {
        displayNoVisionResults(container);
        return;
    }
    
    // Separate interesting and regular results
    const interestingSearches = data.searches.filter(s => s.has_interesting_results);
    const regularSearches = data.searches.filter(s => !s.has_interesting_results);
    
    let html = `
        <div class="vision-summary">
            <p><strong>${data.total_searches}</strong> search${data.total_searches !== 1 ? 'es' : ''} performed</p>
            ${interestingSearches.length > 0 ? `<p class="interesting-count">🔥 <strong>${interestingSearches.length}</strong> with interesting results</p>` : ''}
        </div>
    `;
    
    // Display interesting results first
    if (interestingSearches.length > 0) {
        html += `
            <div class="interesting-results-section">
                <h3 class="section-heading">🔥 Interesting Results</h3>
        `;
        
        for (let index = 0; index < interestingSearches.length; index++) {
            html += renderSearchItem(interestingSearches[index], index + 1, true);
        }
        
        html += `</div>`;
    }
    
    // Display regular results
    if (regularSearches.length > 0) {
        html += `
            <div class="regular-results-section">
                <h3 class="section-heading">Other Searches</h3>
        `;
        
        for (let index = 0; index < regularSearches.length; index++) {
            html += renderSearchItem(regularSearches[index], interestingSearches.length + index + 1, false);
        }
        
        html += `</div>`;
    }
    
    container.innerHTML = html;
    
    // Load details for all searches
    for (const search of data.searches) {
        await loadAndDisplayVisionDetails(search.id);
    }
}

function renderSearchItem(search, displayIndex, isInteresting) {
    const timestamp = new Date(search.request_timestamp).toLocaleString();
    const statusClass = isInteresting ? 'interesting' : 'no-results';
    const statusIcon = isInteresting ? '🔥' : '✓';
    
    return `
        <div class="vision-search-item ${statusClass}">
            <div class="vision-search-header">
                <div class="vision-search-date">
                    <strong>${statusIcon} Search ${displayIndex}</strong>
                    <span class="timestamp">${timestamp}</span>
                </div>
                <div class="vision-search-stats">
                    <span class="stat-badge">Full: ${search.total_full_matches}</span>
                    <span class="stat-badge">Partial: ${search.total_partial_matches}</span>
                    <span class="stat-badge">Similar: ${search.total_similar_images}</span>
                    <span class="stat-badge">Pages: ${search.total_pages_with_image}</span>
                </div>
            </div>
            
            <div class="vision-search-details">
                ${isInteresting ? `<p class="interesting-label">⚠️ <strong>Interesting results found!</strong></p>` : ''}
                ${search.best_match_score ? `<p>Best match score: ${search.best_match_score.toFixed(3)}</p>` : ''}
                <div id="vision-details-${search.id}" class="vision-details-container">
                    <div class="loading-placeholder">Loading details...</div>
                </div>
            </div>
            
            <div class="vision-search-meta">
                <span>Processing time: ${search.processing_time_ms || 'N/A'}ms</span>
                <span>API cost: ${search.api_cost_units} unit(s)</span>
            </div>
        </div>
    `;
}

async function loadAndDisplayVisionDetails(searchId) {
    const detailsContainer = document.getElementById(`vision-details-${searchId}`);
    if (!detailsContainer) return;

    detailsContainer.innerHTML = '<div class="loading-placeholder">Loading details...</div>';

    try {
        const response = await fetch(`${API_BASE}/vision/request/${searchId}`);
        if (response.status === 404) {
            detailsContainer.innerHTML = '<p class="no-data-message">No details stored for this search.</p>';
            return;
        }
        if (!response.ok) throw new Error('Failed to load details');

        const finding = await response.json();

        // Build detailed matches display
        let html = '<div class="vision-matches-list">';

        // Show summary stats
        html += `
            <div class="vision-stats-summary">
                <div class="stat-item"><strong>Full Matches:</strong> ${finding.total_full_matches}</div>
                <div class="stat-item"><strong>Partial Matches:</strong> ${finding.total_partial_matches}</div>
                <div class="stat-item"><strong>Similar Images:</strong> ${finding.total_similar_images}</div>
                <div class="stat-item"><strong>Pages with Image:</strong> ${finding.total_pages_with_image}</div>
                ${finding.best_match_score ? `<div class="stat-item"><strong>Best Score:</strong> ${finding.best_match_score.toFixed(3)}</div>` : ''}
                ${finding.processing_time_ms ? `<div class="stat-item"><strong>Processing:</strong> ${finding.processing_time_ms}ms</div>` : ''}
            </div>
        `;

        // Show web entities first (context/labels)
        if (finding.web_entities && finding.web_entities.length > 0) {
            html += `
                <div class="vision-context-section">
                    <h4 class="vision-context-title">🏷️ CONTEXT & LABELS (${finding.web_entities.length} entities)</h4>
                    <div class="vision-entities">
            `;
            
            finding.web_entities.forEach(entity => {
                const scorePercent = entity.entity_score ? (entity.entity_score * 100).toFixed(0) : '';
                html += `
                    <span class="vision-entity-tag">
                        ${escapeHtml(entity.entity_description)}
                        ${scorePercent ? `<span class="entity-score">${scorePercent}%</span>` : ''}
                    </span>
                `;
            });
            
            html += '</div></div>';
        }
        
        if (finding.matches && finding.matches.length > 0) {
            // Group by category
            const byCategory = {};
            finding.matches.forEach(match => {
                const cat = match.domain_category || 'other';
                if (!byCategory[cat]) byCategory[cat] = [];
                byCategory[cat].push(match);
            });
            
            // Display each category
            Object.keys(byCategory).sort().forEach(category => {
                const categoryIcon = {
                    'auction': '🔨',
                    'marketplace': '🛒',
                    'museum': '🏛️',
                    'social': '📱',
                    'academic': '🎓',
                    'other': '🔗'
                }[category] || '🔗';
                
                html += `
                    <div class="vision-category-section">
                        <h4 class="vision-category-title">${categoryIcon} ${category.toUpperCase()} (${byCategory[category].length})</h4>
                        <div class="vision-matches">
                `;
                
                byCategory[category].forEach((match, i) => {
                    html += `
                        <div class="vision-match-item">
                            <div class="vision-match-header">
                                <span class="vision-match-type">${match.match_type}</span>
                                <strong>${escapeHtml(match.domain || 'Unknown domain')}</strong>
                            </div>
                    `;
                    
                    if (match.page_title) {
                        html += `<div class="vision-match-title">📄 ${escapeHtml(match.page_title)}</div>`;
                    }
                    
                    // Show page URL if available
                    if (match.page_url) {
                        html += `
                            <div class="vision-match-url">
                                <strong>Page:</strong> <a href="${escapeHtml(match.page_url)}" target="_blank" rel="noopener noreferrer" class="full-url-link">
                                    🔗 ${escapeHtml(match.page_url)}
                                </a>
                            </div>
                        `;
                    }
                    
                    // Show image URL if available
                    if (match.image_url) {
                        html += `
                            <div class="vision-match-url">
                                <strong>Image:</strong> <a href="${escapeHtml(match.image_url)}" target="_blank" rel="noopener noreferrer" class="full-url-link">
                                    🖼️ ${escapeHtml(match.image_url)}
                                </a>
                            </div>
                        `;
                    }
                    
                    if (match.confidence_score) {
                        html += `<div class="vision-match-score">Confidence: ${match.confidence_score.toFixed(3)}</div>`;
                    }
                    
                    html += '</div>';
                });
                
                html += '</div></div>';
            });
        } else {
            html += '<p>No detailed matches available.</p>';
        }
        
        html += '</div>';
        
        detailsContainer.innerHTML = html;
        
    } catch (error) {
        detailsContainer.innerHTML = `<p class="error-message">Error loading details: ${escapeHtml(error.message)}</p>`;
    }
}

function showError(message) {
    document.getElementById('artworkTitle').textContent = 'Error';
    document.getElementById('artworkSubtitle').textContent = message;
    document.getElementById('imageContainer').innerHTML = 
        `<div class="alert alert-error">${message}</div>`;
}
