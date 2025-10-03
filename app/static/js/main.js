/**
 * Diamond Painting Organizer - Main JavaScript
 * Handles all frontend interactions with Flask backend
 */

// ===== Global State =====
let currentFilter = 'alle';
let deleteStoneId = null;
let allStones = [];
let currentSort = { column: null, direction: 'asc' };

// ===== API Configuration =====
const API_BASE = '';  // Same origin

// ===== DOM Elements =====
const elements = {
    // Forms
    addStoneForm: document.getElementById('add-stone-form'),
    dmcNumber: document.getElementById('dmc-number'),
    colorName: document.getElementById('color-name'),
    quantity: document.getElementById('quantity'),
    pieces: document.getElementById('pieces'),
    location: document.getElementById('location'),
    formMessage: document.getElementById('form-message'),
    quantityButtons: document.querySelectorAll('.quantity-btn'),
    colorPreview: document.getElementById('color-preview'),
    diamondPreview: document.querySelector('.diamond-preview'),
    previewText: document.querySelector('.preview-text'),

    // Search
    searchInput: document.getElementById('search-input'),
    searchBtn: document.getElementById('search-btn'),
    clearSearchBtn: document.getElementById('clear-search-btn'),
    searchResults: document.getElementById('search-results'),

    // Table
    stonesTbody: document.getElementById('stones-tbody'),
    stonesTable: document.getElementById('stones-table'),
    emptyState: document.getElementById('empty-state'),
    filterButtons: document.querySelectorAll('.filter-btn'),

    // Modal
    deleteModal: document.getElementById('delete-modal'),
    confirmDeleteBtn: document.getElementById('confirm-delete-btn'),
    cancelDeleteBtn: document.getElementById('cancel-delete-btn'),
    modalStoneDetails: document.getElementById('modal-stone-details'),

    // Backup/Restore
    exportBtn: document.getElementById('export-btn'),
    importFile: document.getElementById('import-file'),
    backupMessage: document.getElementById('backup-message')
};

// ===== Initialize App =====
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    createSparkles();
});

function initializeApp() {
    // Load all stones
    loadStones();

    // Event Listeners - Form
    elements.addStoneForm.addEventListener('submit', handleAddStone);

    // Event Listeners - Quantity Buttons
    elements.quantityButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Toggle: if already active, deactivate it
            if (btn.classList.contains('active')) {
                btn.classList.remove('active');
                elements.quantity.value = '';
                elements.pieces.disabled = false;
            } else {
                // Remove active from all buttons
                elements.quantityButtons.forEach(b => b.classList.remove('active'));
                // Add active to clicked button
                btn.classList.add('active');
                // Set hidden input value
                elements.quantity.value = btn.dataset.value;
                // Disable pieces input when button is active
                elements.pieces.value = '';
                elements.pieces.disabled = true;
            }
        });
    });

    // Event Listeners - Pieces input
    elements.pieces.addEventListener('input', () => {
        if (elements.pieces.value) {
            // If pieces has value, deactivate all quantity buttons
            elements.quantityButtons.forEach(btn => btn.classList.remove('active'));
            elements.quantity.value = '';
        }
    });

    // Event Listeners - Backup/Restore
    if (elements.exportBtn) {
        elements.exportBtn.addEventListener('click', handleExportBackup);
    }
    if (elements.importFile) {
        elements.importFile.addEventListener('change', handleImportBackup);
    }

    // Event Listeners - Search
    elements.searchBtn.addEventListener('click', handleSearch);
    elements.clearSearchBtn.addEventListener('click', handleClearSearch);
    elements.searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSearch();
        }
    });

    // Auto-fill color name and show preview when DMC number is entered
    elements.dmcNumber.addEventListener('input', async (e) => {
        e.target.value = e.target.value.replace(/[^0-9]/g, '');

        const dmcNumber = e.target.value;
        if (dmcNumber.length >= 2) {
            await autoFillColorName(dmcNumber);
        } else {
            elements.colorName.value = '';
            elements.colorName.placeholder = 'Optional';
            resetColorPreview();
        }
    });

    // Event Listeners - Filters
    elements.filterButtons.forEach(btn => {
        btn.addEventListener('click', () => handleFilter(btn));
    });

    // Event Listeners - Modal
    elements.cancelDeleteBtn.addEventListener('click', closeDeleteModal);
    elements.confirmDeleteBtn.addEventListener('click', confirmDelete);

    // Close modal on outside click
    elements.deleteModal.addEventListener('click', (e) => {
        if (e.target === elements.deleteModal) {
            closeDeleteModal();
        }
    });
}

