document.addEventListener('DOMContentLoaded', () => {
    const cameraInput = document.getElementById('camera-input');
    const uploadInput = document.getElementById('upload-input');
    const manualQueryInput = document.getElementById('manual-query');
    const digBtn = document.getElementById('dig-btn');
    const loadingOverlay = document.getElementById('loading-overlay');
    const loadingText = document.getElementById('loading-text');
    const resultsSection = document.getElementById('results-section');
    const resultsGrid = document.getElementById('results-grid');
    const searchTermSpan = document.getElementById('search-term');
    const sortSelect = document.getElementById('sort-select');
    const regionCodeSpan = document.getElementById('region-code');

    let currentResults = [];
    let selectedFile = null;
    let userCountry = 'us'; // Default

    // Pagination state
    let currentPage = 1;
    const itemsPerPage = 10;

    // 1. Detect Location
    if ("geolocation" in navigator) {
        navigator.geolocation.getCurrentPosition(async (position) => {
            try {
                const { latitude, longitude } = position.coords;
                // Reverse Geocoding to get Country Code (using a free API or approximate)
                // For simplicity, we'll try to fetch from a geo-ip service if possible, 
                // or just default to 'us' if we can't easily reverse geocode without another key.
                // A simple trick is to ask the backend to detect IP, but here we'll just show coordinates or 'Detected'.

                // Let's try a simple fetch to a free geoip service for better UX
                const response = await fetch('https://ipapi.co/json/');
                const data = await response.json();
                if (data.country_code) {
                    userCountry = data.country_code.toLowerCase();
                    regionCodeSpan.textContent = userCountry.toUpperCase();
                } else {
                    regionCodeSpan.textContent = "US (Default)";
                }
            } catch (e) {
                console.log("Geo-IP failed, defaulting to US");
                regionCodeSpan.textContent = "US (Default)";
            }
        }, (error) => {
            console.log("Location denied, defaulting to US");
            regionCodeSpan.textContent = "US (Default)";
        });
    } else {
        regionCodeSpan.textContent = "US (Default)";
    }

    // Event Listeners
    cameraInput.addEventListener('change', (e) => {
        if (e.target.files[0]) {
            selectedFile = e.target.files[0];
            manualQueryInput.value = `Image: ${selectedFile.name}`; // Visual feedback
        }
    });

    uploadInput.addEventListener('change', (e) => {
        if (e.target.files[0]) {
            selectedFile = e.target.files[0];
            manualQueryInput.value = `Image: ${selectedFile.name}`; // Visual feedback
        }
    });

    digBtn.addEventListener('click', startSearch);

    // Allow Enter key in text box to trigger search
    manualQueryInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') startSearch();
    });

    sortSelect.addEventListener('change', () => renderResults(currentResults));

    async function startSearch() {
        const manualText = manualQueryInput.value.trim();

        if (!selectedFile && !manualText) {
            alert("Please capture/upload an image or enter a description.");
            return;
        }

        // Reset UI
        resultsSection.classList.add('hidden');
        showLoading(true, "Starting search...");

        try {
            let query = "";

            // 1. Identify Product if Image exists
            if (selectedFile) {
                showLoading(true, "Analyzing image...");
                const formData = new FormData();
                formData.append('image', selectedFile);

                const identifyResponse = await fetch('/api/identify', {
                    method: 'POST',
                    body: formData
                });

                if (!identifyResponse.ok) throw new Error('Failed to identify image');

                const identifyData = await identifyResponse.json();
                query = identifyData.query;
            }

            // Append manual description if present (and not just the placeholder)
            if (manualText && !manualText.startsWith("Image: ")) {
                query = query ? `${query} ${manualText}` : manualText;
            }

            if (!query) throw new Error('Could not determine what to search for.');

            // 2. Search Products
            showLoading(true, `Searching for "${query}" in ${userCountry.toUpperCase()}...`);
            searchTermSpan.textContent = query;

            const searchResponse = await fetch(`/api/search?q=${encodeURIComponent(query)}&country=${userCountry}`);
            if (!searchResponse.ok) throw new Error('Search failed');

            const searchData = await searchResponse.json();
            currentResults = searchData.results || [];

            // 3. Display Results
            currentPage = 1; // Reset to first page for new search
            renderResults(currentResults);
            resultsSection.classList.remove('hidden');

        } catch (error) {
            console.error(error);
            alert('An error occurred: ' + error.message);
        } finally {
            showLoading(false);
            // Clear file selection after search? Optional. 
            // Keeping it allows re-search.
        }
    }

    function showLoading(show, text = "Loading...") {
        if (show) {
            loadingText.textContent = text;
            loadingOverlay.classList.remove('hidden');
        } else {
            loadingOverlay.classList.add('hidden');
        }
    }

    function renderResults(results) {
        resultsGrid.innerHTML = '';
        const paginationControls = document.getElementById('pagination-controls');

        if (results.length === 0) {
            resultsGrid.innerHTML = '<p style="text-align: center; color: #666;">No results found.</p>';
            if (paginationControls) paginationControls.classList.add('hidden');
            return;
        }

        // Sort
        const sortMode = sortSelect.value;
        const sortedResults = [...results].sort((a, b) => {
            if (sortMode === 'price-asc') return a.price - b.price;
            if (sortMode === 'price-desc') return b.price - a.price;
            return 0;
        });

        // Calculate pagination
        const totalPages = Math.ceil(sortedResults.length / itemsPerPage);
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const pageResults = sortedResults.slice(startIndex, endIndex);

        // Render current page items
        pageResults.forEach(item => {
            const card = document.createElement('div');
            card.className = 'product-card';

            // Format price
            const symbol = item.currency === 'INR' ? '₹' : '$';
            const priceFormatted = `${symbol}${item.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

            card.innerHTML = `
                <div class="product-image-container">
                    <img src="${item.image}" alt="${escapeHtml(item.name)}" class="product-image" onerror="this.src='https://placehold.co/200x200?text=No+Image'">
                </div>
                <div class="product-info">
                    <div class="product-store">${escapeHtml(item.store)}</div>
                    <div class="product-name">${escapeHtml(item.name)}</div>
                    <div class="product-price">${priceFormatted}</div>
                </div>
                <a href="${item.link}" target="_blank" rel="noopener noreferrer" class="view-btn">View Product</a>
            `;

            resultsGrid.appendChild(card);
        });

        // Render pagination controls
        if (totalPages > 1 && paginationControls) {
            paginationControls.classList.remove('hidden');
            paginationControls.innerHTML = '';

            // Previous button
            const prevBtn = document.createElement('button');
            prevBtn.className = 'page-btn';
            prevBtn.textContent = '← Previous';
            prevBtn.disabled = currentPage === 1;
            prevBtn.onclick = () => {
                if (currentPage > 1) {
                    currentPage--;
                    renderResults(currentResults);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            };
            paginationControls.appendChild(prevBtn);

            // Page numbers
            const pageInfo = document.createElement('span');
            pageInfo.className = 'page-info';
            pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
            paginationControls.appendChild(pageInfo);

            // Next button
            const nextBtn = document.createElement('button');
            nextBtn.className = 'page-btn';
            nextBtn.textContent = 'Next →';
            nextBtn.disabled = currentPage === totalPages;
            nextBtn.onclick = () => {
                if (currentPage < totalPages) {
                    currentPage++;
                    renderResults(currentResults);
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            };
            paginationControls.appendChild(nextBtn);
        } else if (paginationControls) {
            paginationControls.classList.add('hidden');
        }
    }

    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
