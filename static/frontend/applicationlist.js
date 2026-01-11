import { apiCall, formatCurrency, getStatusClass, getCurrentUser, showModal } from './utils.js';

export async function renderApplications() {
    const user = getCurrentUser();
    const isLender = user?.role === 'lender';
    const endpoint = isLender ? '/lender/applications' : '/borrower/applications';

    let apps = [];
    try {
        apps = await apiCall(endpoint);
    } catch (e) {
        console.error("Failed to fetch applications", e);
        return `<div class="p-8 text-center text-red-500 bg-white rounded-xl shadow-sm border border-red-100">
            <p class="font-bold">Error loading applications</p>
            <p class="text-sm mt-1">${e.message}</p>
            <button onclick="window.navigateTo('${isLender ? 'dashboard' : 'my-applications'}')" class="mt-4 px-4 py-2 bg-red-50 text-red-600 rounded-lg text-sm font-semibold">Retry</button>
        </div>`;
    }

    const tableBody = (apps && apps.length > 0)
        ? apps.map(a => `
            <tr class="hover:bg-gray-50/50 transition-colors cursor-pointer group border-b p-2 border-[color:var(--border-color)]" onclick="window.viewApplication(${a.id})">
                <td class="px-3 py-4">
                    <p class="font-bold text-gray-900 group-hover:text-[var(--green)] transition-colors">${a.project_name}</p>
                    <p class="text-[10px] text-gray-500 font-medium uppercase mt-0.5">ID: LOAN-${a.id}</p>
                </td>
                <td class="px-6 py-4 text-sm text-gray-600 font-medium">${a.org_name || 'N/A'}</td>
                <td class="px-6 py-4 text-sm text-gray-500">${a.sector}</td>
                <td class="px-6 py-4 text-sm font-bold text-gray-900">${formatCurrency(a.amount_requested, a.currency)}</td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 rounded-full cursor-progress text-[11px] font-bold uppercase tracking-wider ${getStatusClass(a.status)}">${a.status}</span>
                </td>
                <td class="px-6 py-4 text-sm text-gray-600 text-center">
                    <div class="flex items-center justify-center gap-3">
                        <p class="inlin-flex font-bold text-amber-700 ">${a.shareholder_entities ?? 0}+1</p>
                        <button onclick="window.inviteShareholders(event, ${a.id})" class="flex items-center gap-2 px-3 py-1 rounded-md text-sm bg-amber-400 text-amber-700 hover:bg-amber-100 transition-all" title="Invite shareholders">
                        <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none"><circle cx="9" cy="7" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M11 13H7C4.79086 13 3 14.7909 3 17C3 18.6569 4.34315 20 6 20H12C13.6569 20 15 18.6569 15 17C15 14.7909 13.2091 13 11 13Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M20.7249 9.25H15.7751M18.25 6.77515L18.25 11.7249" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>
                        <span class="invite-text text-xs font-semibold">Invite</span>
                        </button>
                    </div>
                </td>
                <td class="px-2 py-5 text-center">
                    <button onclick="window.navigateToAudit(${a.id})" class=" text-[var(--green)] px-2 py-1 rounded-full transition-all flex-inline items-center justify-center mx-auto gap-2 hover:border-[var(--green)] hover:border">
                         <svg fill="currentColor" class="w-6 h-6" viewBox="0 0 24 24" data-name="Line Color"><path d="M21,15l-2.83-2.83M13,10a3,3,0,1,0,3-3A3,3,0,0,0,13,10Zm0,7H7m2-4H7" style="fill: none; stroke: currentColor; stroke-linecap: round; stroke-linejoin: round; stroke-width: 2;"></path><path d="M17,17v3a1,1,0,0,1-1,1H4a1,1,0,0,1-1-1V4A1,1,0,0,1,4,3H16" style="fill: none; stroke:currentColor"></path></svg>
                         <p class="text-xs font-bold">See Audit</p>
                    </button>
                </td>
            </tr>
        `).join('')
        : `<tr>
            <td colspan="8" class="px-6 py-20 text-center">
                <div class="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <svg class="w-8 h-8 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                </div>
                <h2 class="text-xl font-bold text-gray-900">No applications found</h2>
                <p class="text-gray-500 mt-2 mb-8">You haven't submitted any loan applications yet.</p>
                ${!isLender ? `
                    <button onclick="window.navigateTo('apply')" class="px-8 py-3 bg-[var(--green)] text-white font-bold rounded-2xl hover:opacity-90 transition-all shadow-lg shadow-green-900/10">
                        Start New Application
                    </button>
                ` : ''}
            </td>
        </tr>`;

    return `
        <div class="bg-white rounded-2xl shadow-sm overflow-hidden border border-gray-100">
            <div class="p-6 border-b border-gray-50 flex justify-between items-center">
                <h2 class="text-lg font-bold text-gray-900">${isLender ? 'Applications Queue' : 'My Applications'}</h2>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full">
                    <thead>
                        <tr class="bg-gray-50/50 text-left text-xs uppercase text-gray-500 font-bold tracking-wider">
                            <th class="px-6 py-4">Project Name</th>
                            <th class="px-6 py-4">Org Name</th>
                            <th class="px-6 py-4">Industry Sector</th>
                            <th class="px-6 py-4">Amount</th>
                            <th class="px-6 py-4">Status</th>
                            <th class="px-6 py-4">Shareholders</th>
                            <th class="px-6 py-4 text-center">Audit</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-50">
                         ${tableBody}
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

// Global Audit View Handler
window.viewAuditTrail = async function (e, entityType, entityId) {
    if (e) e.stopPropagation();
    try {
        const logs = await apiCall(`/audit/${entityType}/${entityId}`);
        const content = `
            <div class="space-y-6 max-h-[60vh] overflow-y-auto pr-2">
                ${logs.length > 0 ? logs.map((log, index) => {
            const date = new Date(log.timestamp).toLocaleString();
            const isLast = index === logs.length - 1;
            return `
                        <div class="flex gap-4">
                            <div class="flex flex-col items-center">
                                <div class="w-3 h-3 rounded-full bg-[var(--green)] ring-4 ring-green-50"></div>
                                ${!isLast ? '<div class="w-0.5 bg-gray-200 flex-1 my-1"></div>' : ''}
                            </div>
                            <div class="flex-1 pb-6">
                                <p class="text-sm font-bold text-gray-900">${log.action.toUpperCase()}</p>
                                <p class="text-xs text-gray-500 mb-2">${date} • User ID: ${log.user_id || 'System'}</p>
                                <div class="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg font-mono text-xs">
                                    ${JSON.stringify(log.data, null, 2)}
                                </div>
                            </div>
                        </div>
                    `;
        }).join('') : '<p class="text-gray-500 text-center py-4">No history recorded yet.</p>'}
            </div>
        `;

        showModal(`Audit Trail #${entityId}`, content);

    } catch (e) {
        alert("Failed to load audit trail: " + e.message);
    }
}

// Invite shareholders helper - copies an invite link and shows temporary feedback
window.inviteShareholders = function (e, loanId) {
    if (e) e.stopPropagation();
    const link = `${location.origin}/invite?loan_id=${loanId}`;
    try {
        navigator.clipboard.writeText(link).then(() => {
            const btn = e.currentTarget || (e.target && e.target.closest ? e.target.closest('button') : null);
            const textEl = btn ? btn.querySelector('.invite-text') : null;
            if (textEl) {
                const prev = textEl.textContent;
                textEl.textContent = 'Copied!';
                setTimeout(() => textEl.textContent = prev, 2000);
            } else {
                alert('Shareholder invite link copied to clipboard');
            }
        }).catch(() => {
            alert('Could not copy to clipboard. Link: ' + link);
        });
    } catch (err) {
        alert('Copy failed: ' + err.message);
    }
};