// ===== API Functions =====

/**
 * Fetch all stones from backend
 */
async function loadStones() {
    try {
        showLoading(true);

        const response = await fetch(`${API_BASE}/api/stones`);

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        allStones = data.data || [];

        displayStones(allStones);

    } catch (error) {
        console.error('Error loading stones:', error);
        showError('Fehler beim Laden der Steinchen. Bitte Seite neu laden.');
        showLoading(false);
    }
}

/**
 * Add new stone via API
 */
async function handleAddStone(e) {
    e.preventDefault();

    // Validate form
    if (!elements.dmcNumber.value) {
        showMessage('Bitte DMC-Nummer eingeben!', 'error');
        return;
    }

    // Check if either quantity OR pieces is filled
    if (!elements.quantity.value && !elements.pieces.value) {
        showMessage('Bitte wähle Menge (Viele/Wenige) ODER gib Stückzahl ein!', 'error');
        return;
    }

    const stoneData = {
        dmc_number: elements.dmcNumber.value.trim(),
        color_name: elements.colorName.value.trim() || null,
        quantity: elements.quantity.value,
        pieces: elements.pieces.value ? parseInt(elements.pieces.value) : null,
        location: elements.location.value.trim() || null
    };

    try {
        const response = await fetch(`${API_BASE}/api/stones`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(stoneData)
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('✨ Steinchen erfolgreich hinzugefügt!', 'success');
            elements.addStoneForm.reset();
            // Reset quantity buttons
            elements.quantityButtons.forEach(btn => btn.classList.remove('active'));
            loadStones();  // Reload to show new stone
        } else {
            showMessage(data.error || 'Fehler beim Hinzufügen', 'error');
        }

    } catch (error) {
        console.error('Error adding stone:', error);
        showMessage('Netzwerkfehler. Bitte erneut versuchen.', 'error');
    }
}

/**
 * Search for stone by DMC number
 */
async function handleSearch() {
    const searchQuery = elements.searchInput.value.trim().toLowerCase();
    const searchMessage = document.getElementById('search-message');

    if (!searchQuery) {
        searchMessage.textContent = '⚠️ Bitte Suchbegriff eingeben';
        searchMessage.className = 'message error';
        searchMessage.classList.remove('hidden');
        setTimeout(() => searchMessage.classList.add('hidden'), 3000);
        return;
    }

    // Hide previous messages
    searchMessage.classList.add('hidden');

    try {
        // Search in local data for both DMC number and color name
        const matchingStones = allStones.filter(stone => {
            const dmcMatch = stone.dmc_number.toLowerCase().includes(searchQuery);
            const colorMatch = stone.color_name && stone.color_name.toLowerCase().includes(searchQuery);
            return dmcMatch || colorMatch;
        });

        if (matchingStones.length > 0) {
            displaySearchResults(matchingStones);
        } else {
            elements.searchResults.innerHTML = `
                <p style="color: var(--warning);">
                    💫 Keine Steinchen mit "${searchQuery}" gefunden
                </p>
            `;
            elements.searchResults.classList.remove('hidden');
        }

    } catch (error) {
        console.error('Error searching:', error);
        searchMessage.textContent = '⚠️ Suchfehler. Bitte erneut versuchen.';
        searchMessage.className = 'message error';
        searchMessage.classList.remove('hidden');
    }
}

/**
 * Clear search results
 */
function handleClearSearch() {
    elements.searchInput.value = '';
    elements.searchResults.classList.add('hidden');
    elements.searchResults.innerHTML = '';
}

/**
 * Handle filter button clicks
 */
function handleFilter(clickedBtn) {
    // Update active state
    elements.filterButtons.forEach(btn => btn.classList.remove('active'));
    clickedBtn.classList.add('active');

    // Get filter value
    currentFilter = clickedBtn.dataset.filter;

    // Filter stones
    const filteredStones = filterStones(allStones, currentFilter);
    displayStones(filteredStones);
}

/**
 * Delete stone with confirmation
 */
function openDeleteModal(stone) {
    deleteStoneId = stone.id;

    elements.modalStoneDetails.innerHTML = `
        <p><strong>DMC:</strong> ${stone.dmc_number}</p>
        ${stone.color_name ? `<p><strong>Farbe:</strong> ${stone.color_name}</p>` : ''}
        <p><strong>Menge:</strong> ${stone.quantity}</p>
    `;

    elements.deleteModal.classList.remove('hidden');
}

function closeDeleteModal() {
    elements.deleteModal.classList.add('hidden');
    deleteStoneId = null;
}

