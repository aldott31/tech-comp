/**
 * Albanian Tech Map - Vanilla JavaScript
 * Interactive map using Leaflet
 */

(function() {
    'use strict';

    // Global variables
    let map = null;
    let markers = [];
    let companies = [];
    let currentFilter = 'all';

    /**
     * Initialize the map when DOM is ready
     */
    function initMap() {
        // Create map instance
        map = L.map('map', {
            center: TECHMAP_CONFIG.mapCenter,
            zoom: TECHMAP_CONFIG.mapZoom,
            zoomControl: true,
        });

        // Add OpenStreetMap tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 19,
        }).addTo(map);

        // Fix Leaflet default marker icon paths
        delete L.Icon.Default.prototype._getIconUrl;
        L.Icon.Default.mergeOptions({
            iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
            iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
            shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
        });

        // Load companies from API
        loadCompanies();

        // Setup event listeners
        setupEventListeners();
    }

    /**
     * Load companies from API
     */
    function loadCompanies() {
        console.log('Loading companies from API...');

        fetch(TECHMAP_CONFIG.apiUrl)
            .then(response => response.json())
            .then(data => {
                console.log(`Loaded ${data.length} companies`);
                companies = data;
                displayCompanies(companies);
                populateCompanyList(companies);

                // If there's a selected company, zoom to it
                if (TECHMAP_CONFIG.selectedCompanyId) {
                    const company = companies.find(c => c.id === TECHMAP_CONFIG.selectedCompanyId);
                    if (company) {
                        map.setView([company.lat, company.lng], 16);
                    }
                }
            })
            .catch(error => {
                console.error('Error loading companies:', error);
                showError('Gabim në ngarkimin e të dhënave. Ju lutem provoni përsëri më vonë.');
            });
    }

    /**
     * Display companies on map
     */
    function displayCompanies(companiesToDisplay) {
        // Clear existing markers
        markers.forEach(marker => map.removeLayer(marker));
        markers = [];

        // Add markers for each company
        companiesToDisplay.forEach(company => {
            if (company.lat && company.lng) {
                const marker = L.marker([company.lat, company.lng])
                    .addTo(map);

                // Create popup content
                const popupContent = createPopupContent(company);
                marker.bindPopup(popupContent);

                // Add marker to array
                markers.push(marker);
            }
        });

        console.log(`Displayed ${markers.length} markers on map`);
    }

    /**
     * Create popup content for a company
     */
    function createPopupContent(company) {
        const div = document.createElement('div');
        div.className = 'infoWindow';

        div.innerHTML = `
            <h3>${escapeHtml(company.name)}</h3>
            ${company.nipt ? `<p class="mb-1"><small class="text-muted">NIPT: ${escapeHtml(company.nipt)}</small></p>` : ''}
            ${company.city ? `<p class="mb-1"><i class="fa fa-map-marker"></i> ${escapeHtml(company.city)}</p>` : ''}
            <div class="popup-links">
                ${company.website ? `
                    <a href="${escapeHtml(company.website)}" target="_blank" rel="noopener noreferrer" class="btn btn-sm btn-link">
                        <i class="fa fa-globe"></i> WEBSITE →
                    </a>
                ` : ''}
                ${company.email ? `
                    <a href="mailto:${escapeHtml(company.email)}" class="btn btn-sm btn-link">
                        <i class="fa fa-envelope"></i> ${escapeHtml(company.email)}
                    </a>
                ` : ''}
                ${company.phone ? `
                    <a href="tel:${escapeHtml(company.phone)}" class="btn btn-sm btn-link">
                        <i class="fa fa-phone"></i> ${escapeHtml(company.phone)}
                    </a>
                ` : ''}
            </div>
        `;

        return div;
    }

    /**
     * Populate company list in sidebar
     */
    function populateCompanyList(companiesToDisplay) {
        const listContainer = document.getElementById('company-list');
        if (!listContainer) return;

        listContainer.innerHTML = '';

        if (companiesToDisplay.length === 0) {
            listContainer.innerHTML = '<div class="alert alert-info m-2">Nuk u gjet asnjë kompani.</div>';
            return;
        }

        companiesToDisplay.forEach(company => {
            const item = document.createElement('div');
            item.className = 'company-list-item';
            item.innerHTML = `
                <div class="company-name">${escapeHtml(company.name)}</div>
                <div class="company-meta">
                    <span class="badge bg-info">${escapeHtml(company.category)}</span>
                    ${company.city ? `<span class="badge bg-secondary">${escapeHtml(company.city)}</span>` : ''}
                </div>
            `;

            // Click to zoom to company
            item.addEventListener('click', () => {
                map.setView([company.lat, company.lng], 16);

                // Find and open the marker popup
                const marker = markers.find(m =>
                    m.getLatLng().lat === company.lat &&
                    m.getLatLng().lng === company.lng
                );
                if (marker) {
                    marker.openPopup();
                }
            });

            listContainer.appendChild(item);
        });
    }

    /**
     * Setup event listeners
     */
    function setupEventListeners() {
        // Filter buttons
        const filterAll = document.getElementById('filter-all');
        const filterSoftware = document.getElementById('filter-software');
        const filterAgency = document.getElementById('filter-agency');

        if (filterAll) {
            filterAll.addEventListener('click', () => filterCompanies('all'));
        }
        if (filterSoftware) {
            filterSoftware.addEventListener('click', () => filterCompanies('software'));
        }
        if (filterAgency) {
            filterAgency.addEventListener('click', () => filterCompanies('agency'));
        }

        // Search input
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                const query = e.target.value.toLowerCase();
                filterBySearch(query);
            });
        }

        // Toggle sidebar
        const toggleBtn = document.getElementById('toggle-sidebar');
        const sidebar = document.getElementById('side-panel');
        if (toggleBtn && sidebar) {
            toggleBtn.addEventListener('click', () => {
                sidebar.classList.toggle('hidden');
            });
        }
    }

    /**
     * Filter companies by category
     */
    function filterCompanies(filter) {
        currentFilter = filter;

        let filtered = companies;

        if (filter === 'software') {
            filtered = companies.filter(c =>
                c.category.toLowerCase().includes('software')
            );
        } else if (filter === 'agency') {
            filtered = companies.filter(c =>
                c.category.toLowerCase().includes('agency') ||
                c.category.toLowerCase().includes('digital')
            );
        }

        displayCompanies(filtered);
        populateCompanyList(filtered);

        // Update active button
        document.querySelectorAll('.btn-group button').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(`filter-${filter}`).classList.add('active');
    }

    /**
     * Filter companies by search query
     */
    function filterBySearch(query) {
        if (!query) {
            displayCompanies(companies);
            populateCompanyList(companies);
            return;
        }

        const filtered = companies.filter(c =>
            c.name.toLowerCase().includes(query) ||
            (c.category && c.category.toLowerCase().includes(query)) ||
            (c.city && c.city.toLowerCase().includes(query))
        );

        displayCompanies(filtered);
        populateCompanyList(filtered);
    }

    /**
     * Show error message
     */
    function showError(message) {
        const mapContainer = document.getElementById('map');
        if (mapContainer) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'alert alert-danger map-error';
            errorDiv.innerHTML = `<i class="fa fa-exclamation-triangle"></i> ${message}`;
            mapContainer.parentNode.insertBefore(errorDiv, mapContainer);
        }
    }

    /**
     * Escape HTML to prevent XSS
     */
    function escapeHtml(text) {
        if (!text) return '';
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }

    // Initialize map when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMap);
    } else {
        initMap();
    }

})();
