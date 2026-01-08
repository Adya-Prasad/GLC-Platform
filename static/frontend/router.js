import { requireAuth } from './auth.js';
import { renderBorrowerDashboard, renderLenderDashboard } from './dashboard.js';
import { renderApplicationForm, handleApplicationSubmit } from './applicationform.js';
import { renderApplications } from './applicationlist.js';
import { renderLoanAssets } from './loanassets.js';
import { renderAuditPage } from './audit.js';
import { renderDocs } from './docs.js';
import { renderLearn } from './learn.js';

const MENUS = {
    lender: [
        { id: 'dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6', label: 'Dashboard' },
        { id: 'apply', icon: 'M12 6v6m0 0v6m0-6h6m-6 0H6', label: 'New Application' },
        { id: 'applications', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2', label: 'All Applications' },
        { id: 'loan-assets', icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', label: 'Loan Assets' },
        { id: 'audit', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z', label: 'Audit Report' },
        { id: 'docs', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253', label: 'Docs' },
        { id: 'learn', icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z', label: 'Learn' }
    ],
    borrower: [
        { id: 'apply', icon: 'M12 6v6m0 0v6m0-6h6m-6 0H6', label: 'New Application' },
        { id: 'applications', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2', label: 'My Applications' },
        { id: 'loan-assets', icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', label: 'Loan Assets' },
        { id: 'audit', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z', label: 'Audit Report' },
        { id: 'docs', icon: 'M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253', label: 'Docs' },
        { id: 'learn', icon: 'M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z', label: 'Learn' }
    ]
};

let user = null;

export function initRouter() {
    user = requireAuth();
    if (!user) return; // redirect happens in requireAuth

    // Setup global navigation helpers
    window.navigateTo = navigateTo;
    window.viewApplication = viewApplication;
    window.handleApplicationSubmit = handleApplicationSubmit;
    window.filterApps = (val) => console.log("Filtering by", val); // Helper stub

    renderSidebar();

    // Initial Route
    const defaultPage = user.role === 'lender' ? 'dashboard' : 'applications';
    navigateTo(defaultPage);
}

function renderSidebar() {
    const items = MENUS[user.role] || MENUS.borrower;
    const nav = document.getElementById('nav-menu');
    nav.innerHTML = items.map(item => `
        <button onclick="window.navigateTo('${item.id}')" id="nav-${item.id}" class="w-full py-2 px-3 text-left rounded-lg flex items-center space-x-3 transition-colors text-sm text-gray-500 hover:text-green-700 font-medium my-1">
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${item.icon}"/></svg>
            <span>${item.label}</span>
        </button>
    `).join('');

    // Update Sidebar User Info
    document.getElementById('user-name').textContent = user.name;
    document.getElementById('user-role-display').textContent = user.role.charAt(0).toUpperCase() + user.role.slice(1);

    // Set avatar initial
    const avatarEl = document.getElementById('user-avatar');
    if (avatarEl) avatarEl.textContent = user.name.charAt(0).toUpperCase();
}

export async function navigateTo(page) {
    console.log("Navigating to:", page);
    const content = document.getElementById('page-content');
    if (!content) {
        console.error("Content area not found!");
        return;
    }
    const title = document.getElementById('page-title');

    // Update Active Nav State
    document.querySelectorAll('#nav-menu button').forEach(b => {
        b.classList.remove('text-green-700', 'font-bold');
        b.classList.add('text-gray-500', 'font-medium');
    });
    const activeBtn = document.getElementById(`nav-${page}`);
    if (activeBtn) {
        activeBtn.classList.remove('text-gray-500', 'font-medium');
        activeBtn.classList.add('text-green-700', 'font-bold');
    }

    content.innerHTML = '<div class="flex justify-center items-center h-64"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-green-700"></div></div>';

    try {
        switch (page) {
            case 'dashboard':
                title.textContent = 'Dashboard';
                content.innerHTML = user.role === 'lender' ? await renderLenderDashboard() : await renderBorrowerDashboard();
                break;
            case 'apply':
                title.textContent = 'New Application';
                content.innerHTML = renderApplicationForm();
                break;
            case 'applications':
                title.textContent = user.role === 'lender' ? 'All Applications' : 'My Applications';
                content.innerHTML = await renderApplications();
                break;
            case 'my-applications':
                title.textContent = 'My Applications';
                content.innerHTML = await renderApplications();
                break;
            case 'loan-assets':
                title.textContent = 'Loan Assets';
                content.innerHTML = await renderLoanAssets();
                break;
            case 'portfolio':
                title.textContent = 'Portfolio Analytics';
                // Using dashboard view for now, usually a diff view
                content.innerHTML = await renderLenderDashboard();
                break;
            case 'audit':
                title.textContent = 'Audit Detail';
                content.innerHTML = await renderAuditPage();
                break;
            case 'docs':
                title.textContent = 'Documentation';
                content.innerHTML = await renderDocs();
                break;
            case 'learn':
                title.textContent = 'Learning Center';
                content.innerHTML = await renderLearn();
                break;
            default:
                content.innerHTML = `<p>Page ${page} not found.</p>`;
        }
    } catch (e) {
        console.error(e);
        content.innerHTML = `<p class="text-red-500">Error loading page: ${e.message}</p>`;
    }
}

function viewApplication(id) {
    // Current stub
    alert(`Viewing details for application ${id}`);
}

// Navigation Helper for Audit
window.navigateToAudit = function (appId) {
    window.currentAuditAppId = appId; // global state for router param
    navigateTo('audit');
}
