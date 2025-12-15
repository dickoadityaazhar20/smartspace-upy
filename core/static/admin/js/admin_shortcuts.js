/**
 * SmartSpace Admin Keyboard Shortcuts
 * Custom keyboard shortcuts for Django Unfold Admin
 */

document.addEventListener('DOMContentLoaded', function () {

    // Define URL mappings for shortcuts
    const shortcuts = {
        'd': '/admin/',                          // Dashboard
        'u': '/admin/core/user/',                // Users
        'r': '/admin/core/room/',                // Ruangan
        'p': '/admin/core/booking/',             // Peminjaman
        'w': '/admin/core/wishlist/',            // Wishlist
        'c': '/admin/chat/',                     // Chat User
        't': '/admin/core/testimonial/',         // Testimoni
        'a': '/admin/shortcuts/',                // Admin Shortcut
    };

    // Listen for keydown events
    document.addEventListener('keydown', function (e) {
        // Ignore if user is typing in an input field
        const activeElement = document.activeElement;
        const isTyping = activeElement.tagName === 'INPUT' ||
            activeElement.tagName === 'TEXTAREA' ||
            activeElement.isContentEditable;

        if (isTyping) return;

        const key = e.key.toLowerCase();

        // Handle 's' for SIDEBAR search (left - "Search apps and model...")
        if (key === 's') {
            e.preventDefault();
            // Find the sidebar search input specifically
            const sidebarSearch = document.querySelector('aside input[type="text"]') ||
                document.querySelector('nav input[type="text"]') ||
                document.querySelector('input[placeholder*="Search apps"]') ||
                document.querySelector('input[placeholder*="apps and model"]');
            if (sidebarSearch) {
                sidebarSearch.focus();
            }
            return;
        }

        // Handle '/' for CHANGELIST search (right - "Type to search")
        if (key === '/') {
            e.preventDefault();
            // Find the table/changelist search input
            const changelistSearch = document.querySelector('input[name="q"]') ||
                document.querySelector('input[placeholder*="Type to search"]') ||
                document.querySelector('input[placeholder*="type to search"]') ||
                document.querySelector('main input[type="text"]');
            if (changelistSearch) {
                changelistSearch.focus();
            }
            return;
        }

        // Handle navigation shortcuts (d, u, r, p, w, c, t)
        if (shortcuts[key]) {
            e.preventDefault();
            window.location.href = shortcuts[key];
            return;
        }
    });

    // Update the search shortcut hints
    function updateSearchHints() {
        // Find all kbd elements and update hints
        const allKbd = document.querySelectorAll('kbd');
        allKbd.forEach(function (kbd) {
            const text = kbd.textContent.trim().toLowerCase();
            // Change 't' to 's' for sidebar search
            if (text === 't') {
                // Check if this is in sidebar area
                const inSidebar = kbd.closest('aside') || kbd.closest('nav') ||
                    kbd.closest('[class*="sidebar"]');
                if (inSidebar) {
                    kbd.textContent = 's';
                }
            }
        });
    }

    // Run after a short delay to ensure DOM is fully loaded
    setTimeout(updateSearchHints, 100);
    setTimeout(updateSearchHints, 500);

    console.log('%c⌨️ SmartSpace Shortcuts Active', 'color: #3B82F6; font-weight: bold;');
    console.log('S=Sidebar Search, /=Table Search, D=Dashboard, U=Users, R=Ruangan, P=Peminjaman, W=Wishlist, C=Chat, T=Testimoni');
});
