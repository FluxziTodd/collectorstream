// Global State
let currentUser = null;
let allCards = [];
let filteredCards = [];
let currentView = 'performance';
let currentGroupBy = 'sport';
let currentSort = 'profitPercent';
let currentSearchQuery = '';
let currentPage = 1;
const itemsPerPage = 50;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
});

// Auth Functions
function checkAuth() {
    const token = localStorage.getItem('token');
    const email = localStorage.getItem('email');

    if (token && email) {
        currentUser = { token, email };
        updateAuthUI();
    }
}

function updateAuthUI() {
    if (currentUser) {
        document.getElementById('authButtons').style.display = 'none';
        document.getElementById('profileDropdown').style.display = 'block';
        document.getElementById('profileEmail').textContent = currentUser.email;
        document.getElementById('profileAvatar').textContent = currentUser.email.charAt(0).toUpperCase();

        if (currentUser.email === 'todd@fluxzi.com') {
            document.getElementById('adminMenuSection').style.display = 'block';
        }
    } else {
        document.getElementById('authButtons').style.display = 'flex';
        document.getElementById('profileDropdown').style.display = 'none';
    }
}

function toggleProfileMenu() {
    document.getElementById('profileMenu').classList.toggle('active');
}

function openLoginModal() {
    document.getElementById('loginModal').classList.add('active');
}

function closeLoginModal() {
    document.getElementById('loginModal').classList.remove('active');
    document.getElementById('loginForm').reset();
    document.getElementById('loginError').style.display = 'none';
}

function openSignupModal() {
    document.getElementById('signupModal').classList.add('active');
}

function closeSignupModal() {
    document.getElementById('signupModal').classList.remove('active');
    document.getElementById('signupForm').reset();
    document.getElementById('signupError').style.display = 'none';
}

async function handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    const errorEl = document.getElementById('loginError');

    errorEl.style.display = 'none';

    try {
        const response = await fetch('https://api.collectorstream.com/v1/auth/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Login failed');
        }

        localStorage.setItem('token', data.token);
        localStorage.setItem('email', email);
        currentUser = { token: data.token, email };

        closeLoginModal();
        updateAuthUI();
        // Stay on home page after login
        showHome();
    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
    }
}

async function handleSignup(e) {
    e.preventDefault();
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    const errorEl = document.getElementById('signupError');

    errorEl.style.display = 'none';

    try {
        const response = await fetch('https://api.collectorstream.com/v1/auth/signup', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Signup failed');
        }

        localStorage.setItem('token', data.token);
        localStorage.setItem('email', email);
        currentUser = { token: data.token, email };

        closeSignupModal();
        updateAuthUI();
        // Stay on home page after signup
        showHome();
    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
    }
}

function logout() {
    localStorage.removeItem('token');
    localStorage.removeItem('email');
    currentUser = null;
    updateAuthUI();
    showHome();
}

// Page Navigation
function showHome() {
    // Hide portfolio and admin
    document.getElementById('portfolioContent').classList.remove('active');
    document.getElementById('adminContent').classList.remove('active');
    
    // Show main content
    document.getElementById('mainContent').classList.remove('hidden');
    
    // Close profile menu
    document.getElementById('profileMenu').classList.remove('active');
}

function showPortfolio() {
    if (!currentUser) {
        openLoginModal();
        return;
    }

    // Hide main content and admin
    document.getElementById('mainContent').classList.add('hidden');
    document.getElementById('adminContent').classList.remove('active');
    
    // Show portfolio
    document.getElementById('portfolioContent').classList.add('active');
    
    // Close profile menu
    document.getElementById('profileMenu').classList.remove('active');
    
    loadPortfolio();
}

function showAdminDashboard() {
    if (!currentUser || currentUser.email !== 'todd@fluxzi.com') {
        alert('Admin access denied');
        return;
    }

    // Hide main content and portfolio
    document.getElementById('mainContent').classList.add('hidden');
    document.getElementById('portfolioContent').classList.remove('active');
    
    // Show admin
    document.getElementById('adminContent').classList.add('active');
    
    // Close profile menu
    document.getElementById('profileMenu').classList.remove('active');
    
    loadAdminDashboard();
}

