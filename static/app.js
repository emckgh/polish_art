// Polish Looted Art Database - Frontend JavaScript

const API_BASE = '/api';
let currentPage = 1;
let currentQuery = '';
const pageSize = 10;

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
        
        displayArtworks(data.items);
        updatePagination(data);
        updateStats(data);
        
    } catch (error) {
        showError(`Failed to load artworks: ${error.message}`);
    }
}

function displayArtworks(artworks) {
    if (artworks.length === 0) {
        artworkTableBody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px; color: #999;">No artworks found</td></tr>';
        return;
    }
    
    artworkTableBody.innerHTML = artworks.map(artwork => {
        const statusClass = artwork.status.toLowerCase().replace('_', '-');
        const artistInfo = artwork.artist 
            ? `${escapeHtml(artwork.artist.name)}${artwork.artist.nationality ? ` (${escapeHtml(artwork.artist.nationality)})` : ''}`
            : 'Unknown';
        
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
    artworkTableBody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 40px; color: #666;">Loading artworks...</td></tr>';
}

function showError(message) {
    artworkTableBody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 40px; color: var(--secondary);">${escapeHtml(message)}</td></tr>`;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
