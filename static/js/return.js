document.addEventListener('DOMContentLoaded', function() {
    const returnButton = document.getElementById('returnToSearchButton');

    // Initialize or retrieve our custom history stack from sessionStorage
    let customHistory = JSON.parse(sessionStorage.getItem('customPageHistory') || '[]');
    const currentUrl = window.location.href;

    // Check if we're on the exact protected route
    // Parse the URL and check if the pathname is exactly "/protected"
    const urlObj = new URL(currentUrl);
    const isExactProtectedRoute = urlObj.pathname === '/protected';

    // If on the exact protected route, clear history
    if (isExactProtectedRoute) {
        sessionStorage.removeItem('customPageHistory');
        customHistory = [currentUrl];
    }
    // Otherwise add current page to history if not already the last page visited
    else if (customHistory.length === 0 || customHistory[customHistory.length - 1] !== currentUrl) {
        customHistory.push(currentUrl);
    }

    // Save updated history
    sessionStorage.setItem('customPageHistory', JSON.stringify(customHistory));

    if (returnButton) {
        // Update the button text
        returnButton.textContent = 'Return to Previous';

        // Remove existing href
        returnButton.parentElement.removeAttribute('href');

        // Add custom history navigation
        returnButton.addEventListener('click', function() {
            // Get the latest history
            let history = JSON.parse(sessionStorage.getItem('customPageHistory') || '[]');

            if (isExactProtectedRoute) {
                // If on exact protected route, simply reload
                window.location.reload();
            }
            else if (history.length > 1) {
                // Remove current page from history
                history.pop();

                // Get previous page
                const previousUrl = history[history.length - 1];

                // Save updated history without current page
                sessionStorage.setItem('customPageHistory', JSON.stringify(history));

                // Navigate to previous page
                window.location.href = previousUrl;
            }
            else {
                // Fallback to base protected route if no history
                sessionStorage.removeItem('customPageHistory');
                window.location.href = '/protected';
            }
        });
    }

    // Keep the Enter key functionality
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            if (returnButton) {
                returnButton.click();
            }
        }
    });
});