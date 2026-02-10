// Polish Looted Art Database - Frontend JavaScript

// Use current origin so API works when served from any host (localhost, LAN IP, etc.)
const API_BASE = (typeof window !== 'undefined' && window.location?.origin && window.location.protocol !== 'file:')
    ? `${window.location.origin}/api`
    : '/api';
let currentPage = 1;
let currentQuery = '';
const pageSize = 10;
let visionStatusMap = new Map();
let filterVisionAPI = '';
let filterStatus = '';

// DOM Elements
const artworkTableBody = document.getElementById('artworkTableBody');
const searchInput = document.getElementById('searchInput');
const searchBtn = document.getElementById('searchBtn');
const clearBtn = document.getElementById('clearBtn');
const prevBtn = document.getElementById('prevBtn');
const nextBtn = document.getElementById('nextBtn');
const pageInfo = document.getElementById('pageInfo');
const totalCount = document.getElementById('totalCount');


// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadVisionStatus();
    loadArtworks();
    setupEventListeners();
});

function setupEventListeners() {
    searchBtn.addEventListener('click', handleSearch);
    clearBtn.addEventListener('click', handleClear);
    prevBtn.addEventListener('click', () => changePage(-1));
    nextBtn.addEventListener('click', () => changePage(1));
    
    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') handleSearch();
    });
    
    document.getElementById('filterVisionAPI').addEventListener('change', (e) => {
        filterVisionAPI = e.target.value;
        currentPage = 1;
        loadArtworks(1);
    });
    
    document.getElementById('filterTestColumn').addEventListener('change', (e) => {
        filterStatus = e.target.value;
        currentPage = 1;
        loadArtworks(1);
    });
}

async function loadVisionStatus() {
    try {
        const response = await fetch(`${API_BASE}/vision/artwork-status`);
        if (response.ok) {
            const data = await response.json();
            // Convert array to Map for quick lookup
            visionStatusMap = new Map(data.map(item => [item.artwork_id, item]));
        }
        
        // Load and display Vision API stats
        const statsResponse = await fetch(`${API_BASE}/vision/stats`);
        if (statsResponse.ok) {
            const stats = await statsResponse.json();
            const visionStatsEl = document.getElementById('visionStats');
            if (visionStatsEl) {
                visionStatsEl.textContent = `Vision API: ${stats.total_units} units used (${stats.unique_artworks} artworks searched, ${stats.interesting_count} interesting)`;
            }
        }
    } catch (error) {
        console.error('Failed to load Vision API status:', error);
    }
}

async function loadArtworks(page = 1) {
    showLoading();
    
    try {
        const url = currentQuery
            ? `${API_BASE}/artworks/search/query?q=${encodeURIComponent(currentQuery)}&page=${page}&page_size=${pageSize}`
            : `${API_BASE}/artworks?page=${page}&page_size=${pageSize}`;
        
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        
        // Apply client-side filtering
        let filteredItems = data.items;
        
        // Filter by Vision API status
        if (filterVisionAPI === 'searched') {
            filteredItems = filteredItems.filter(artwork => {
                const status = visionStatusMap.get(artwork.id);
                return status && status.has_searches;
            });
        } else if (filterVisionAPI === 'interesting') {
            filteredItems = filteredItems.filter(artwork => {
                const status = visionStatusMap.get(artwork.id);
                return status && status.has_interesting_results;
            });
        } else if (filterVisionAPI === 'not-searched') {
            filteredItems = filteredItems.filter(artwork => {
                const status = visionStatusMap.get(artwork.id);
                return !status || !status.has_searches;
            });
        }
        
        // Filter by status
        if (filterStatus) {
            filteredItems = filteredItems.filter(artwork => {
                return artwork.status === filterStatus;
            });
        }
        
        displayArtworks(filteredItems);
        updatePagination(data);
        updateStats(data);
        
    } catch (error) {
        const isFile = typeof window !== 'undefined' && window.location?.protocol === 'file:';
        const looksLikeNetwork = /fetch|network|connection|refused/i.test(String(error.message));
        const hint = isFile
            ? ' Open this app from the server (e.g. http://localhost:8000/), not as a file.'
            : looksLikeNetwork
                ? ' Make sure the server is running: python -m uvicorn src.main:app --host 0.0.0.0 --port 8000, then open http://localhost:8000/'
                : '';
        showError(`Failed to load artworks: ${error.message}.${hint}`);
    }
}

function displayArtworks(artworks) {
    if (artworks.length === 0) {
        artworkTableBody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #999;">No artworks found</td></tr>';
        return;
    }
    
    artworkTableBody.innerHTML = artworks.map(artwork => {
        const statusClass = artwork.status.toLowerCase().replace('_', '-');
        const artistInfo = artwork.artist 
            ? `${escapeHtml(artwork.artist.name)}${artwork.artist.nationality ? ` (${escapeHtml(artwork.artist.nationality)})` : ''}`
            : 'Unknown';
        
        // Get Vision API status for this artwork
        const visionStatus = visionStatusMap.get(artwork.id) || { has_searches: false, has_interesting_results: false };
        let visionIcons = '';
        if (visionStatus.has_interesting_results) {
            visionIcons = '🔥';
        } else if (visionStatus.has_searches) {
            visionIcons = '✓';
        }
        
        return `
            <tr class="clickable-row" onclick="window.location.href='/static/detail.html?id=${artwork.id}'">
                <td>
                    ${artwork.image_hash 
                        ? `<img src="${API_BASE}/artworks/${artwork.id}/image" 
                                alt="${escapeHtml(artwork.title)}" 
                                class="table-thumbnail"
                                onerror="this.outerHTML='<div class=\\'no-image-placeholder\\'>No Image</div>'">`
                        : `<div class="no-image-placeholder">No Image</div>`
                    }
                </td>
                <td class="artwork-title-cell">${escapeHtml(artwork.title)}</td>
                <td class="vision-status-cell" style="text-align: center;">${visionIcons}</td>
                <td class="artwork-artist-cell">${artistInfo}</td>
                <td class="artwork-year-cell">${artwork.creation_year || '—'}</td>
                <td>
                    <span class="artwork-status ${statusClass}">${escapeHtml(artwork.status).replace(/_/g, ' ')}</span>
                </td>
                <td class="artwork-location-cell">${artwork.last_known_location ? escapeHtml(artwork.last_known_location) : '—'}</td>
                <td class="artwork-description-cell">${artwork.description ? escapeHtml(artwork.description).substring(0, 150) + '...' : '—'}</td>
            </tr>
        `;
    }).join('');
}

function updatePagination(data) {
    currentPage = data.page;
    pageInfo.textContent = `Page ${data.page} of ${data.total_pages}`;
    
    prevBtn.disabled = data.page <= 1;
    nextBtn.disabled = data.page >= data.total_pages;
}

function updateStats(data) {
    const searchText = currentQuery ? ` matching "${currentQuery}"` : '';
    totalCount.textContent = `${data.total} artwork${data.total !== 1 ? 's' : ''} found${searchText}`;
}

function changePage(delta) {
    loadArtworks(currentPage + delta);
}

function handleSearch() {
    currentQuery = searchInput.value.trim();
    currentPage = 1;
    loadArtworks(1);
}

function handleClear() {
    searchInput.value = '';
    currentQuery = '';
    currentPage = 1;
    loadArtworks(1);
}

function showLoading() {
    artworkTableBody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 40px; color: #666;">Loading artworks...</td></tr>';
}

function showError(message) {
    artworkTableBody.innerHTML = `<tr><td colspan="8" style="text-align: center; padding: 40px; color: var(--secondary);">${escapeHtml(message)}</td></tr>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
