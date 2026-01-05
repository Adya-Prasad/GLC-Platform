import { initRouter } from './router.js';
import { logout } from './auth.js';

// Expose logout globally for the sidebar button
window.logout = logout;

document.addEventListener('DOMContentLoaded', () => {
    initRouter();
});