// Portfolio Functions
async function loadPortfolio() {
    try {
        const response = await fetch('https://api.collectorstream.com/v1/cards', {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Failed to load portfolio');
        }

        allCards = data.cards || [];
        filteredCards = [...allCards];
        renderDashboard();
    } catch (error) {
        console.error('Error loading portfolio:', error);
        showEmptyState('Error loading portfolio: ' + error.message);
    }
}

function renderDashboard() {
    calculateAndRenderStats();
    applyFiltersAndSort();
    renderCurrentView();
}

function calculateAndRenderStats() {
    let totalValue = 0;
    let totalInvested = 0;
    let topPerformer = null;
    let biggestLoser = null;
    let maxGainPercent = -Infinity;
    let maxLossPercent = Infinity;

    allCards.forEach(card => {
        const currentValue = parseFloat(card.currentValue || 0);
        const purchasePrice = parseFloat(card.purchasePrice || 0);
        const profit = currentValue - purchasePrice;
        const profitPercent = purchasePrice > 0 ? (profit / purchasePrice) * 100 : 0;

        totalValue += currentValue;
        totalInvested += purchasePrice;

        if (profitPercent > maxGainPercent) {
            maxGainPercent = profitPercent;
            topPerformer = { ...card, profitPercent, profit };
        }

        if (profitPercent < maxLossPercent) {
            maxLossPercent = profitPercent;
            biggestLoser = { ...card, profitPercent, profit };
        }
    });

    const totalProfit = totalValue - totalInvested;
    const roi = totalInvested > 0 ? ((totalProfit / totalInvested) * 100).toFixed(2) : 0;

    // Update stats
    document.getElementById('totalValue').textContent = `$${totalValue.toFixed(2)}`;
    document.getElementById('totalInvested').textContent = `$${totalInvested.toFixed(2)}`;

    const profitEl = document.getElementById('totalProfit');
    profitEl.textContent = `${totalProfit >= 0 ? '+' : ''}$${totalProfit.toFixed(2)}`;
    profitEl.className = 'portfolio-stat-value ' + (totalProfit >= 0 ? 'positive' : 'negative');

    const roiEl = document.getElementById('totalROI');
    roiEl.textContent = `${roi >= 0 ? '+' : ''}${roi}%`;
    roiEl.className = 'portfolio-stat-value ' + (roi >= 0 ? 'positive' : 'negative');

    // Render top performer and biggest loser
    renderTopPerformer('topPerformer', topPerformer);
    renderTopPerformer('biggestLoser', biggestLoser);
}

function renderTopPerformer(elementId, card) {
    const el = document.getElementById(elementId);
    if (!card) {
        el.innerHTML = '<div style="font-size: 13px; color: var(--text-muted);">N/A</div>';
        return;
    }

    const isPositive = card.profitPercent >= 0;
    el.innerHTML = `
        <div class="top-performer-card">
            ${card.frontImageUrl ? `<img src="${card.frontImageUrl}" class="top-performer-img" alt="${card.playerName}">` : '<div class="top-performer-img"></div>'}
            <div class="top-performer-info">
                <div class="top-performer-name">${card.playerName || 'Unknown'}</div>
                <div class="top-performer-meta">${card.sport || ''} • ${card.team || ''}</div>
                <div class="top-performer-change ${isPositive ? 'positive' : 'negative'}">
                    ${isPositive ? '+' : ''}${card.profitPercent.toFixed(2)}% ${isPositive ? '↗' : '↘'}
                </div>
            </div>
        </div>
    `;
}

// View Management
function changeView(view) {
    currentView = view;
    document.querySelectorAll('.view-mode-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    document.getElementById('groupByControl').style.display = view === 'grouped' ? 'flex' : 'none';
    document.getElementById('performanceView').classList.toggle('active', view === 'performance');
    document.getElementById('allCardsView').style.display = view === 'all' ? 'block' : 'none';
    document.getElementById('groupedView').classList.toggle('active', view === 'grouped');

    renderCurrentView();
}

function changeGroupBy(groupBy) {
    currentGroupBy = groupBy;
    if (currentView === 'grouped') {
        renderCurrentView();
    }
}

function changeSorting(sortBy) {
    currentSort = sortBy;
    applyFiltersAndSort();
    renderCurrentView();
}

function handleSearch(query) {
    currentSearchQuery = query.toLowerCase().trim();
    applyFiltersAndSort();
    renderCurrentView();

    const resultsInfo = document.getElementById('searchResultsInfo');
    if (currentSearchQuery) {
        resultsInfo.style.display = 'flex';
        document.getElementById('searchResultsText').textContent =
            `Found ${filteredCards.length} result${filteredCards.length !== 1 ? 's' : ''} for "${query}"`;
    } else {
        resultsInfo.style.display = 'none';
    }
}

function clearSearch() {
    document.getElementById('searchInput').value = '';
    currentSearchQuery = '';
    applyFiltersAndSort();
    renderCurrentView();
    document.getElementById('searchResultsInfo').style.display = 'none';
}

function applyFiltersAndSort() {
    // Filter
    filteredCards = allCards.filter(card => {
        if (!currentSearchQuery) return true;

        const searchableText = [
            card.playerName,
            card.team,
            card.sport,
            card.setName,
            card.cardNumber,
            card.year
        ].filter(Boolean).join(' ').toLowerCase();

        return searchableText.includes(currentSearchQuery);
    });

    // Sort
    filteredCards.sort((a, b) => {
        const aValue = parseFloat(a.currentValue || 0);
        const aPrice = parseFloat(a.purchasePrice || 0);
        const aProfit = aValue - aPrice;
        const aProfitPercent = aPrice > 0 ? (aProfit / aPrice) * 100 : 0;

        const bValue = parseFloat(b.currentValue || 0);
        const bPrice = parseFloat(b.purchasePrice || 0);
        const bProfit = bValue - bPrice;
        const bProfitPercent = bPrice > 0 ? (bProfit / bPrice) * 100 : 0;

        switch (currentSort) {
            case 'profitPercent':
                return bProfitPercent - aProfitPercent;
            case 'profitAmount':
                return bProfit - aProfit;
            case 'currentValue':
                return bValue - aValue;
            case 'playerName':
                return (a.playerName || '').localeCompare(b.playerName || '');
            case 'purchaseDate':
                return new Date(b.createdAt || 0) - new Date(a.createdAt || 0);
            default:
                return 0;
        }
    });

    currentPage = 1;
}

function renderCurrentView() {
    switch (currentView) {
        case 'performance':
            renderPerformanceDashboard();
            break;
        case 'all':
            renderAllCardsGrid();
            break;
        case 'grouped':
            renderGroupedView();
            break;
    }
}

// Performance Dashboard
function renderPerformanceDashboard() {
    if (filteredCards.length === 0) {
        document.getElementById('hotCards').innerHTML = getEmptyMessage();
        document.getElementById('decliningCards').innerHTML = getEmptyMessage();
        document.getElementById('sportBreakdown').innerHTML = getEmptyMessage();
        return;
    }

    // Calculate profit percentages
    const cardsWithProfit = filteredCards.map(card => {
        const currentValue = parseFloat(card.currentValue || 0);
        const purchasePrice = parseFloat(card.purchasePrice || 0);
        const profit = currentValue - purchasePrice;
        const profitPercent = purchasePrice > 0 ? (profit / purchasePrice) * 100 : 0;
        return { ...card, profit, profitPercent };
    });

    // Top gainers
    const gainers = [...cardsWithProfit]
        .filter(c => c.profitPercent > 0)
        .sort((a, b) => b.profitPercent - a.profitPercent)
        .slice(0, 5);

    // Top losers
    const losers = [...cardsWithProfit]
        .filter(c => c.profitPercent < 0)
        .sort((a, b) => a.profitPercent - b.profitPercent)
        .slice(0, 5);

    document.getElementById('hotCards').innerHTML = gainers.length > 0
        ? gainers.map(renderCardTile).join('')
        : getEmptyMessage('No gainers yet');

    document.getElementById('decliningCards').innerHTML = losers.length > 0
        ? losers.map(renderCardTile).join('')
        : getEmptyMessage('No decliners yet');

    renderSportBreakdown(cardsWithProfit);
}

function renderSportBreakdown(cards) {
    const sportGroups = groupCards(cards, 'sport');
    const el = document.getElementById('sportBreakdown');

    if (Object.keys(sportGroups).length === 0) {
        el.innerHTML = getEmptyMessage();
        return;
    }

    el.innerHTML = Object.entries(sportGroups).map(([sport, sportCards]) => {
        const totalValue = sportCards.reduce((sum, c) => sum + parseFloat(c.currentValue || 0), 0);
        const count = sportCards.length;

        return `
            <div class="sport-card" onclick="filterBySport('${sport}')">
                <div class="sport-card-header">
                    <div class="sport-name">${sport || 'Unknown'}</div>
                    <div class="sport-card-arrow">View All →</div>
                </div>
                <div class="sport-stats">
                    <div class="sport-stat">
                        <div class="sport-stat-label">Total Value</div>
                        <div class="sport-stat-value">$${totalValue.toFixed(2)}</div>
                    </div>
                    <div class="sport-stat">
                        <div class="sport-stat-label">Cards</div>
                        <div class="sport-stat-value">${count}</div>
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function filterBySport(sport) {
    currentSearchQuery = sport.toLowerCase();
    document.getElementById('searchInput').value = sport;
    changeView('all');
    handleSearch(sport);
}

// All Cards Grid
function renderAllCardsGrid() {
    const grid = document.getElementById('allCardsGrid');
    const pagination = document.getElementById('pagination');

    if (filteredCards.length === 0) {
        grid.innerHTML = getEmptyMessage();
        pagination.innerHTML = '';
        return;
    }

    const totalPages = Math.ceil(filteredCards.length / itemsPerPage);
    const startIdx = (currentPage - 1) * itemsPerPage;
    const endIdx = startIdx + itemsPerPage;
    const pageCards = filteredCards.slice(startIdx, endIdx);

    grid.innerHTML = pageCards.map(card => {
        const currentValue = parseFloat(card.currentValue || 0);
        const purchasePrice = parseFloat(card.purchasePrice || 0);
        const profit = currentValue - purchasePrice;
        const profitPercent = purchasePrice > 0 ? (profit / purchasePrice) * 100 : 0;
        return renderCardTile({ ...card, profit, profitPercent });
    }).join('');

    renderPagination(totalPages);
}

function renderPagination(totalPages) {
    const el = document.getElementById('pagination');

    if (totalPages <= 1) {
        el.innerHTML = '';
        return;
    }

    let html = `
        <button class="pagination-btn" onclick="changePage(${currentPage - 1})" ${currentPage === 1 ? 'disabled' : ''}>
            Previous
        </button>
    `;

    const maxVisible = 7;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);

    if (endPage - startPage + 1 < maxVisible) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }

    if (startPage > 1) {
        html += `<button class="pagination-btn" onclick="changePage(1)">1</button>`;
        if (startPage > 2) html += `<span class="pagination-info">...</span>`;
    }

    for (let i = startPage; i <= endPage; i++) {
        html += `<button class="pagination-btn ${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += `<span class="pagination-info">...</span>`;
        html += `<button class="pagination-btn" onclick="changePage(${totalPages})">${totalPages}</button>`;
    }

    html += `
        <button class="pagination-btn" onclick="changePage(${currentPage + 1})" ${currentPage === totalPages ? 'disabled' : ''}>
            Next
        </button>
    `;

    el.innerHTML = html;
}

function changePage(page) {
    currentPage = page;
    renderAllCardsGrid();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// Grouped View
function renderGroupedView() {
    const el = document.getElementById('groupedContent');

    if (filteredCards.length === 0) {
        el.innerHTML = getEmptyMessage();
        return;
    }

    const cardsWithProfit = filteredCards.map(card => {
        const currentValue = parseFloat(card.currentValue || 0);
        const purchasePrice = parseFloat(card.purchasePrice || 0);
        const profit = currentValue - purchasePrice;
        const profitPercent = purchasePrice > 0 ? (profit / purchasePrice) * 100 : 0;
        return { ...card, profit, profitPercent };
    });

    const groups = groupCards(cardsWithProfit, currentGroupBy);

    el.innerHTML = Object.entries(groups).map(([groupName, groupCards]) => {
        const totalValue = groupCards.reduce((sum, c) => sum + parseFloat(c.currentValue || 0), 0);
        const count = groupCards.length;

        return `
            <div class="group-section" id="group-${encodeURIComponent(groupName)}">
                <div class="group-header" onclick="toggleGroup('${encodeURIComponent(groupName)}')">
                    <div class="group-header-left">
                        <div class="group-toggle">▼</div>
                        <div class="group-title">${groupName || 'Unknown'}</div>
                    </div>
                    <div class="group-stats">
                        <span>${count} card${count !== 1 ? 's' : ''}</span>
                        <span>•</span>
                        <span>$${totalValue.toFixed(2)}</span>
                    </div>
                </div>
                <div class="group-content">
                    <div class="cards-grid">
                        ${groupCards.map(renderCardTile).join('')}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function toggleGroup(groupName) {
    const el = document.getElementById(`group-${groupName}`);
    el.classList.toggle('collapsed');
}

function groupCards(cards, groupBy) {
    const groups = {};

    cards.forEach(card => {
        let key;
        switch (groupBy) {
            case 'sport':
                key = card.sport || 'Unknown';
                break;
            case 'team':
                key = card.team || 'Unknown';
                break;
            case 'player':
                key = card.playerName || 'Unknown';
                break;
            case 'year':
                key = card.year || 'Unknown';
                break;
            default:
                key = 'Unknown';
        }

        if (!groups[key]) groups[key] = [];
        groups[key].push(card);
    });

    return groups;
}

// Card Tile Rendering
function renderCardTile(card) {
    const profitClass = card.profit > 0 ? 'positive' : card.profit < 0 ? 'negative' : 'neutral';
    const arrow = card.profit > 0 ? '↗' : card.profit < 0 ? '↘' : '→';

    let recommendation = 'HOLD';
    let recommendationClass = 'hold';
    if (card.profitPercent > 20) {
        recommendation = 'SELL';
        recommendationClass = 'sell';
    } else if (card.profitPercent < -10) {
        recommendation = 'BUY';
        recommendationClass = 'buy';
    }

    return `
        <div class="card-tile" onclick="openEditCardModal('${card.id}')">
            ${card.frontImageUrl ?
                `<img src="${card.frontImageUrl}" class="card-tile-img" alt="${card.playerName}">` :
                '<div class="card-tile-img"></div>'
            }
            <div class="card-tile-content">
                <div class="card-tile-name">${card.playerName || 'Unknown Player'}</div>
                <div class="card-tile-set">${card.year || ''} ${card.setName || ''} ${card.cardNumber ? '#' + card.cardNumber : ''}</div>
                <div class="card-tile-meta">${card.team || ''} • ${card.sport || ''}</div>
                <div class="card-tile-values">
                    <span>$${parseFloat(card.purchasePrice || 0).toFixed(2)} → $${parseFloat(card.currentValue || 0).toFixed(2)}</span>
                </div>
                <div class="card-tile-profit ${profitClass}">
                    ${card.profit >= 0 ? '+' : ''}$${Math.abs(card.profit).toFixed(2)} (${card.profitPercent >= 0 ? '+' : ''}${card.profitPercent.toFixed(2)}%) ${arrow}
                </div>
                <div class="card-badge ${recommendationClass}">${recommendation}</div>
            </div>
        </div>
    `;
}

function getEmptyMessage(message = 'No cards to display') {
    return `
        <div class="empty-state" style="grid-column: 1 / -1;">
            <div class="empty-state-icon">🎴</div>
            <div class="empty-state-title">${message}</div>
            <div class="empty-state-text">Start adding cards to your portfolio to see them here.</div>
        </div>
    `;
}

// Refresh Market Values
async function refreshAllMarketValues() {
    if (!currentUser || allCards.length === 0) {
        alert('No cards to refresh');
        return;
    }

    const progressEl = document.getElementById('refreshProgress');
    const progressText = document.getElementById('refreshProgressText');
    progressEl.classList.add('active');

    let successCount = 0;
    let errorCount = 0;

    try {
        for (let i = 0; i < allCards.length; i++) {
            const card = allCards[i];
            progressText.textContent = `Refreshing ${i + 1}/${allCards.length} cards...`;

            try {
                const response = await fetch(`https://api.collectorstream.com/v1/cards/${card.id}/market-value`, {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${currentUser.token}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.marketValue !== undefined) {
                        allCards[i].currentValue = data.marketValue;
                        successCount++;
                    } else if (data.currentValue !== undefined) {
                        allCards[i].currentValue = data.currentValue;
                        successCount++;
                    }
                } else {
                    errorCount++;
                }
            } catch (error) {
                errorCount++;
            }

            await new Promise(resolve => setTimeout(resolve, 200));
        }

        progressText.textContent = `Refresh complete! ${successCount} updated, ${errorCount} errors`;
        setTimeout(() => {
            progressEl.classList.remove('active');
            loadPortfolio();
        }, 1500);
    } catch (error) {
        console.error('Error refreshing market values:', error);
        progressText.textContent = 'Error refreshing market values';
        setTimeout(() => progressEl.classList.remove('active'), 2000);
    }
}

// Edit Card Modal Functions
function openEditCardModal(cardId) {
    const card = allCards.find(c => c.id === cardId);
    if (!card) return;

    document.getElementById('editCardId').value = card.id;
    document.getElementById('editPlayerName').value = card.playerName || '';
    document.getElementById('editTeam').value = card.team || '';
    document.getElementById('editSport').value = card.sport || '';
    document.getElementById('editYear').value = card.year || '';
    document.getElementById('editSetName').value = card.setName || '';
    document.getElementById('editCardNumber').value = card.cardNumber || '';
    document.getElementById('editManufacturer').value = card.manufacturer || '';
    document.getElementById('editCondition').value = card.condition || '';
    document.getElementById('editGradingCompany').value = card.gradingCompany || '';
    document.getElementById('editGradingGrade').value = card.gradingGrade || '';
    document.getElementById('editPurchasePrice').value = card.purchasePrice || 0;
    document.getElementById('editEstimatedValue').value = card.currentValue || card.estimatedValue || 0;
    document.getElementById('editNotes').value = card.notes || '';

    document.getElementById('editCardError').style.display = 'none';
    document.getElementById('editCardSuccess').style.display = 'none';

    document.getElementById('editCardModal').classList.add('active');
}

function closeEditCardModal() {
    document.getElementById('editCardModal').classList.remove('active');
    document.getElementById('editCardForm').reset();
}

async function saveCardEdits(e) {
    e.preventDefault();

    const cardId = document.getElementById('editCardId').value;
    const errorEl = document.getElementById('editCardError');
    const successEl = document.getElementById('editCardSuccess');

    errorEl.style.display = 'none';
    successEl.style.display = 'none';

    const cardData = {
        playerName: document.getElementById('editPlayerName').value,
        team: document.getElementById('editTeam').value,
        sport: document.getElementById('editSport').value,
        year: document.getElementById('editYear').value,
        setName: document.getElementById('editSetName').value,
        cardNumber: document.getElementById('editCardNumber').value,
        manufacturer: document.getElementById('editManufacturer').value,
        condition: document.getElementById('editCondition').value,
        gradingCompany: document.getElementById('editGradingCompany').value,
        gradingGrade: document.getElementById('editGradingGrade').value,
        purchasePrice: parseFloat(document.getElementById('editPurchasePrice').value),
        estimatedValue: parseFloat(document.getElementById('editEstimatedValue').value),
        notes: document.getElementById('editNotes').value
    };

    try {
        const response = await fetch(`https://api.collectorstream.com/v1/cards/${cardId}`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${currentUser.token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(cardData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.message || 'Failed to update card');
        }

        successEl.textContent = 'Card updated successfully!';
        successEl.style.display = 'block';

        setTimeout(() => {
            closeEditCardModal();
            loadPortfolio();
        }, 1000);
    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
    }
}

async function deleteCard() {
    const cardId = document.getElementById('editCardId').value;
    const card = allCards.find(c => c.id === cardId);
    const cardName = card ? card.playerName : 'this card';

    if (!confirm(`Are you sure you want to delete ${cardName}? This action cannot be undone.`)) {
        return;
    }

    const errorEl = document.getElementById('editCardError');
    errorEl.style.display = 'none';

    try {
        const response = await fetch(`https://api.collectorstream.com/v1/cards/${cardId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${currentUser.token}`
            }
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || 'Failed to delete card');
        }

        closeEditCardModal();
        loadPortfolio();
    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
    }
}

