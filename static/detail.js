// Polish Looted Art Database - Detail Page JavaScript

const API_BASE = '/api';
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

function showError(message) {
    document.getElementById('artworkTitle').textContent = 'Error';
    document.getElementById('artworkSubtitle').textContent = message;
    document.getElementById('imageContainer').innerHTML = 
        `<div class="alert alert-error">${message}</div>`;
}
