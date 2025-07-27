document.addEventListener('DOMContentLoaded', () => {
    const themeToggle = document.getElementById('themeToggle');
    const darkTheme = document.getElementById('dark-theme');
    const lightTheme = document.getElementById('light-theme');
    const nbaToggle = document.querySelector('.theme-toggle:not(#themeToggle)');

    const hasPlayoffTables = checkForMeaningfulPlayoffTables();
    if (nbaToggle && !hasPlayoffTables) nbaToggle.style.display = 'none';

    const savedTheme = localStorage.getItem('theme') || 'dark';
    const savedStatsMode = hasPlayoffTables ? (localStorage.getItem('statsMode') || 'regular') : 'regular';

    applyTheme(savedTheme);
    if (hasPlayoffTables && nbaToggle) applyStatsMode(savedStatsMode);

    updateThemeOnServer(savedTheme);
    if (hasPlayoffTables) updateStatsModeOnServer(savedStatsMode);

    themeToggle?.addEventListener('click', () => {
        const isLight = themeToggle.classList.toggle('light');
        document.body.classList.toggle('light-mode');
        darkTheme.disabled = isLight;
        lightTheme.disabled = !isLight;

        const newTheme = isLight ? 'light' : 'dark';
        localStorage.setItem('theme', newTheme);
        updateThemeOnServer(newTheme);
    });

    if (nbaToggle && hasPlayoffTables) {
        nbaToggle.addEventListener('click', () => {
            const isPlayoff = nbaToggle.classList.toggle('playoff-mode');
            const mode = isPlayoff ? 'playoff' : 'regular';
            applyStatsMode(mode);
            localStorage.setItem('statsMode', mode);
            updateStatsModeOnServer(mode);
        });
    }

    function applyTheme(theme) {
        if (theme === 'light') {
            themeToggle?.classList.add('light');
            darkTheme.disabled = true;
            lightTheme.disabled = false;
            document.body.classList.add('light-mode');
        } else {
            themeToggle?.classList.remove('light');
            darkTheme.disabled = false;
            lightTheme.disabled = true;
            document.body.classList.remove('light-mode');
        }
    }

    function applyStatsMode(mode) {
        const playerGrids = document.querySelectorAll('.playerGrid');

        playerGrids.forEach(grid => {
            const [regularTable, playoffTable] = grid.querySelectorAll('.playerTable');
            if (!regularTable) return;

            const isPlayoff = mode === 'playoff';
            const hasPlayoff = playoffTable && isTableMeaningful(playoffTable);

            regularTable.style.display = !isPlayoff || !hasPlayoff ? 'block' : 'none';
            if (playoffTable) playoffTable.style.display = isPlayoff && hasPlayoff ? 'block' : 'none';

            const existingMsg = grid.querySelector('.no-playoff-data');
            if (isPlayoff && !hasPlayoff) {
                if (!existingMsg) {
                    const msg = document.createElement('div');
                    msg.className = 'no-playoff-data';
                    msg.textContent = 'No playoff statistics available';
                    Object.assign(msg.style, {
                        color: '#ff9800',
                        fontWeight: 'bold',
                        textAlign: 'center',
                        padding: '10px',
                        marginTop: '10px'
                    });
                    grid.insertBefore(msg, playoffTable);
                } else {
                    existingMsg.style.display = 'block';
                }
            } else if (existingMsg) {
                existingMsg.style.display = 'none';
            }
        });

        if (nbaToggle) {
            const isPlayoff = mode === 'playoff';

            // Sync the button's class state with the mode
            if (isPlayoff) {
                nbaToggle.classList.add('playoff-mode');
            } else {
                nbaToggle.classList.remove('playoff-mode');
            }

            const sun = nbaToggle.querySelector('.sun');
            const moon = nbaToggle.querySelector('.moon');
            if (sun && moon) {
                sun.style.opacity = isPlayoff ? '0' : '1';
                moon.style.opacity = isPlayoff ? '1' : '0';
            }
        }

        updateModeIndicator(mode);
    }

    function updateModeIndicator(mode) {
        let indicator = document.getElementById('statsIndicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'statsIndicator';
            Object.assign(indicator.style, {
                position: 'fixed',
                bottom: '65px',
                left: '65px',
                padding: '5px 10px',
                borderRadius: '4px',
                fontSize: '12px',
                fontWeight: 'bold',
                zIndex: '1000',
                boxShadow: '0 1px 3px rgba(0,0,0,0.3)'
            });
            document.body.appendChild(indicator);
        }

        indicator.textContent = mode === 'playoff' ? 'Playoff Stats' : 'Regular Stats';
        indicator.style.backgroundColor = mode === 'playoff' ? '#FFD700' : '#17408B';
        indicator.style.color = mode === 'playoff' ? '#000' : '#fff';
    }

    function checkForMeaningfulPlayoffTables() {
        return Array.from(document.querySelectorAll('.playerGrid')).some(grid => {
            const tables = grid.querySelectorAll('.playerTable');
            return tables.length > 1 && isTableMeaningful(tables[1]);
        });
    }

    function isTableMeaningful(table) {
        const content = table.textContent.trim().toLowerCase();
        if (!content || /no data|no playoff|not available|no stats/.test(content)) return false;
        if (table.querySelector('table')?.rows.length <= 1) return false;

        const filledCells = Array.from(table.querySelectorAll('td')).filter(td => td.textContent.trim() !== '').length;
        return filledCells > 3;
    }

    // Function to get CSRF token from meta tag or cookie
    function getCSRFToken() {
        // Method 1: Try to get from meta tag (if you have it in your HTML head)
        const metaToken = document.querySelector('meta[name="csrf-token"]');
        if (metaToken) {
            return metaToken.getAttribute('content');
        }

        // Method 2: Try to get from cookie
        const cookies = document.cookie.split(';');
        for (let cookie of cookies) {
            const [name, value] = cookie.trim().split('=');
            if (name === 'csrf_token') {
                return decodeURIComponent(value);
            }
        }

        // Method 3: Try to get from a hidden form field (if you have one)
        const hiddenInput = document.querySelector('input[name="csrf_token"]');
        if (hiddenInput) {
            return hiddenInput.value;
        }

        return null;
    }

    function updateThemeOnServer(theme) {
        console.log('Sending theme to server:', theme);
        const payload = { theme };
        console.log('Payload:', JSON.stringify(payload));

        const csrfToken = getCSRFToken();
        const headers = { 'Content-Type': 'application/json' };

        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;  // or 'X-CSRF-Token' depending on your setup
        }

        fetch('/update_theme', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(payload)
        })
        .then(res => {
            console.log('Server response status:', res.status);

            if (res.status === 401) {
                console.log('Theme saved locally (not logged in)');
                return null;
            }
            if (!res.ok) {
                return res.text().then(text => {
                    console.log('Server error response:', text);
                    throw new Error(`HTTP error! status: ${res.status}, message: ${text}`);
                });
            }
            return res.json();
        })
        .then(data => {
            if (data) {
                console.log('Theme updated on server:', data);
            }
        })
        .catch(error => {
            console.error('Theme update failed:', error);
        });
    }

    function updateStatsModeOnServer(mode) {
        const csrfToken = getCSRFToken();
        const headers = { 'Content-Type': 'application/json' };

        if (csrfToken) {
            headers['X-CSRFToken'] = csrfToken;  // or 'X-CSRF-Token' depending on your setup
        }

        fetch('/update_stats_mode', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({ mode })
        })
        .then(res => {
            if (res.status === 401) {
                console.log('Stats mode saved locally (not logged in)');
                return null;
            }
            if (!res.ok) {
                return res.text().then(text => {
                    throw new Error(`HTTP error! status: ${res.status}, message: ${text}`);
                });
            }
            return res.json();
        })
        .then(data => {
            if (data) {
                console.log('Stats mode updated on server:', data.mode || mode);
            }
        })
        .catch(error => {
            console.error('Stats mode update failed:', error);
        });
    }
});