async function refreshSingleCardValue() {
    const cardId = document.getElementById('editCardId').value;
    const errorEl = document.getElementById('editCardError');
    const successEl = document.getElementById('editCardSuccess');
    const valueInput = document.getElementById('editEstimatedValue');

    errorEl.style.display = 'none';
    successEl.style.display = 'none';

    try {
        const response = await fetch(`https://api.collectorstream.com/v1/cards/${cardId}/market-value`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${currentUser.token}`,
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.message || 'Failed to refresh market value');
        }

        const data = await response.json();

        if (data.marketValue !== undefined) {
            valueInput.value = data.marketValue;
            successEl.textContent = `Market value updated to $${data.marketValue.toFixed(2)}`;
            successEl.style.display = 'block';
        } else if (data.currentValue !== undefined) {
            valueInput.value = data.currentValue;
            successEl.textContent = `Market value updated to $${data.currentValue.toFixed(2)}`;
            successEl.style.display = 'block';
        } else {
            errorEl.textContent = 'No market value found for this card';
            errorEl.style.display = 'block';
        }
    } catch (error) {
        errorEl.textContent = error.message;
        errorEl.style.display = 'block';
    }
}

// Admin Functions
async function loadAdminDashboard() {
    refreshAdminStats();
}

async function refreshAdminStats() {
    if (!currentUser) return;

    try {
        const response = await fetch('https://api.collectorstream.com/v1/admin/stats', {
            headers: { 'Authorization': `Bearer ${currentUser.token}` }
        });

        const data = await response.json();

        if (response.ok) {
            document.getElementById('adminTotalUsers').textContent = data.totalUsers || 0;
            document.getElementById('adminTotalCards').textContent = data.totalCards || 0;
            document.getElementById('adminActiveScrapers').textContent = data.activeScrapers || 0;
        }
    } catch (error) {
        console.error('Error loading admin stats:', error);
    }
}

async function loadAdminUsers() {
    alert('User management UI - Connect to GET /v1/admin/users endpoint');
}

async function loadAdminScrapers() {
    alert('Scraper management UI - Connect to GET /v1/admin/scrapers endpoint');
}
