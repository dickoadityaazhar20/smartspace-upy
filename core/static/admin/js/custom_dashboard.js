/**
 * SmartSpace UPY - Custom Dashboard JavaScript
 */

document.addEventListener('DOMContentLoaded', function () {
    // Theme Toggle
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function () {
            document.documentElement.classList.toggle('light');
            const icon = this.querySelector('.material-icons-outlined');
            icon.textContent = document.documentElement.classList.contains('light') ? 'light_mode' : 'dark_mode';
        });
    }

    // Global Search
    const globalSearch = document.getElementById('globalSearch');
    if (globalSearch) {
        globalSearch.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') {
                const query = this.value.trim();
                if (query) {
                    // Redirect to admin search
                    window.location.href = `/smartspace-panel-upy/core/booking/?q=${encodeURIComponent(query)}`;
                }
            }
        });
    }

    // Animate numbers on load
    animateNumbers();
});

function animateNumbers() {
    const statValues = document.querySelectorAll('.stat-value');
    statValues.forEach(el => {
        const finalValue = parseInt(el.textContent) || 0;
        let currentValue = 0;
        const duration = 1000;
        const step = finalValue / (duration / 16);

        const animate = () => {
            currentValue += step;
            if (currentValue < finalValue) {
                el.textContent = Math.floor(currentValue);
                requestAnimationFrame(animate);
            } else {
                el.textContent = finalValue;
            }
        };

        if (finalValue > 0) {
            el.textContent = '0';
            requestAnimationFrame(animate);
        }
    });
}