async function confirmDelete() {
    if (!deleteStoneId) return;

    try {
        const response = await fetch(`${API_BASE}/api/stones/${deleteStoneId}`, {
            method: 'DELETE'
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('🗑️ Steinchen gelöscht', 'success');
            closeDeleteModal();
            loadStones();  // Reload table
        } else {
            showMessage(data.error || 'Fehler beim Löschen', 'error');
        }

    } catch (error) {
        console.error('Error deleting stone:', error);
        showMessage('Netzwerkfehler beim Löschen', 'error');
    }
}

// ===== Display Functions =====

/**
 * Display stones in table
 */
async function displayStones(stones) {
    showLoading(false);

    if (stones.length === 0) {
        elements.stonesTable.style.display = 'none';
        elements.emptyState.classList.remove('hidden');
        return;
    }

    elements.stonesTable.style.display = 'table';
    elements.emptyState.classList.add('hidden');

    // Pre-fetch all colors
    const colorPromises = stones.map(stone =>
        fetch(`${API_BASE}/api/dmc/${stone.dmc_number}`)
            .then(res => res.json())
            .then(data => ({
                dmc: stone.dmc_number,
                hex: data.success && data.hex_code ? data.hex_code : '#cccccc'
            }))
            .catch(() => ({ dmc: stone.dmc_number, hex: '#cccccc' }))
    );

    const colors = await Promise.all(colorPromises);
    const colorMap = {};
    colors.forEach(c => {
        colorMap[c.dmc] = c.hex;
        colorCache[c.dmc] = c.hex;
    });

    elements.stonesTbody.innerHTML = stones.map(stone => {
        const colorHex = colorMap[stone.dmc_number] || '#cccccc';
        return `
        <tr>
            <td>
                <div class="color-preview" style="background-color: ${colorHex};" title="${stone.color_name || 'DMC ' + stone.dmc_number}"></div>
            </td>
            <td><strong>${stone.dmc_number}</strong></td>
            <td>${stone.color_name || '-'}</td>
            <td>
                ${stone.quantity ?
                    `<span class="quantity-badge quantity-${stone.quantity}">
                        ${stone.quantity === 'viele' ? '🌟 Viele' : '💫 Wenige'}
                    </span>`
                    : '-'}
            </td>
            <td>${stone.pieces || '-'}</td>
            <td>${stone.location === 'None' ? '-' : (stone.location || '-')}</td>
            <td>
                <button
                    class="btn-delete"
                    onclick="openDeleteModal(${JSON.stringify(stone).replace(/"/g, '&quot;')})"
                    aria-label="Steinchen löschen"
                >
                    🗑️ Löschen
                </button>
            </td>
        </tr>
    `}).join('');
}

/**
 * Display search results
 */
function displaySearchResults(stones) {
    if (!stones || stones.length === 0) {
        elements.searchResults.innerHTML = `
            <p style="color: var(--warning);">
                💫 Keine Steinchen gefunden
            </p>
        `;
        elements.searchResults.classList.remove('hidden');
        return;
    }

    const resultsHTML = stones.map(stone => {
        return `
            <div style="padding: 1rem; border: 2px solid var(--primary); border-radius: var(--radius-md); margin-bottom: 1rem; background: rgba(139, 92, 246, 0.05);">
                <div style="display: flex; align-items: center; justify-content: space-between; gap: 1rem;">
                    <div style="flex: 1;">
                        <strong style="font-size: 1.2rem;">DMC ${stone.dmc_number}</strong>
                        <p style="margin: 0.5rem 0; color: var(--text);">${stone.color_name || '-'}</p>
                        <p style="margin: 0.5rem 0;">
                            ${stone.quantity ?
                                (stone.quantity === 'viele' ? '🌟 Viele' : '💫 Wenige') :
                                `📦 ${stone.pieces} Stück`
                            }
                        </p>
                        ${stone.location && stone.location !== 'None' ? `<p style="margin: 0.5rem 0;">📍 ${stone.location}</p>` : ''}
                    </div>
                    <button
                        class="btn-delete"
                        onclick="openDeleteModal(${JSON.stringify(stone).replace(/"/g, '&quot;')})"
                        style="align-self: flex-start;"
                    >
                        🗑️ Löschen
                    </button>
                </div>
            </div>
        `;
    }).join('');

    elements.searchResults.innerHTML = `
        <h3 style="margin-bottom: 1rem;">Gefunden! ✨ (${stones.length})</h3>
        ${resultsHTML}
    `;
    elements.searchResults.classList.remove('hidden');
}

/**
 * Display search result (legacy - single stone)
 */
function displaySearchResult(stone) {
    displaySearchResults([stone]);
}

/**
 * Display search result (old version for reference)
 */
function displaySearchResult_old(stone) {
    elements.searchResults.innerHTML = `
        <h3 style="margin-bottom: 1rem;">Gefunden! ✨</h3>
        <div style="display: grid; gap: 0.5rem;">
            <p><strong>DMC Nummer:</strong> ${stone.dmc_number}</p>
            <p><strong>Farbname:</strong> ${stone.color_name || '-'}</p>
            <p><strong>Menge:</strong>
                <span class="quantity-badge quantity-${stone.quantity}">
                    ${stone.quantity === 'viele' ? '🌟 Viele' : '💫 Wenige'}
                </span>
            </p>
            <p><strong>Ort:</strong> ${stone.location || '-'}</p>
        </div>
    `;
    elements.searchResults.classList.remove('hidden');
}

/**
 * Show loading spinner
 */
function showLoading(isLoading) {
    if (isLoading) {
        elements.stonesTbody.innerHTML = `
            <tr class="loading-row">
                <td colspan="5">
                    <div class="loading-spinner"></div>
                    <p>Lade Steinchen...</p>
                </td>
            </tr>
        `;
    }
}

/**
 * Show form message
 */
function showMessage(message, type = 'success') {
    elements.formMessage.textContent = message;
    elements.formMessage.className = `message ${type}`;
    elements.formMessage.classList.remove('hidden');

    // Auto-hide after 5 seconds
    setTimeout(() => {
        elements.formMessage.classList.add('hidden');
    }, 5000);
}

/**
 * Show error in stones table
 */
function showError(message) {
    elements.stonesTbody.innerHTML = `
        <tr>
            <td colspan="5" style="text-align: center; color: var(--error); padding: 2rem;">
                ⚠️ ${message}
            </td>
        </tr>
    `;
}

// ===== Utility Functions =====

/**
 * Auto-fill color name and show color preview when DMC number is entered
 */
async function autoFillColorName(dmcNumber) {
    try {
        const response = await fetch(`${API_BASE}/api/dmc/${dmcNumber}`);

        if (!response.ok) {
            console.error('Error fetching DMC color');
            return;
        }

        const data = await response.json();

        if (data.success && data.color_name) {
            // Fill color name
            elements.colorName.value = data.color_name;
            elements.colorName.placeholder = data.color_name;

            // Add visual feedback
            elements.colorName.style.borderColor = '#10B981';
            setTimeout(() => {
                elements.colorName.style.borderColor = '';
            }, 1000);

            // Update color preview
            if (data.hex_code) {
                elements.diamondPreview.style.color = data.hex_code;
                elements.diamondPreview.classList.add('colored');
                elements.previewText.textContent = `${data.color_name} (${data.hex_code})`;
                elements.previewText.style.color = data.hex_code;
            }
        } else {
            elements.colorName.value = '';
            elements.colorName.placeholder = 'Nicht gefunden - kann manuell eingegeben werden';
            resetColorPreview();
        }

    } catch (error) {
        console.error('Error in autoFillColorName:', error);
        elements.colorName.placeholder = 'Optional';
        resetColorPreview();
    }
}

/**
 * Reset color preview to default state
 */
function resetColorPreview() {
    if (elements.diamondPreview) {
        elements.diamondPreview.style.color = '';
        elements.diamondPreview.classList.remove('colored');
    }
    if (elements.previewText) {
        elements.previewText.textContent = 'Gib DMC-Nummer ein';
        elements.previewText.style.color = '';
    }
}

/**
 * Get color hex code for DMC number from cache or API
 */
const colorCache = {};

function getColorHexForDMC(dmcNumber) {
    // Return cached color if available
    if (colorCache[dmcNumber]) {
        return colorCache[dmcNumber];
    }

    // Fetch color asynchronously and update
    fetch(`${API_BASE}/api/dmc/${dmcNumber}`)
        .then(res => res.json())
        .then(data => {
            if (data.success && data.hex_code) {
                colorCache[dmcNumber] = data.hex_code;
                // Update all table cells with this DMC number
                document.querySelectorAll(`tr[data-dmc="${dmcNumber}"] .color-cell`).forEach(cell => {
                    cell.style.backgroundColor = data.hex_code;
                });
            }
        })
        .catch(err => console.error('Error fetching color:', err));

    // Return default color while loading
    return '#E5E7EB';
}

/**
 * Filter stones by quantity
 */
function filterStones(stones, filter) {
    if (filter === 'alle') {
        return stones;
    }
    return stones.filter(stone => stone.quantity === filter);
}

/**
 * Create animated sparkles
 */
function createSparkles() {
    const sparklesContainer = document.getElementById('sparkles');
    const sparkleCount = 20;

    for (let i = 0; i < sparkleCount; i++) {
        const sparkle = document.createElement('div');
        sparkle.style.position = 'absolute';
        sparkle.style.width = '4px';
        sparkle.style.height = '4px';
        sparkle.style.background = 'white';
        sparkle.style.borderRadius = '50%';
        sparkle.style.boxShadow = '0 0 10px rgba(255, 255, 255, 0.8)';
        sparkle.style.left = Math.random() * 100 + '%';
        sparkle.style.top = Math.random() * 100 + '%';
        sparkle.style.animation = `sparkle ${2 + Math.random() * 3}s ease-in-out infinite`;
        sparkle.style.animationDelay = Math.random() * 2 + 's';
        sparkle.style.opacity = '0';

        sparklesContainer.appendChild(sparkle);
    }

    // Add sparkle animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes sparkle {
            0%, 100% {
                opacity: 0;
                transform: scale(0) rotate(0deg);
            }
            50% {
                opacity: 1;
                transform: scale(1.5) rotate(180deg);
            }
        }
    `;
    document.head.appendChild(style);
}

/**
 * Sort stones by column
 */
function sortStones(stones, column, direction) {
    const sorted = [...stones];

    sorted.sort((a, b) => {
        let aVal = a[column];
        let bVal = b[column];

        // Handle null/undefined values
        if (aVal === null || aVal === undefined || aVal === '' || aVal === 'None') aVal = '';
        if (bVal === null || bVal === undefined || bVal === '' || bVal === 'None') bVal = '';

        // Convert to numbers for numeric columns
        if (column === 'dmc_number' || column === 'pieces') {
            aVal = parseInt(aVal) || 0;
            bVal = parseInt(bVal) || 0;
        } else {
            // Convert to lowercase for string comparison
            aVal = String(aVal).toLowerCase();
            bVal = String(bVal).toLowerCase();
        }

        if (aVal < bVal) return direction === 'asc' ? -1 : 1;
        if (aVal > bVal) return direction === 'asc' ? 1 : -1;
        return 0;
    });

    return sorted;
}

/**
 * Handle column header click for sorting
 */
async function handleSort(column) {
    // Toggle direction if same column, otherwise default to asc
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }

    // Update sort icons
    document.querySelectorAll('.sortable').forEach(th => {
        const icon = th.querySelector('.sort-icon');
        if (th.dataset.sort === column) {
            icon.textContent = currentSort.direction === 'asc' ? '↑' : '↓';
            th.classList.add('sorted');
        } else {
            icon.textContent = '⇅';
            th.classList.remove('sorted');
        }
    });

    // Sort and display
    const sorted = sortStones(allStones, column, currentSort.direction);
    await displayStones(sorted);
}

// ===== Backup & Restore Functions =====
async function handleExportBackup() {
    try {
        const response = await fetch(`${API_BASE}/api/backup/export`);

        if (!response.ok) {
            throw new Error('Backup export failed');
        }

        // Create blob and download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `diamond_painting_backup_${new Date().toISOString().slice(0,10)}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        showBackupMessage('✓ Backup erfolgreich heruntergeladen', 'success');
    } catch (error) {
        console.error('Export error:', error);
        showBackupMessage('✗ Fehler beim Backup-Download', 'error');
    }
}

async function handleImportBackup(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Show confirmation dialog
    if (!confirm(`Achtung: Alle aktuellen Daten werden durch das Backup ersetzt!\n\nBackup: ${file.name}\nFortfahren?`)) {
        event.target.value = ''; // Reset file input
        return;
    }

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/backup/import`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Import failed');
        }

        showBackupMessage(`✓ ${result.count} Steinchen erfolgreich wiederhergestellt`, 'success');

        // Reload stones after import
        setTimeout(() => {
            loadStones();
        }, 1500);

    } catch (error) {
        console.error('Import error:', error);
        showBackupMessage(`✗ Fehler beim Import: ${error.message}`, 'error');
    }

    // Reset file input
    event.target.value = '';
}

function showBackupMessage(message, type) {
    const messageEl = elements.backupMessage;
    messageEl.textContent = message;
    messageEl.className = `message ${type}`;
    messageEl.classList.remove('hidden');

    setTimeout(() => {
        messageEl.classList.add('hidden');
    }, 5000);
}

// ===== Export for global access =====
window.openDeleteModal = openDeleteModal;
window.closeDeleteModal = closeDeleteModal;
window.handleSort = handleSort;