// AI Deep Thinking Mode Toggle Button JavaScript
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, looking for thinking button...');

    const thinkingBtn = document.getElementById('thinkingBtn');
    const searchStats = document.getElementById('StatsSearch');
    const searchAI = document.getElementById('AISearch');
    const statsContainer = document.getElementById('search-input');
    const AIContainer = document.getElementById('searchAI');
    const modeText = document.getElementById('queryModeIndicator');

    // Get saved AI mode preference, default to true (AI mode)
    const savedAIMode = localStorage.getItem('aiMode');
    let isThinking = savedAIMode !== null ? savedAIMode === 'true' : true;

    console.log('Loaded AI mode from localStorage:', isThinking);

    // Apply the saved mode on page load
    applyAIMode(isThinking);

    console.log('thinkingBtn:', thinkingBtn);

    if (thinkingBtn) {
        console.log('Elements found, adding click listener...');

        thinkingBtn.addEventListener('click', function() {
            console.log('Button clicked!');
            isThinking = !isThinking;

            console.log('isThinking:', isThinking);

            // Save the new preference
            localStorage.setItem('aiMode', isThinking.toString());
            console.log('Saved AI mode to localStorage:', isThinking);

            applyAIMode(isThinking);

            // Optional: Trigger custom event for other parts of your application
            const customEvent = new CustomEvent('thinkingModeToggle', {
                detail: { isThinking: isThinking }
            });
            document.dispatchEvent(customEvent);
        });
    } else {
        console.error('Could not find elements:', {
            thinkingBtn: thinkingBtn,
        });
    }

    // Function to apply AI mode settings
    function applyAIMode(isThinking) {
        modeText.style.opacity = '0';

        setTimeout(() => {
            modeText.innerText = isThinking ? "AI Mode" : "Stat Mode";
            modeText.classList.toggle('aiMode', isThinking);
            modeText.classList.toggle('statMode', !isThinking);
            modeText.style.opacity = '1';
        }, 300); // Delay matches the CSS transition duration

        if (isThinking) {
            thinkingBtn.classList.add('active');
            searchStats.hidden = true;
            statsContainer.disabled = true;
            searchAI.hidden = false;
            AIContainer.disabled = false;
            console.log('Applied AI mode');
        } else {
            thinkingBtn.classList.remove('active');
            searchStats.hidden = false;
            statsContainer.disabled = false;
            searchAI.hidden = true;
            AIContainer.disabled = true;
            console.log('Applied Stat mode');
        }
    }
});

