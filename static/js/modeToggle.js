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
            const sun = nbaToggle.querySelector('.sun');
            const moon = nbaToggle.querySelector('.moon');
            if (sun && moon) {
                sun.style.opacity = mode === 'playoff' ? '0' : '1';
                moon.style.opacity = mode === 'playoff' ? '1' : '0';
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
    let isThinking = true;
    if (isThinking) {
        thinkingBtn.classList.add('active');
        searchStats.hidden = true;
        statsContainer.disabled = true;
        searchAI.hidden = false;
        AIContainer.disabled = false;
        modeText.classList.add('aiMode')
        modeText.classList.remove('statMode')
        modeText.innerText = "AI Mode"
        console.log('Initialized in thinking mode');
    }


    console.log('thinkingBtn:', thinkingBtn);

    if (thinkingBtn) {
        console.log('Elements found, adding click listener...');

        thinkingBtn.addEventListener('click', function() {
            console.log('Button clicked!');
            isThinking = !isThinking;

            console.log('isThinking:', isThinking);
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
            } else {
                thinkingBtn.classList.remove('active');
                searchStats.hidden = false;
                statsContainer.disabled = false;
                searchAI.hidden = true;
                AIContainer.disabled = true;
            }

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