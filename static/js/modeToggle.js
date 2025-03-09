// Add this to your base template or the templates used right after login
document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('themeToggle');
    const darkTheme = document.getElementById('dark-theme');
    const lightTheme = document.getElementById('light-theme');

    // Get theme from localStorage (this happens immediately after login)
    const savedTheme = localStorage.getItem('theme') || 'dark'; // Default to dark if not set

    // Apply the theme visually
    if (savedTheme === 'light') {
        toggle.classList.add('light');
        darkTheme.disabled = true;
        lightTheme.disabled = false;
    } else {
        toggle.classList.remove('light');
        darkTheme.disabled = false;
        lightTheme.disabled = true;
    }

    // Send the theme to the server immediately after login
    updateThemeOnServer(savedTheme);

    // The rest of your toggle click handler
    toggle.addEventListener('click', function() {
        toggle.classList.toggle('light');
        const isLightTheme = toggle.classList.contains('light');

        darkTheme.disabled = isLightTheme;
        lightTheme.disabled = !isLightTheme;

        localStorage.setItem('theme', isLightTheme ? 'light' : 'dark');

        // Send theme change to server
        updateThemeOnServer(isLightTheme ? 'light' : 'dark');
    });

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
});