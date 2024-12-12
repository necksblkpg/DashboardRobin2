document.addEventListener('DOMContentLoaded', function() {
    const themeToggle = document.getElementById('theme-toggle');
    const htmlEl = document.documentElement;
    const themeIcon = document.getElementById('theme-icon');

    function setTheme(mode) {
        if (mode === 'dark') {
            htmlEl.classList.add('dark');
            localStorage.setItem('theme', 'dark');
            themeIcon.classList.remove('fa-sun');
            themeIcon.classList.add('fa-moon');
        } else {
            htmlEl.classList.remove('dark');
            localStorage.setItem('theme', 'light');
            themeIcon.classList.remove('fa-moon');
            themeIcon.classList.add('fa-sun');
        }
    }

    if (localStorage.getItem('theme') === 'dark') {
        setTheme('dark');
    } else {
        setTheme('light');
    }

    themeToggle.addEventListener('click', () => {
        if (htmlEl.classList.contains('dark')) {
            setTheme('light');
        } else {
            setTheme('dark');
        }
    });
});