// Fallback if DOMContentLoaded doesn't work
setTimeout(function() {
    if (!document.getElementById('thinkingBtn')) {
        console.error('Button still not found after timeout. Check if HTML is properly loaded.');
    }
}, 1000);

// Optional: Function to get current thinking mode state
function getThinkingMode() {
    const thinkingBtn = document.getElementById('thinkingBtn');
    return thinkingBtn ? thinkingBtn.classList.contains('active') : false;
}

document.addEventListener('keydown', function (e) {
  if (e.key === 'Enter') {
    const target = e.target;

    // Only handle text inputs
    if (target.tagName === 'INPUT' && target.type === 'text') {
      e.preventDefault();

      const form = target.form;

      // If current input is disabled, trigger alternate logic
      if (target.disabled) {
        if (target.id === 'search-input') {
          const altInput = document.getElementById('searchAI');
          if (!altInput.disabled) {
            console.log('search-input is disabled, triggering searchAI logic');
            form.querySelector('input[name="Submit"]')?.remove(); // clean up if needed

            const hiddenSubmit = document.createElement('input');
            hiddenSubmit.type = 'hidden';
            hiddenSubmit.name = 'Submit';
            hiddenSubmit.value = 'Submit';
            form.appendChild(hiddenSubmit);

            form.submit();
          }
        } else if (target.id === 'searchAI') {
          const altInput = document.getElementById('search-input');
          if (!altInput.disabled) {
            console.log('searchAI is disabled, triggering search-input logic');
            form.querySelector('input[name="Submit"]')?.remove();

            const hiddenSubmit = document.createElement('input');
            hiddenSubmit.type = 'hidden';
            hiddenSubmit.name = 'Submit';
            hiddenSubmit.value = 'Submit';
            form.appendChild(hiddenSubmit);

            form.submit();
          }
        }
      } else {
        // If input is enabled, submit normally
        console.log('Active input is enabled, submitting form');
        form.querySelector('input[name="Submit"]')?.remove();

        const hiddenSubmit = document.createElement('input');
        hiddenSubmit.type = 'hidden';
        hiddenSubmit.name = 'Submit';
        hiddenSubmit.value = 'Submit';
        form.appendChild(hiddenSubmit);

        form.submit();
      }
    }
  }
});

