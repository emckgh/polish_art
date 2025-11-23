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
const modal = document.getElementById('detailModal');
const modalBody = document.getElementById('modalBody');
const closeBtn = document.querySelector('.close');

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
    
    closeBtn.addEventListener('click', closeModal);
    
    window.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
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
            <tr>
                <td>
                    ${artwork.image_hash 
                        ? `<img src="${API_BASE}/artworks/${artwork.id}/image" 
                                alt="${escapeHtml(artwork.title)}" 
                                class="table-thumbnail" 
                                onclick="showDetail('${artwork.id}')"
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

async function showDetail(artworkId) {
    try {
        const response = await fetch(`${API_BASE}/artworks/${artworkId}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const artwork = await response.json();
        
        modalBody.innerHTML = `
            ${artwork.image_hash 
                ? `<img src="${API_BASE}/artworks/${artwork.id}/image" alt="${escapeHtml(artwork.title)}" class="modal-image" onerror="this.style.display='none'">`
                : '<div style="text-align: center; padding: 40px; background: #f0f0f0; color: #999; border-radius: 8px; margin-bottom: 20px;">No image available</div>'
            }
            <h2 class="modal-title">${escapeHtml(artwork.title)}</h2>
            
            ${artwork.artist ? `
                <div class="modal-detail">
                    <span class="modal-label">Artist:</span> ${escapeHtml(artwork.artist.name)}
                    ${artwork.artist.birth_year || artwork.artist.death_year 
                        ? ` (${artwork.artist.birth_year || '?'} - ${artwork.artist.death_year || '?'})` 
                        : ''
                    }
                    ${artwork.artist.nationality ? ` - ${escapeHtml(artwork.artist.nationality)}` : ''}
                </div>
            ` : ''}
            
            ${artwork.creation_year ? `
                <div class="modal-detail">
                    <span class="modal-label">Year Created:</span> ${artwork.creation_year}
                </div>
            ` : ''}
            
            ${artwork.description ? `
                <div class="modal-detail">
                    <span class="modal-label">Description:</span><br>
                    ${escapeHtml(artwork.description)}
                </div>
            ` : ''}
            
            <div class="modal-detail">
                <span class="modal-label">Status:</span> 
                <span class="artwork-status">${escapeHtml(artwork.status)}</span>
            </div>
            
            ${artwork.last_known_location ? `
                <div class="modal-detail">
                    <span class="modal-label">Last Known Location:</span> ${escapeHtml(artwork.last_known_location)}
                </div>
            ` : ''}
            
            ${artwork.last_known_date ? `
                <div class="modal-detail">
                    <span class="modal-label">Last Known Date:</span> ${new Date(artwork.last_known_date).toLocaleDateString()}
                </div>
            ` : ''}
            
            ${artwork.image_hash ? `
                <div class="modal-detail">
                    <span class="modal-label">Image Hash:</span> <code style="font-size: 0.85em; word-break: break-all;">${escapeHtml(artwork.image_hash)}</code>
                </div>
            ` : ''}
            
            <div class="modal-detail">
                <span class="modal-label">Artwork ID:</span> <code style="font-size: 0.85em;">${escapeHtml(artwork.id)}</code>
            </div>
            
            <div class="modal-detail">
                <span class="modal-label">Added to Database:</span> ${new Date(artwork.created_at).toLocaleString()}
            </div>
            
            <div class="modal-detail">
                <span class="modal-label">Last Updated:</span> ${new Date(artwork.updated_at).toLocaleString()}
            </div>
        `;
        
        modal.style.display = 'block';
        
    } catch (error) {
        alert(`Failed to load artwork details: ${error.message}`);
    }
}

function closeModal() {
    modal.style.display = 'none';
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
