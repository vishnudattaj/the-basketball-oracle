document.addEventListener('DOMContentLoaded', function() {
    const returnButton = document.getElementById('returnToSearchButton');

    if (returnButton) {
        // Update the button text to be more accurate
        returnButton.textContent = 'Return to Previous';

        // Remove the existing onClick (which is set via the parent <a> tag)
        returnButton.parentElement.removeAttribute('href');

        // Add new event listener
        returnButton.addEventListener('click', function() {
            window.history.back();
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