document.addEventListener('DOMContentLoaded', function() {
    const toggle = document.getElementById('themeToggle');
    const darkTheme = document.getElementById('dark-theme');
    const lightTheme = document.getElementById('light-theme');

    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        toggle.classList.add('light');
        darkTheme.disabled = true;
        lightTheme.disabled = false;
    }

    toggle.addEventListener('click', function() {
        toggle.classList.toggle('light');
        const isLightTheme = toggle.classList.contains('light');

        darkTheme.disabled = isLightTheme;
        lightTheme.disabled = !isLightTheme;

        localStorage.setItem('theme', isLightTheme ? 'light' : 'dark');
    });
});