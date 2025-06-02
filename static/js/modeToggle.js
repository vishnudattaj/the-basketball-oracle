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

        indicator.textContent = mode === 'playoff' ? 'Playoff Stats' : 'Regular Season';
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

    function updateThemeOnServer(theme) {
        fetch('/update_theme', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ theme })
        }).then(res => res.json())
          .then(data => console.log('Theme updated:', data.theme))
          .catch(console.error);
    }

    function updateStatsModeOnServer(mode) {
        fetch('/update_stats_mode', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode })
        }).then(res => res.json())
          .then(data => console.log('Stats mode updated:', data.mode))
          .catch(console.error);
    }
});