// Help button functionality
document.addEventListener('DOMContentLoaded', function() {
    const helpBtn = document.getElementById('helpBtn');
    const helpIndicator = document.getElementById('helpModeIndicator');
    let helpMode = false;

    if (helpBtn) {
        helpBtn.addEventListener('click', function() {
            helpMode = !helpMode;

            if (helpMode) {
                // Activate help mode
                helpBtn.classList.add('active');
                helpIndicator.classList.add('show');

                // Show help content (you can customize this)
                showHelpContent();
            } else {
                // Deactivate help mode
                helpBtn.classList.remove('active');
                helpIndicator.classList.remove('show');

                // Hide help content
                hideHelpContent();
            }
        });
    }

    function showHelpContent() {
        // Create and show help modal or tooltip
        // You can customize this based on your needs
        const helpContent = `
            <div id="helpModal" style="
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: linear-gradient(145deg, #ffffff, #f8f9fa);
                border-radius: 12px;
                padding: 2rem;
                box-shadow: 0 1rem 3rem rgba(0,0,0,0.3);
                z-index: 1000;
                max-width: 600px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                color: #333;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                    <h3 style="margin: 0; color: #1e40af;">The Basketball Oracle 🏀📊</h3>
                    <button onclick="document.getElementById('helpModal').remove(); document.getElementById('helpOverlay').remove(); document.getElementById('helpBtn').classList.remove('active'); document.getElementById('helpModeIndicator').classList.remove('show');" style="
                        background: none;
                        border: none;
                        font-size: 1.5rem;
                        cursor: pointer;
                        color: #666;
                        padding: 0;
                        width: 2rem;
                        height: 2rem;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        border-radius: 50%;
                        transition: all 0.2s;
                    " onmouseover="this.style.background='#f0f0f0'" onmouseout="this.style.background='none'">✕</button>
                </div>

                <div style="line-height: 1.6;">
                    <p style="color: #666; margin-bottom: 1.5rem; font-style: italic;">A dynamic NBA analytics website where you can explore standings, view live scores, inspect team rosters, analyze player careers, check boxscores, and predict player performance using machine learning and RAG-powered search.</p>

                    <h5 style="color: #1e40af; margin-bottom: 0.5rem;">🔍 Search Features</h5>
                    <p><strong>AI Mode:</strong> Ask natural language questions powered by a RAG pipeline. Try questions like:</p>
                    <ul style="margin-left: 1rem; color: #555;">
                        <li><em>"How did analytics change player scouting in the NBA?"</em></li>
                        <li><em>"Has switch-heavy defense redefined what it means to be a 'good defender'?"</em></li>
                        <li><em>"Why was Luka Doncic traded?"</em></li>
                    </ul>
                    <p><strong>Stats Mode:</strong> Search for specific players and teams. Separate multiple players with comma and space (e.g., "LeBron James, Stephen Curry"). You can search for teams as well.</p>

                    <h5 style="color: #1e40af; margin-bottom: 0.5rem; margin-top: 1.5rem;">📊 What is <a href="/protected/pri" style="color: #1e40af; text-decoration: none; font-weight: bold;">PRI</a>?</h5>
                    <p>Player Rating Index - A custom metric for player comparison that rates each player based on their current season performance.</p>

                    <h5 style="color: #1e40af; margin-bottom: 0.5rem; margin-top: 1.5rem;">🏀 Navigation</h5>
                    <p>• <strong>Players:</strong> Click any player name anywhere on the site to view their player page with ML predictions and career stats</p>
                    <p>• <strong>Teams:</strong> Click team names, logos, or abbreviations to explore roster details and team info</p>
                    <p>• <strong>Games:</strong> Click on scorecard games (completed or in-progress) to view detailed boxscores</p>
                    <p>• <strong>Standings:</strong> Navigate through NBA standings and playoff scenarios</p>

                    <h5 style="color: #1e40af; margin-bottom: 0.5rem; margin-top: 1.5rem;">🤖 Machine Learning Features</h5>
                    <p>Each player has ML models predicting their stats for next season (PTS, REB, AST, STL, BLK). Player bios classify them as star players, role players, or bench warmers based on performance analysis.</p>

                    <h5 style="color: #1e40af; margin-bottom: 0.5rem; margin-top: 1.5rem;">🎨 Additional Features</h5>
                    <p>• Toggle between light and dark themes</p>
                    <p>• Switch between regular season and playoff stat views</p>
                    <p>• Typeahead search with predictive suggestions</p>
                    <p>• Live scores and game updates via ESPN APIs</p>

                    <p style="margin-top: 1.5rem; padding: 0.75rem; background: #f8f9fa; border-radius: 6px; font-size: 0.9rem; color: #666;">
                        ⚠️ <strong>Note:</strong> Best viewed on laptops with 1920x1080 resolution. Performance optimized for standard laptop screens.
                    </p>
                </div>
            </div>

            <div id="helpOverlay" style="
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0,0,0,0.5);
                z-index: 999;
            " onclick="this.remove(); document.getElementById('helpModal').remove(); document.getElementById('helpBtn').classList.remove('active'); document.getElementById('helpModeIndicator').classList.remove('show');"></div>
        `;

        document.body.insertAdjacentHTML('beforeend', helpContent);
    }

    function hideHelpContent() {
        const helpModal = document.getElementById('helpModal');
        const helpOverlay = document.getElementById('helpOverlay');

        if (helpModal) helpModal.remove();
        if (helpOverlay) helpOverlay.remove();
    }

    // Close help on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && helpMode) {
            helpBtn.click();
        }
    });
});