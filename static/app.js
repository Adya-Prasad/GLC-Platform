// GLC Platform Frontend Application
const API_BASE = '/api/v1';
let currentUser = null;
let currentPage = 'dashboard';

// Menu configurations
const MENUS = {
    borrower: [
        { id: 'dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6', label: 'Dashboard' },
        { id: 'apply', icon: 'M12 6v6m0 0v6m0-6h6m-6 0H6', label: 'New Application' },
        { id: 'my-applications', icon: 'M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', label: 'My Applications' },
        { id: 'documents', icon: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z', label: 'Documents' }
    ],
    lender: [
        { id: 'dashboard', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6', label: 'Dashboard' },
        { id: 'applications', icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2', label: 'Applications' },
        { id: 'portfolio', icon: 'M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z', label: 'Portfolio' },
        { id: 'reports', icon: 'M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z', label: 'Reports' },
        { id: 'audit', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z', label: 'Audit Trail' }
    ]
};

// Login function
async function login(role) {
    try {
        const res = await fetch(`${API_BASE}/auth/login?role=${role}`);
        currentUser = await res.json();
        localStorage.setItem('glc_user', JSON.stringify(currentUser));
        showMainApp();
    } catch (e) {
        currentUser = { name: `Demo ${role}`, role, token: 'demo' };
        localStorage.setItem('glc_user', JSON.stringify(currentUser));
        showMainApp();
    }
}

// Auth check
if (!localStorage.getItem('glc_user')) {
    window.location.href = '/login';
}

function logout() {
    localStorage.removeItem('glc_user');
    currentUser = null;
    window.location.href = '/login';
}

function showMainApp() {
    // Auth screen logic moved to separate page
    document.getElementById('user-role-display').textContent = currentUser.role.charAt(0).toUpperCase() + currentUser.role.slice(1);
    document.getElementById('user-name').textContent = currentUser.name;
    renderMenu();
    navigateTo('dashboard');
}

function renderMenu() {
    const menu = MENUS[currentUser.role] || MENUS.borrower;
    const nav = document.getElementById('nav-menu');
    nav.innerHTML = menu.map(item => `
        <button onclick="navigateTo('${item.id}')" id="nav-${item.id}" class="w-full py-2 px-3 text-left rounded-lg flex items-center space-x-3 transition-colors text-sm text-gray-500 hover:text-green-700 font-medium">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${item.icon}"/></svg>
            <span>${item.label}</span>
        </button>
    `).join('');
}

function navigateTo(page) {
    currentPage = page;
    document.querySelectorAll('#nav-menu button').forEach(b => {
        b.classList.remove('text-green-700', 'font-bold');
        b.classList.add('text-gray-500', 'font-medium');
    });
    const activeBtn = document.getElementById(`nav-${page}`);
    if (activeBtn) {
        activeBtn.classList.add('text-green-700', 'font-bold');
        activeBtn.classList.remove('text-gray-500', 'font-medium');
    }
    renderPage(page);
}

async function renderPage(page) {
    const content = document.getElementById('page-content');
    const title = document.getElementById('page-title');

    const pages = {
        'dashboard': () => currentUser.role === 'lender' ? renderLenderDashboard() : renderBorrowerDashboard(),
        'apply': renderApplyForm,
        'my-applications': renderMyApplications,
        'documents': renderDocuments,
        'applications': renderAllApplications,
        'portfolio': renderPortfolio,
        'reports': renderReports,
        'audit': renderAuditTrail
    };

    const titles = {
        'dashboard': 'Dashboard', 'apply': 'New Loan Application', 'my-applications': 'My Applications',
        'documents': 'Documents', 'applications': 'All Applications', 'portfolio': 'Portfolio Overview',
        'reports': 'Reports', 'audit': 'Audit Trail'
    };

    title.textContent = titles[page] || 'Dashboard';
    content.innerHTML = '<div class="flex justify-center py-20"><div class="animate-spin w-8 h-8 border-4 border-glc-green-500 border-t-transparent rounded-full"></div></div>';

    if (pages[page]) {
        content.innerHTML = await pages[page]();
    }
}

// Dashboard Renderers
async function renderBorrowerDashboard() {
    let apps = [];
    try {
        const res = await fetch(`${API_BASE}/borrower/applications`, { headers: { 'Authorization': `Bearer ${currentUser.token}` } });
        apps = await res.json();
    } catch (e) { }

    const stats = [
        { label: 'Total Applications', value: apps.length, color: 'blue' },
        { label: 'Approved', value: apps.filter(a => a.status === 'approved').length, color: 'green' },
        { label: 'Pending', value: apps.filter(a => ['submitted', 'under_review'].includes(a.status)).length, color: 'yellow' },
        { label: 'ESG Score Avg', value: apps.length ? Math.round(apps.reduce((s, a) => s + (a.esg_score || 0), 0) / apps.length) : 0, color: 'purple' }
    ];

    return `
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            ${stats.map(s => `<div class="bg-white rounded-2xl p-6 shadow-sm card-hover"><p class="text-gray-400 text-sm">${s.label}</p><p class="text-3xl font-bold text-[var(--green)] mt-2">${s.value}</p></div>`).join('')}
        </div>
        <div class="bg-white rounded-2xl p-6 shadow-sm">
            <div class="flex justify-between items-center mb-6"><h3 class="text-lg font-semibold">Recent Applications</h3><button onclick="navigateTo('apply')" class="bg-[var(--green)] text-white px-4 py-2 rounded-lg hover:opacity-90 transition-all">+ New Application</button></div>
            ${apps.length ? `<div class="overflow-x-auto"><table class="w-full"><thead><tr class="text-left text-gray-400 text-sm border-b"><th class="pb-4">Project</th><th class="pb-4">Sector</th><th class="pb-4">Amount</th><th class="pb-4">Status</th><th class="pb-4">ESG</th></tr></thead><tbody>${apps.slice(0, 5).map(a => `<tr class="border-b border-gray-100 hover:bg-gray-50"><td class="py-4 font-medium">${a.project_name}</td><td class="py-4">${a.sector}</td><td class="py-4">${a.currency} ${(a.amount_requested / 1e6).toFixed(1)}M</td><td class="py-4"><span class="px-3 py-1 rounded-full text-xs ${getStatusClass(a.status)}">${a.status}</span></td><td class="py-4"><span class="font-semibold ${a.esg_score >= 70 ? 'text-green-600' : 'text-yellow-600'}">${a.esg_score || '-'}</span></td></tr>`).join('')}</tbody></table></div>` : '<p class="text-gray-400 text-center py-8">No applications yet. Click "New Application" to get started.</p>'}
        </div>`;
}

async function renderLenderDashboard() {
    let portfolio = { total_applications: 0, num_approved: 0, num_pending: 0, avg_esg_score: 0, total_financed_co2: 0, percent_eligible_green: 0 };
    try {
        const res = await fetch(`${API_BASE}/lender/portfolio/summary`, { headers: { 'Authorization': `Bearer ${currentUser.token}` } });
        portfolio = await res.json();
    } catch (e) { }

    return `
        <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            <div class="bg-white rounded-2xl p-5 shadow-sm"><p class="text-gray-400 text-xs">Total Apps</p><p class="text-2xl font-bold text-[var(--green)]">${portfolio.total_applications}</p></div>
            <div class="bg-white rounded-2xl p-5 shadow-sm"><p class="text-gray-400 text-xs">Approved</p><p class="text-2xl font-bold text-green-600">${portfolio.num_approved}</p></div>
            <div class="bg-white rounded-2xl p-5 shadow-sm"><p class="text-gray-400 text-xs">Pending</p><p class="text-2xl font-bold text-yellow-600">${portfolio.num_pending}</p></div>
            <div class="bg-white rounded-2xl p-5 shadow-sm"><p class="text-gray-400 text-xs">Avg ESG</p><p class="text-2xl font-bold text-purple-600">${portfolio.avg_esg_score}</p></div>
            <div class="bg-white rounded-2xl p-5 shadow-sm"><p class="text-gray-400 text-xs">Financed CO₂</p><p class="text-2xl font-bold text-orange-600">${(portfolio.total_financed_co2 / 1000).toFixed(0)}k</p></div>
            <div class="bg-white rounded-2xl p-5 shadow-sm"><p class="text-gray-400 text-xs">Green %</p><p class="text-2xl font-bold text-[var(--green)]">${portfolio.percent_eligible_green?.toFixed(0) || 0}%</p></div>
        </div>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-white rounded-2xl p-6 shadow-sm"><h3 class="font-semibold mb-4">Quick Actions</h3>
                <div class="space-y-3">
                    <button onclick="navigateTo('applications')" class="w-full py-3 px-4 bg-green-50 hover:bg-green-100 text-green-700 rounded-xl text-left flex items-center justify-between transition-colors">Review Applications <span>→</span></button>
                    <button onclick="navigateTo('portfolio')" class="w-full py-3 px-4 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-xl text-left flex items-center justify-between transition-colors">View Portfolio <span>→</span></button>
                </div>
            </div>
            <div class="bg-white rounded-2xl p-6 shadow-sm"><h3 class="font-semibold mb-4">Sector Distribution</h3>
                <div class="space-y-2">${Object.entries(portfolio.sector_breakdown || {}).map(([k, v]) => `<div class="flex justify-between items-center"><span class="text-sm">${k}</span><span class="bg-green-100 text-green-700 px-2 py-1 rounded text-xs">${v}</span></div>`).join('') || '<p class="text-gray-400">No data</p>'}</div>
            </div>
        </div>`;
}

function renderApplyForm() {
    return `
        <div class="max-w-3xl mx-auto bg-white rounded-2xl p-8 shadow-sm fade-in">
            <form id="apply-form" onsubmit="submitApplication(event)" class="space-y-6">
                <div class="grid grid-cols-2 gap-4">
                    <div><label class="block text-sm font-medium text-glc-zinc-400 mb-2">Organization Name *</label><input name="org_name" required class="w-full px-4 py-3 border border-glc-zinc-200 rounded-xl focus:ring-2 focus:ring-glc-green-500 focus:border-transparent" placeholder="ACME Renewables Ltd"></div>
                    <div><label class="block text-sm font-medium text-glc-zinc-400 mb-2">Project Name *</label><input name="project_name" required class="w-full px-4 py-3 border border-glc-zinc-200 rounded-xl focus:ring-2 focus:ring-glc-green-500" placeholder="Wind Farm Project X"></div>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div><label class="block text-sm font-medium text-glc-zinc-400 mb-2">Sector *</label><select name="sector" required class="w-full px-4 py-3 border border-glc-zinc-200 rounded-xl"><option>Renewable Energy</option><option>Energy Efficiency</option><option>Clean Transportation</option><option>Green Buildings</option><option>Sustainable Water Management</option><option>Pollution Prevention</option></select></div>
                    <div><label class="block text-sm font-medium text-glc-zinc-400 mb-2">Location *</label><input name="location" required class="w-full px-4 py-3 border border-glc-zinc-200 rounded-xl" placeholder="Madrid, Spain"></div>
                </div>
                <div class="grid grid-cols-3 gap-4">
                    <div><label class="block text-sm font-medium text-glc-zinc-400 mb-2">Amount (USD) *</label><input name="amount_requested" type="number" required class="w-full px-4 py-3 border border-glc-zinc-200 rounded-xl" placeholder="120000000"></div>
                    <div><label class="block text-sm font-medium text-glc-zinc-400 mb-2">Currency</label><select name="currency" class="w-full px-4 py-3 border border-glc-zinc-200 rounded-xl"><option>USD</option><option>EUR</option><option>GBP</option></select></div>
                    <div><label class="block text-sm font-medium text-glc-zinc-400 mb-2">Project Type</label><select name="project_type" class="w-full px-4 py-3 border border-glc-zinc-200 rounded-xl"><option>New</option><option>Existing</option></select></div>
                </div>
                <div><label class="block text-sm font-medium text-glc-zinc-400 mb-2">Use of Proceeds *</label><textarea name="use_of_proceeds" required rows="3" class="w-full px-4 py-3 border border-glc-zinc-200 rounded-xl" placeholder="Describe how the loan proceeds will be used..."></textarea></div>
                <div class="bg-glc-green-50 rounded-xl p-4"><h4 class="font-semibold text-glc-green-800 mb-4">Carbon Emissions (tCO₂)</h4>
                    <div class="grid grid-cols-4 gap-4">
                        <div><label class="text-xs text-glc-zinc-400">Scope 1</label><input name="scope1_tco2" type="number" class="w-full px-3 py-2 border rounded-lg" placeholder="25000"></div>
                        <div><label class="text-xs text-glc-zinc-400">Scope 2</label><input name="scope2_tco2" type="number" class="w-full px-3 py-2 border rounded-lg" placeholder="10000"></div>
                        <div><label class="text-xs text-glc-zinc-400">Scope 3</label><input name="scope3_tco2" type="number" class="w-full px-3 py-2 border rounded-lg" placeholder="5000"></div>
                        <div><label class="text-xs text-glc-zinc-400">Baseline Year</label><input name="baseline_year" type="number" class="w-full px-3 py-2 border rounded-lg" placeholder="2023"></div>
                    </div>
                </div>
                <button type="submit" class="w-full py-4 bg-glc-green-500 hover:bg-glc-green-600 text-white rounded-xl font-semibold transition-all">Submit Application</button>
            </form>
        </div>`;
}

async function submitApplication(e) {
    e.preventDefault();
    const form = e.target;
    const data = Object.fromEntries(new FormData(form));
    data.amount_requested = parseFloat(data.amount_requested);
    data.scope1_tco2 = parseFloat(data.scope1_tco2) || null;
    data.scope2_tco2 = parseFloat(data.scope2_tco2) || null;
    data.scope3_tco2 = parseFloat(data.scope3_tco2) || null;
    data.baseline_year = parseInt(data.baseline_year) || null;

    try {
        const res = await fetch(`${API_BASE}/borrower/apply`, {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentUser.token}` },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if (res.ok) {
            alert(`Application submitted! ID: ${result.id}`);
            navigateTo('my-applications');
        } else {
            alert('Error: ' + JSON.stringify(result.detail));
        }
    } catch (e) { alert('Error submitting application'); }
}

async function renderMyApplications() {
    let apps = [];
    try {
        const res = await fetch(`${API_BASE}/borrower/applications`, { headers: { 'Authorization': `Bearer ${currentUser.token}` } });
        apps = await res.json();
    } catch (e) { }
    return renderApplicationsTable(apps, true);
}

async function renderAllApplications() {
    let apps = [];
    try {
        const res = await fetch(`${API_BASE}/lender/applications`, { headers: { 'Authorization': `Bearer ${currentUser.token}` } });
        apps = await res.json();
    } catch (e) { }
    return renderApplicationsTable(apps, false);
}

function renderApplicationsTable(apps, isBorrower) {
    if (!apps.length) return '<div class="bg-white rounded-2xl p-12 text-center text-glc-zinc-400">No applications found</div>';
    return `<div class="bg-white rounded-2xl shadow-sm overflow-hidden"><table class="w-full"><thead class="bg-glc-zinc-50"><tr class="text-left text-sm text-glc-zinc-400"><th class="p-4">Project</th><th class="p-4">${isBorrower ? 'Sector' : 'Borrower'}</th><th class="p-4">Amount</th><th class="p-4">Status</th><th class="p-4">ESG</th><th class="p-4">GLP</th><th class="p-4">Actions</th></tr></thead><tbody>${apps.map(a => `<tr class="border-b border-glc-zinc-100 hover:bg-glc-zinc-50"><td class="p-4 font-medium">${a.project_name}</td><td class="p-4">${isBorrower ? a.sector : (a.org_name || a.borrower_name || '-')}</td><td class="p-4">${a.currency} ${(a.amount_requested / 1e6).toFixed(1)}M</td><td class="p-4"><span class="px-3 py-1 rounded-full text-xs ${getStatusClass(a.status)}">${a.status}</span></td><td class="p-4 font-semibold ${(a.esg_score || 0) >= 70 ? 'text-glc-green-600' : 'text-yellow-600'}">${a.esg_score || '-'}</td><td class="p-4">${a.glp_eligibility ? '<span class="text-glc-green-600">✓</span>' : '<span class="text-glc-zinc-400">-</span>'}</td><td class="p-4"><button onclick="viewApplication(${a.id})" class="text-glc-green-600 hover:underline">View</button></td></tr>`).join('')}</tbody></table></div>`;
}

async function viewApplication(id) {
    const endpoint = currentUser.role === 'lender' ? `${API_BASE}/lender/application/${id}` : `${API_BASE}/borrower/application/${id}`;
    try {
        const res = await fetch(endpoint, { headers: { 'Authorization': `Bearer ${currentUser.token}` } });
        const data = await res.json();
        showApplicationModal(data);
    } catch (e) { alert('Error loading application'); }
}

function showApplicationModal(data) {
    const app = data.loan_app || data;
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4';
    modal.onclick = e => { if (e.target === modal) modal.remove(); };
    modal.innerHTML = `<div class="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto p-8">
        <div class="flex justify-between items-start mb-6"><h2 class="text-2xl font-bold">${app.project_name}</h2><button onclick="this.closest('.fixed').remove()" class="text-glc-zinc-400 hover:text-glc-zinc-600 text-2xl">&times;</button></div>
        <div class="grid grid-cols-2 gap-6 mb-6">
            <div><p class="text-sm text-glc-zinc-400">Sector</p><p class="font-medium">${app.sector}</p></div>
            <div><p class="text-sm text-glc-zinc-400">Location</p><p class="font-medium">${app.location}</p></div>
            <div><p class="text-sm text-glc-zinc-400">Amount</p><p class="font-medium">${app.currency} ${(app.amount_requested / 1e6).toFixed(2)}M</p></div>
            <div><p class="text-sm text-glc-zinc-400">Status</p><p><span class="px-3 py-1 rounded-full text-xs ${getStatusClass(app.status)}">${app.status}</span></p></div>
        </div>
        <div class="bg-glc-zinc-50 rounded-xl p-4 mb-6"><h4 class="font-semibold mb-2">Use of Proceeds</h4><p class="text-sm">${app.use_of_proceeds || 'N/A'}</p></div>
        <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="bg-glc-green-50 rounded-xl p-4 text-center"><p class="text-xs text-glc-zinc-400">ESG Score</p><p class="text-3xl font-bold text-glc-green-600">${app.esg_score || '-'}</p></div>
            <div class="rounded-xl p-4 text-center ${app.glp_eligibility ? 'bg-green-50' : 'bg-yellow-50'}"><p class="text-xs text-glc-zinc-400">GLP Eligible</p><p class="text-xl font-bold ${app.glp_eligibility ? 'text-green-600' : 'text-yellow-600'}">${app.glp_eligibility ? 'Yes' : 'No'}</p><p class="text-xs">${app.glp_category || ''}</p></div>
            <div class="rounded-xl p-4 text-center ${app.carbon_lockin_risk === 'high' ? 'bg-red-50' : 'bg-green-50'}"><p class="text-xs text-glc-zinc-400">Carbon Risk</p><p class="text-xl font-bold ${app.carbon_lockin_risk === 'high' ? 'text-red-600' : 'text-green-600'}">${app.carbon_lockin_risk || 'Low'}</p></div>
        </div>
        <div class="bg-glc-zinc-50 rounded-xl p-4 mb-6"><h4 class="font-semibold mb-2">Emissions Profile</h4><div class="grid grid-cols-4 gap-4 text-center"><div><p class="text-xs text-glc-zinc-400">Scope 1</p><p class="font-medium">${app.scope1_tco2?.toLocaleString() || '-'}</p></div><div><p class="text-xs text-glc-zinc-400">Scope 2</p><p class="font-medium">${app.scope2_tco2?.toLocaleString() || '-'}</p></div><div><p class="text-xs text-glc-zinc-400">Scope 3</p><p class="font-medium">${app.scope3_tco2?.toLocaleString() || '-'}</p></div><div><p class="text-xs text-glc-zinc-400">Total</p><p class="font-bold">${app.total_tco2?.toLocaleString() || '-'}</p></div></div></div>
        ${currentUser.role === 'lender' ? `<div class="flex gap-3"><button onclick="runIngestion(${app.id})" class="flex-1 py-3 bg-blue-500 hover:bg-blue-600 text-white rounded-xl">Run Analysis</button><button onclick="verifyApp(${app.id}, 'pass')" class="flex-1 py-3 bg-glc-green-500 hover:bg-glc-green-600 text-white rounded-xl">Approve</button><button onclick="verifyApp(${app.id}, 'fail')" class="flex-1 py-3 bg-red-500 hover:bg-red-600 text-white rounded-xl">Reject</button><button onclick="generateReport(${app.id})" class="flex-1 py-3 bg-purple-500 hover:bg-purple-600 text-white rounded-xl">Report</button></div>` : ''}
    </div>`;
    document.body.appendChild(modal);
}

async function runIngestion(id) {
    try {
        const res = await fetch(`${API_BASE}/ingest/run/${id}`, { method: 'POST', headers: { 'Authorization': `Bearer ${currentUser.token}` } });
        const result = await res.json();
        alert(`Analysis complete!\nESG Score: ${result.esg_score}\nGLP Category: ${result.glp_category}\nDocuments: ${result.documents_processed}`);
        document.querySelector('.fixed')?.remove();
        navigateTo('applications');
    } catch (e) { alert('Error running analysis'); }
}

async function verifyApp(id, result) {
    try {
        const res = await fetch(`${API_BASE}/lender/application/${id}/verify`, {
            method: 'POST', headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${currentUser.token}` },
            body: JSON.stringify({ verifier_role: 'lender', result, notes: '' })
        });
        if (res.ok) {
            alert(`Application ${result === 'pass' ? 'approved' : 'rejected'}!`);
            document.querySelector('.fixed')?.remove();
            navigateTo('applications');
        }
    } catch (e) { alert('Error updating status'); }
}

async function generateReport(id) {
    window.open(`${API_BASE}/report/application/${id}?format=json`, '_blank');
}

async function renderDocuments() {
    return '<div class="bg-white rounded-2xl p-8 text-center text-glc-zinc-400">Select an application to view and upload documents</div>';
}

async function renderPortfolio() {
    let data = {};
    try {
        const res = await fetch(`${API_BASE}/lender/portfolio/summary`, { headers: { 'Authorization': `Bearer ${currentUser.token}` } });
        data = await res.json();
    } catch (e) { }
    return `<div class="grid grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div class="bg-white rounded-2xl p-6 shadow-sm"><p class="text-glc-zinc-400 text-sm">Total Financed</p><p class="text-2xl font-bold text-glc-green-600">$${(data.total_financed_amount / 1e6 || 0).toFixed(1)}M</p></div>
        <div class="bg-white rounded-2xl p-6 shadow-sm"><p class="text-glc-zinc-400 text-sm">Financed CO₂</p><p class="text-2xl font-bold text-orange-600">${((data.total_financed_co2 || 0) / 1000).toFixed(1)}k tCO₂</p></div>
        <div class="bg-white rounded-2xl p-6 shadow-sm"><p class="text-glc-zinc-400 text-sm">Green Projects</p><p class="text-2xl font-bold text-glc-green-600">${data.num_green_projects || 0}</p></div>
        <div class="bg-white rounded-2xl p-6 shadow-sm"><p class="text-glc-zinc-400 text-sm">Flagged (High Risk)</p><p class="text-2xl font-bold text-red-600">${data.flagged_count || 0}</p></div>
    </div>
    <div class="bg-white rounded-2xl p-6 shadow-sm"><h3 class="font-semibold mb-4">Status Breakdown</h3>
        <div class="grid grid-cols-5 gap-4">${Object.entries(data.status_breakdown || {}).map(([k, v]) => `<div class="text-center p-4 bg-glc-zinc-50 rounded-xl"><p class="text-2xl font-bold">${v}</p><p class="text-xs text-glc-zinc-400">${k}</p></div>`).join('')}</div>
    </div>`;
}

async function renderReports() {
    return '<div class="bg-white rounded-2xl p-8"><h3 class="font-semibold mb-4">Generate Reports</h3><p class="text-glc-zinc-400 mb-4">Select an application to generate GLP investor reports.</p><button onclick="navigateTo(\'applications\')" class="bg-glc-green-500 text-white px-6 py-3 rounded-xl hover:bg-glc-green-600">View Applications</button></div>';
}

async function renderAuditTrail() {
    let logs = [];
    try {
        const res = await fetch(`${API_BASE}/audit?limit=50`, { headers: { 'Authorization': `Bearer ${currentUser.token}` } });
        logs = await res.json();
    } catch (e) { }
    if (!logs.length) return '<div class="bg-white rounded-2xl p-8 text-center text-glc-zinc-400">No audit logs yet</div>';
    return `<div class="bg-white rounded-2xl shadow-sm overflow-hidden"><table class="w-full"><thead class="bg-glc-zinc-50"><tr class="text-left text-sm text-glc-zinc-400"><th class="p-4">Timestamp</th><th class="p-4">Entity</th><th class="p-4">Action</th><th class="p-4">Details</th></tr></thead><tbody>${logs.map(l => `<tr class="border-b border-glc-zinc-100"><td class="p-4 text-sm">${new Date(l.timestamp).toLocaleString()}</td><td class="p-4">${l.entity_type} #${l.entity_id}</td><td class="p-4"><span class="px-2 py-1 bg-glc-green-100 text-glc-green-700 rounded text-xs">${l.action}</span></td><td class="p-4 text-sm text-glc-zinc-400">${JSON.stringify(l.data).slice(0, 50)}</td></tr>`).join('')}</tbody></table></div>`;
}

function getStatusClass(status) {
    const classes = {
        'approved': 'bg-green-100 text-green-700',
        'rejected': 'bg-red-100 text-red-700',
        'submitted': 'bg-blue-100 text-blue-700',
        'under_review': 'bg-yellow-100 text-yellow-700',
        'needs_info': 'bg-orange-100 text-orange-700',
        'draft': 'bg-gray-100 text-gray-700'
    };
    return classes[status] || 'bg-gray-100 text-gray-700';
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('glc_user');
    if (saved) {
        currentUser = JSON.parse(saved);
        showMainApp();
    }
});
