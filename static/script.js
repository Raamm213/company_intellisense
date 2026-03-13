document.addEventListener('DOMContentLoaded', () => {
    // --- State Management ---
    let currentPollingInterval = null;
    let searchHistory = [];

    // --- Selectors ---
    const companyInput = document.getElementById('company-name');
    const triggerBtn = document.getElementById('trigger-btn');
    const statusView = document.getElementById('status-view');
    const statusText = document.getElementById('status-text');
    const resultsView = document.getElementById('results-view');
    const jsonOutput = document.getElementById('json-output');
    
    const timeVal = document.getElementById('time-val');
    const tokensVal = document.getElementById('tokens-val');
    const paramsVal = document.getElementById('params-val');

    const navButtons = document.querySelectorAll('.nav-btn[data-tab]');
    const tabContents = document.querySelectorAll('.tab-content');
    
    const historyRows = document.getElementById('history-rows');
    const modalContainer = document.getElementById('modal-container');
    const modalClose = document.getElementById('modal-close');
    const modalTitle = document.getElementById('modal-title');
    const modalJson = document.getElementById('modal-json');

    // --- Tab Switching ---
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            
            // Switch active button
            navButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Switch active tab
            tabContents.forEach(tab => {
                tab.classList.remove('active');
            });
            document.getElementById(`${tabId}-tab`).classList.add('active');
            
            if (tabId === 'history') {
                loadHistory();
            }
        });
    });

    // --- API Calls ---

    async function startSearch() {
        const company = companyInput.value.trim();
        if (!company) {
            alert('Please enter a company name');
            return;
        }

        // Reset UI
        resultsView.classList.add('hidden');
        statusView.classList.remove('hidden');
        triggerBtn.disabled = true;
        statusText.innerText = `Searching for ${company}...`;

        try {
            const response = await fetch('/api/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ company_name: company })
            });

            if (!response.ok) throw new Error('Failed to initiate search');

            // Start polling for status
            pollStatus(company);
        } catch (error) {
            console.error(error);
            showError('Search failed to start');
        }
    }

    async function pollStatus(company) {
        if (currentPollingInterval) clearInterval(currentPollingInterval);

        currentPollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/status/${encodeURIComponent(company)}`);
                const data = await response.json();

                if (data.status === 'completed') {
                    clearInterval(currentPollingInterval);
                    fetchResults(company);
                } else if (data.status === 'failed') {
                    clearInterval(currentPollingInterval);
                    showError('Process failed. Please try again.');
                } else {
                    statusText.innerText = `Processing: ${company}...`;
                }
            } catch (error) {
                console.error('Polling error:', error);
            }
        }, 2000);
    }

    async function fetchResults(company) {
        try {
            const response = await fetch(`/api/results/${encodeURIComponent(company)}`);
            if (!response.ok) throw new Error('Failed to fetch results');
            
            const data = await response.json();
            displayResults(data);
        } catch (error) {
            showError('Error loading results');
        }
    }

    function displayResults(data) {
        statusView.classList.add('hidden');
        resultsView.classList.remove('hidden');
        triggerBtn.disabled = false;

        // Populate metrics
        timeVal.innerText = `${data.metrics?.time_taken || 0}s`;
        tokensVal.innerText = (data.metrics?.tokens_used || 0).toLocaleString();
        
        const params = Object.keys(data.consolidated || {}).length;
        paramsVal.innerText = params;

        // Populate validation
        const validation = data.validation || { status: 'unknown', error_count: 0, errors: [] };
        const validationVal = document.getElementById('validation-val');
        const errorCard = document.getElementById('validation-error-card');
        const errorList = document.getElementById('validation-errors');

        if (validation.status === 'pass' && params > 0) {
            validationVal.innerText = 'PASSED';
            validationVal.style.color = 'var(--success-color)';
            errorCard.classList.add('hidden');
        } else if (params === 0) {
            validationVal.innerText = 'N/A';
            validationVal.style.color = 'var(--text-dim)';
            errorCard.classList.add('hidden');
        } else {
            const total = validation.total_rules || 163;
            const passed = Math.max(0, total - validation.error_count);
            const score = Math.round((passed / total) * 100);
            
            validationVal.innerText = `${score}%`;
            validationVal.style.color = score < 60 ? 'var(--error-color)' : (score < 90 ? 'var(--warning-color)' : 'var(--success-color)');
            
            // Show errors
            errorList.innerHTML = '';
            validation.errors.slice(0, 5).forEach(err => {
                const item = document.createElement('div');
                item.className = 'error-item';
                item.innerHTML = `<i class="fas fa-circle-exclamation"></i> ${err}`;
                errorList.appendChild(item);
            });
            if (validation.errors.length > 5) {
                const more = document.createElement('div');
                more.className = 'error-item-more';
                more.innerText = `+ ${validation.errors.length - 5} more issues...`;
                errorList.appendChild(more);
            }
            errorCard.classList.remove('hidden');
        }

        // Populate JSON
        jsonOutput.textContent = JSON.stringify(data.consolidated, null, 2);
    }

    async function loadHistory() {
        try {
            const response = await fetch('/api/history');
            const data = await response.json();
            searchHistory = data;
            
            historyRows.innerHTML = '';
            data.forEach(item => {
                const row = document.createElement('tr');
                const date = new Date(item.timestamp * 1000).toLocaleString();
                
                row.innerHTML = `
                    <td><strong>${item.name}</strong></td>
                    <td>${date}</td>
                    <td>
                        <button class="tool-btn view-h-btn" data-company="${item.name}"><i class="fas fa-eye"></i></button>
                    </td>
                `;
                historyRows.appendChild(row);
            });

            // Add event listeners to view buttons
            document.querySelectorAll('.view-h-btn').forEach(btn => {
                btn.addEventListener('click', () => {
                    viewHistoryItem(btn.getAttribute('data-company'));
                });
            });
        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    async function viewHistoryItem(company) {
        try {
            const response = await fetch(`/api/results/${encodeURIComponent(company)}`);
            const data = await response.json();
            
            modalTitle.innerText = `${company} Profile`;
            modalJson.textContent = JSON.stringify(data.consolidated, null, 2);
            modalContainer.classList.remove('hidden');
        } catch (error) {
            alert('Failed to load details');
        }
    }

    // --- Utilities ---

    function showError(msg) {
        statusView.classList.add('hidden');
        triggerBtn.disabled = false;
        alert(msg);
    }

    // --- Event Listeners ---
    triggerBtn.addEventListener('click', startSearch);
    companyInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') startSearch();
    });

    modalClose.addEventListener('click', () => {
        modalContainer.classList.add('hidden');
    });

    window.addEventListener('click', (e) => {
        if (e.target === modalContainer) modalContainer.classList.add('hidden');
    });

    document.getElementById('btn-copy').addEventListener('click', () => {
        navigator.clipboard.writeText(jsonOutput.textContent);
        const icon = document.querySelector('#btn-copy i');
        icon.className = 'fas fa-check';
        setTimeout(() => icon.className = 'fas fa-copy', 2000);
    });

    document.getElementById('btn-download').addEventListener('click', () => {
        const company = companyInput.value || 'company';
        const blob = new Blob([jsonOutput.textContent], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${company.toLowerCase().replace(/ /g, '_')}_intel.json`;
        a.click();
    });
    
    // Initial Load
    loadHistory();
});
