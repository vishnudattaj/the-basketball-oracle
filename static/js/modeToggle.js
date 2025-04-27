document.addEventListener('DOMContentLoaded', function() {
    // Original theme toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    const darkTheme = document.getElementById('dark-theme');
    const lightTheme = document.getElementById('light-theme');

    // NBA toggle for regular/playoff stats
    const nbaToggle = document.querySelector('.theme-toggle:not(#themeToggle)');

    // Check if there are any meaningful playoff tables on the page
    const hasPlayoffTables = checkForMeaningfulPlayoffTables();

    // Hide the NBA toggle if there are no meaningful playoff tables
    if (nbaToggle && !hasPlayoffTables) {
        nbaToggle.style.display = 'none';
    }

    // Get theme from localStorage
    const savedTheme = localStorage.getItem('theme') || 'dark'; // Default to dark if not set

    // Get stats mode from localStorage (only if playoff tables exist)
    const savedStatsMode = hasPlayoffTables ? (localStorage.getItem('statsMode') || 'regular') : 'regular';

    // Apply the theme visually
    if (savedTheme === 'light') {
        themeToggle.classList.add('light');
        darkTheme.disabled = true;
        lightTheme.disabled = false;
        document.body.classList.add('light-mode');
    } else {
        themeToggle.classList.remove('light');
        darkTheme.disabled = false;
        lightTheme.disabled = true;
        document.body.classList.remove('light-mode');
    }

    // Apply stats mode visually (only if playoff tables exist)
    if (hasPlayoffTables && savedStatsMode === 'playoff' && nbaToggle) {
        nbaToggle.classList.add('playoff-mode');
        // Apply playoff mode styling
        applyStatsMode('playoff');
    } else if (hasPlayoffTables && nbaToggle) {
        nbaToggle.classList.remove('playoff-mode');
        // Apply regular season mode styling
        applyStatsMode('regular');
    }

    // Send the theme to the server immediately after login
    updateThemeOnServer(savedTheme);

    // Send the stats mode to the server (only if playoff tables exist)
    if (hasPlayoffTables) {
        updateStatsModeOnServer(savedStatsMode);
    }

    // Theme toggle click handler
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            themeToggle.classList.toggle('light');
            document.body.classList.toggle('light-mode');
            const isLightTheme = themeToggle.classList.contains('light');

            darkTheme.disabled = isLightTheme;
            lightTheme.disabled = !isLightTheme;

            localStorage.setItem('theme', isLightTheme ? 'light' : 'dark');

            // Send theme change to server
            updateThemeOnServer(isLightTheme ? 'light' : 'dark');
        });
    }

    // NBA stats toggle click handler (only if playoff tables exist)
    if (nbaToggle && hasPlayoffTables) {
        nbaToggle.addEventListener('click', function() {
            nbaToggle.classList.toggle('playoff-mode');
            const isPlayoffMode = nbaToggle.classList.contains('playoff-mode');

            // Update the stats mode visually
            applyStatsMode(isPlayoffMode ? 'playoff' : 'regular');

            // Save preference to localStorage
            localStorage.setItem('statsMode', isPlayoffMode ? 'playoff' : 'regular');

            // Send stats mode change to server
            updateStatsModeOnServer(isPlayoffMode ? 'playoff' : 'regular');
        });
    }

    // Function to check if there are any meaningful playoff tables on the page
    function checkForMeaningfulPlayoffTables() {
        const playerGrids = document.querySelectorAll('.playerGrid');
        let hasPlayoffTable = false;

        playerGrids.forEach(grid => {
            const playerTables = grid.querySelectorAll('.playerTable');

            // Look at the second playerTable (index 1) which should be playoffs
            if (playerTables.length > 1) {
                const playoffTable = playerTables[1];

                // Check if the table has meaningful content
                if (playoffTable && isTableMeaningful(playoffTable)) {
                    hasPlayoffTable = true;
                }
            }
        });

        return hasPlayoffTable;
    }

    // Function to check if a table has meaningful content (not empty or "No data")
    function isTableMeaningful(tableElement) {
        // Check for common empty table indicators
        const tableContent = tableElement.textContent.trim().toLowerCase();

        // If table is empty or contains typical "no data" messages
        if (tableContent === '' ||
            tableContent.includes('no data') ||
            tableContent.includes('no playoff') ||
            tableContent.includes('not available') ||
            tableContent.includes('no stats') ||
            (tableElement.querySelector('table') && tableElement.querySelector('table').rows.length <= 1)) {
            return false;
        }

        // Count actual data cells (td elements with content)
        const dataCells = tableElement.querySelectorAll('td');
        let nonEmptyCells = 0;

        dataCells.forEach(cell => {
            if (cell.textContent.trim() !== '') {
                nonEmptyCells++;
            }
        });

        // If we have fewer than 3 cells with content, table is likely empty
        return nonEmptyCells > 3;
    }

    // Function to update theme on server
    function updateThemeOnServer(theme) {
        fetch('/update_theme', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ theme: theme }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Theme updated on server:', data.theme);
        })
        .catch(error => {
            console.error('Error updating theme:', error);
        });
    }

    // Function to update stats mode on server
    function updateStatsModeOnServer(mode) {
        fetch('/update_stats_mode', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ mode: mode }),
        })
        .then(response => response.json())
        .then(data => {
            console.log('Stats mode updated on server:', data.mode);
        })
        .catch(error => {
            console.error('Error updating stats mode:', error);
        });
    }

    // Function to apply the stats mode visually
    function applyStatsMode(mode) {
        // Get all playerGrid containers
        const playerGrids = document.querySelectorAll('.playerGrid');

        playerGrids.forEach(grid => {
            const playerTables = grid.querySelectorAll('.playerTable');

            if (playerTables.length > 0) {
                // First playerTable is for regular season
                const regularTable = playerTables[0];
                regularTable.style.display = mode === 'regular' ? 'block' : 'none';

                // Second playerTable (if it exists) is for playoffs
                if (playerTables.length > 1) {
                    const playoffTable = playerTables[1];
                    // Only show playoff table if it has meaningful content
                    if (isTableMeaningful(playoffTable)) {
                        playoffTable.style.display = mode === 'playoff' ? 'block' : 'none';
                    } else {
                        // If playoff table is empty but we're in playoff mode,
                        // keep regular table visible with a message
                        if (mode === 'playoff') {
                            regularTable.style.display = 'block';

                            // Add "No playoff data" message if not already present
                            let noDataMsg = grid.querySelector('.no-playoff-data');
                            if (!noDataMsg) {
                                noDataMsg = document.createElement('div');
                                noDataMsg.className = 'no-playoff-data';
                                noDataMsg.textContent = 'No playoff statistics available';
                                noDataMsg.style.color = '#ff9800';
                                noDataMsg.style.fontWeight = 'bold';
                                noDataMsg.style.textAlign = 'center';
                                noDataMsg.style.padding = '10px';
                                noDataMsg.style.marginTop = '10px';
                                grid.insertBefore(noDataMsg, playoffTable);
                            }
                            noDataMsg.style.display = 'block';
                        } else {
                            // Hide the message in regular mode
                            const noDataMsg = grid.querySelector('.no-playoff-data');
                            if (noDataMsg) {
                                noDataMsg.style.display = 'none';
                            }
                        }
                    }
                }
            }
        });

        // Update the visual indicator for the toggle
        if (nbaToggle) {
            const sunIcon = nbaToggle.querySelector('.sun');
            const moonIcon = nbaToggle.querySelector('.moon');

            if (sunIcon && moonIcon) {
                if (mode === 'playoff') {
                    sunIcon.style.opacity = '0';
                    moonIcon.style.opacity = '1';
                } else {
                    sunIcon.style.opacity = '1';
                    moonIcon.style.opacity = '0';
                }

                updateModeIndicator(mode);
            }
        }

        function updateModeIndicator(mode) {
            let indicator = document.getElementById('statsIndicator');

            if (!indicator) {
                indicator = document.createElement('div');
                indicator.id = 'statsIndicator';
                indicator.style.position = 'fixed';
                indicator.style.bottom = '65px';
                indicator.style.left = '65px';
                indicator.style.padding = '5px 10px';
                indicator.style.borderRadius = '4px';
                indicator.style.fontSize = '12px';
                indicator.style.fontWeight = 'bold';
                indicator.style.zIndex = '1000';
                indicator.style.boxShadow = '0 1px 3px rgba(0,0,0,0.3)';
                document.body.appendChild(indicator);
            }

            if (mode === 'playoff') {
                indicator.textContent = 'Playoff Stats';
                indicator.style.backgroundColor = '#FFD700';
                indicator.style.color = '#000';
            } else {
                indicator.textContent = 'Regular Season';
                indicator.style.backgroundColor = '#17408B';
                indicator.style.color = '#fff';
            }
        }
    }
});