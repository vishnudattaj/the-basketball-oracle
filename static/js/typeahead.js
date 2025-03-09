document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('player');
    const searchContainer = document.querySelector('.search-container');
    const searchIcon = searchContainer.querySelector('.fa-search');
    const searchForm = searchInput.closest('form');
    const searchButton = searchForm ? searchForm.querySelector('button[type="submit"][hidden]') : null;

    // Create dropdown element for suggestions
    const suggestionsDropdown = document.createElement('div');
    suggestionsDropdown.className = 'suggestions-dropdown';
    searchContainer.appendChild(suggestionsDropdown);

    // Variable to store players data
    let playersData = [];

    // Fetch players data from JSON file using a relative path
    fetch('./static/data/players.json')
        .then(response => response.json())
        .then(data => {
            playersData = data;
            console.log("Players data loaded:", playersData.slice(0, 2));
        })
        .catch(error => {
            console.error('Error loading players data:', error);
        });

    // Function to remove accents from text
    function removeAccents(str) {
        return str.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    }

    // Function to get the current input term
    function getCurrentInputTerm() {
        const fullInput = searchInput.value;
        const terms = fullInput.split(',');
        let currentTerm = terms[terms.length - 1].trim();
        return currentTerm;
    }

    // Function to submit the search form
    function submitSearch() {
        if (searchButton) {
            // Set the value attribute of the button to ensure proper form handling
            searchButton.value = "Submit";
            searchButton.click();
        }
    }

    // Improved function to filter players based on input - searches both first and last names
    // Now also compares unaccented versions of text
    function filterPlayers(input) {
        if (!input || input.length < 2) return [];

        const inputLower = input.toLowerCase();
        const inputLowerNoAccent = removeAccents(inputLower);

        return playersData
            .filter(player => {
                // Get player name based on data type
                let playerName;
                if (typeof player === 'string') {
                    playerName = player;
                } else if (player && typeof player === 'object') {
                    playerName = player.name || Object.values(player).find(val => typeof val === 'string');
                } else {
                    return false;
                }

                // Convert player name to lowercase and create unaccented version
                const playerNameLower = playerName.toLowerCase();
                const playerNameLowerNoAccent = removeAccents(playerNameLower);

                // Check if the unaccented input matches any part of the unaccented player name
                return playerNameLower.includes(inputLower) ||
                       playerNameLowerNoAccent.includes(inputLowerNoAccent);
            })
            .slice(0, 8); // Limit to 8 suggestions
    }

    // Function to render suggestions
    function renderSuggestions(suggestions) {
        suggestionsDropdown.innerHTML = '';

        if (suggestions.length === 0) {
            suggestionsDropdown.style.display = 'none';
            return;
        }

        suggestions.forEach(player => {
            const suggestionItem = document.createElement('div');
            suggestionItem.className = 'suggestion-item';

            // Get player name based on data structure
            const playerName = typeof player === 'string' ? player :
                              (player.name ? player.name : Object.values(player).find(val => typeof val === 'string'));

            // Get current term and create unaccented versions for matching
            const currentTerm = getCurrentInputTerm().toLowerCase();
            const currentTermNoAccent = removeAccents(currentTerm);
            const playerNameLower = playerName.toLowerCase();
            const playerNameLowerNoAccent = removeAccents(playerNameLower);

            // Try to find index in original text first
            let index = playerNameLower.indexOf(currentTerm);

            // If not found in original, try in unaccented version
            if (index < 0) {
                // Find match position in unaccented version
                index = playerNameLowerNoAccent.indexOf(currentTermNoAccent);
            }

            if (index >= 0) {
                const beforeMatch = playerName.substring(0, index);
                const match = playerName.substring(index, index + currentTerm.length);
                const afterMatch = playerName.substring(index + currentTerm.length);

                suggestionItem.innerHTML = `${beforeMatch}<strong>${match}</strong>${afterMatch}`;
            } else {
                suggestionItem.textContent = playerName;
            }

            suggestionItem.addEventListener('click', function() {
                // Get existing input up to the last comma
                const existingInput = searchInput.value;
                const lastCommaIndex = existingInput.lastIndexOf(',');

                if (lastCommaIndex === -1) {
                    // No comma yet, just set the value
                    searchInput.value = playerName;
                } else {
                    // Replace just the part after the last comma
                    const beforeComma = existingInput.substring(0, lastCommaIndex + 1);
                    searchInput.value = beforeComma + ' ' + playerName;
                }

                suggestionsDropdown.style.display = 'none';

                // Focus the input field again to continue typing
                searchInput.focus();
            });

            suggestionsDropdown.appendChild(suggestionItem);
        });

        suggestionsDropdown.style.display = 'block';
    }

    // Event listener for input changes
    searchInput.addEventListener('input', function() {
        const currentTerm = getCurrentInputTerm();
        const filteredPlayers = filterPlayers(currentTerm);
        renderSuggestions(filteredPlayers);
    });

    // Make search icon clickable to submit the search
    if (searchIcon) {
        searchIcon.style.cursor = 'pointer'; // Make it look clickable
        searchIcon.addEventListener('click', function() {
            if (suggestionsDropdown.style.display === 'block') {
                suggestionsDropdown.style.display = 'none';
            } else if (searchInput.value.trim() !== '') {
                submitSearch();
            }
        });
    }

    // Close suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!searchContainer.contains(e.target)) {
            suggestionsDropdown.style.display = 'none';
        }
    });

    // Navigate through suggestions with keyboard
    searchInput.addEventListener('keydown', function(e) {
        const suggestions = suggestionsDropdown.querySelectorAll('.suggestion-item');
        const currentActive = suggestionsDropdown.querySelector('.suggestion-item.active');
        let currentIndex = -1;

        if (currentActive) {
            currentIndex = Array.from(suggestions).indexOf(currentActive);
        }

        // Handle Enter key for form submission
        if (e.key === 'Enter') {
            // If dropdown is visible with an active suggestion
            if (suggestionsDropdown.style.display === 'block' && currentActive) {
                e.preventDefault();

                // Get existing input up to the last comma
                const existingInput = searchInput.value;
                const lastCommaIndex = existingInput.lastIndexOf(',');

                if (lastCommaIndex === -1) {
                    // No comma yet, just set the value
                    searchInput.value = currentActive.textContent.trim();
                } else {
                    // Replace just the part after the last comma
                    const beforeComma = existingInput.substring(0, lastCommaIndex + 1);
                    searchInput.value = beforeComma + ' ' + currentActive.textContent.trim();
                }

                suggestionsDropdown.style.display = 'none';
                searchInput.focus();
            }
            // If dropdown is visible but no suggestion is active, hide it
            else if (suggestionsDropdown.style.display === 'block') {
                e.preventDefault();
                suggestionsDropdown.style.display = 'none';
            }
            // If dropdown is not visible, submit the search
            else if (searchInput.value.trim() !== '') {
                e.preventDefault();
                submitSearch();
            }
        }

        // Down arrow
        else if (e.key === 'ArrowDown') {
            e.preventDefault();
            if (suggestions.length > 0) {
                if (currentActive) {
                    currentActive.classList.remove('active');
                }

                const nextIndex = currentIndex < suggestions.length - 1 ? currentIndex + 1 : 0;
                suggestions[nextIndex].classList.add('active');
            }
        }

        // Up arrow
        else if (e.key === 'ArrowUp') {
            e.preventDefault();
            if (suggestions.length > 0) {
                if (currentActive) {
                    currentActive.classList.remove('active');
                }

                const prevIndex = currentIndex > 0 ? currentIndex - 1 : suggestions.length - 1;
                suggestions[prevIndex].classList.add('active');
            }
        }

        // Escape key
        else if (e.key === 'Escape') {
            suggestionsDropdown.style.display = 'none';
        }
    });

    // Add a listener to the form to handle submission correctly
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            // If this is a search submission (not logout)
            if (e.submitter && e.submitter.value === "Submit") {
                // If the dropdown is visible, prevent submission
                if (suggestionsDropdown.style.display === 'block') {
                    e.preventDefault();
                    return;
                }

                if (searchInput.value.trim() === '') {
                    e.preventDefault();
                    return;
                }
            }
            // The form will submit naturally
        });
    }
});