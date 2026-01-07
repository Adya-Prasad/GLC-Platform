import { apiCall, getCurrentUser, showModal } from './utils.js';

export async function renderLoanAssets() {
    const user = getCurrentUser();
    const isLender = user?.role === 'lender';
    const endpoint = isLender ? '/lender/applications' : '/borrower/applications';

    let apps = [];
    try {
        apps = await apiCall(endpoint);
    } catch (e) {
        console.error('Failed to fetch applications', e);
        return `<div class="p-8 text-center text-red-500 bg-white rounded-xl shadow-sm border border-red-100">
            <p class="font-bold">Error loading loan assets</p>
            <p class="text-sm mt-1">${e.message}</p>
        </div>`;
    }

    // Build per-loan cards with document lists (fetch docs for each application)
    const loanCards = [];
    for (const a of apps) {
        let docs = [];
        try {
            docs = await apiCall(`/borrower/${a.id}/documents`);
        } catch (e) {
            docs = [];
        }

        const docsHtml = (docs && docs.length > 0)
            ? docs.map(d => `
                <div class="flex items-center justify-between py-2 border-b">
                    <div class="flex items-center gap-6">
                        <span class="text-sm font-medium text-gray-800">${d.filename}</span>
                        <span class="text-xs text-gray-700">${d.file_type || 'file'}</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <button onclick="window.open('/borrower/document/${d.id}/view','_blank')" title="View" class="p-2 rounded-md hover:bg-gray-100"><svg class="h-5 w-5 text-orange-400" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.477 0 8.268 2.943 9.542 7-1.274 4.057-5.065 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg></button>
                        <a href="/borrower/document/${d.id}/download" title="Download" class="p-2 rounded-md hover:bg-gray-100"><svg class="h-5 w-5 text-violet-400" viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="M7 10l5 5 5-5"/><path d="M12 15V3"/></svg></a>
                        <button onclick="navigator.clipboard.writeText(window.location.origin + '/downloads/${a.loan_id || `LOAN_${a.id}`}/' + encodeURIComponent('${d.filename}')) && alert('Share URL copied to clipboard')" title="Share" class="p-2 rounded-md hover:bg-gray-100"><svg fill="currentColor" class="w-5 h-5 text-rose-400" viewBox="0 0 52 52">
<path d="m48.5 30h-3c-0.8 0-1.5 0.7-1.5 1.5v11c0 0.8-0.7 1.5-1.5 1.5h-33c-0.8 0-1.5-0.7-1.5-1.5v-21c0-0.8 0.7-1.5 1.5-1.5h4c0.8 0 1.5-0.7 1.5-1.5v-3c0-0.8-0.7-1.5-1.5-1.5h-7.5c-2.2 0-4 1.8-4 4v28c0 2.2 1.8 4 4 4h40c2.2 0 4-1.8 4-4v-14.5c0-0.8-0.7-1.5-1.5-1.5z m-14.5-16c-10 0-19.1 8.9-19.9 19.4-0.1 0.8 0.6 1.6 1.5 1.6h3c0.8 0 1.4-0.6 1.5-1.3 0.7-7.5 7.1-13.7 14.9-13.7h1.6c0.9 0 1.3 1.1 0.7 1.7l-5.5 5.6c-0.6 0.6-0.6 1.5 0 2.1l2.1 2.1c0.6 0.6 1.5 0.6 2.1 0l13.6-13.5c0.6-0.6 0.6-1.5 0-2.1l-13.5-13.5c-0.6-0.6-1.5-0.6-2.1 0l-2.1 2.1c-0.6 0.6-0.7 1.5-0.1 2.1l5.6 5.6c0.6 0.6 0.2 1.7-0.7 1.7l-2.7 0.1z"></path></svg></button>
                    </div>
                </div>
            `).join('')
            : `<div class="py-4 text-gray-500">No documents uploaded for this loan.</div>`;

        loanCards.push(`
            <div class="custom-bg mt-4 rounded-lg border bg-white p-3 shadow-sm">
                <div class="flex align-middle justify-between border-b pb-2 mb-2 border-[color:var(--border-color)]">
                    <span class="text-[14px] font-bold text-green-800">${a.loan_id || `LOAN-${a.id}`} : ${a.project_name}</span>
                    <button class="flex px-2 py-1 btn-second text-[13px] flex align-middle"><svg fill="currentColor" class="w-5 h-5"viewBox="0 0 24 24"><path d="M8.71,7.71,11,5.41V15a1,1,0,0,0,2,0V5.41l2.29,2.3a1,1,0,0,0,1.42,0,1,1,0,0,0,0-1.42l-4-4a1,1,0,0,0-.33-.21,1,1,0,0,0-.76,0,1,1,0,0,0-.33.21l-4,4A1,1,0,1,0,8.71,7.71ZM21,12a1,1,0,0,0-1,1v6a1,1,0,0,1-1,1H5a1,1,0,0,1-1-1V13a1,1,0,0,0-2,0v6a3,3,0,0,0,3,3H19a3,3,0,0,0,3-3V13A1,1,0,0,0,21,12Z"/></svg>Upload</button>
                </div>
                <div class="space-y-0">
                    ${docsHtml}
                </div>
            </div>
        `);
    }

    const content = loanCards.length ? loanCards.join('\n') : `<div class="p-8 text-center text-gray-500 bg-white rounded-xl">No loan assets available</div>`;

    return `
        <div class="bg-white rounded-xl p-4">
            <h1 class="text-lg font-bold text-gray-800">Reports and Data</h1>
            <p class="text-[15px] font-medium text-gray-800">A Centrally Distributed Collection of Data and Generated Reports to Manage</p>
            <div class="mt-4">
                ${content}
            </div>
        </div>
    `;
}

// View assets modal
window.viewLoanAssets = async function (e, loanId) {
    if (e) e.stopPropagation();
    try {
        const docs = await apiCall(`/borrower/${loanId}/documents`);
        const app = await apiCall(`/borrower/application/${loanId}`);

        const docsHtml = (docs && docs.length > 0)
            ? docs.map(d => `
                <li class="py-2 border-b"><a href="/downloads/${app.loan_id}/${d.filename}" target="_blank" class="text-[14px] text-green-700 font-medium">${d.filename}</a> <span class="text-xs text-gray-400">(${d.file_type || 'file'})</span></li>
            `).join('')
            : '<li class="py-4 text-gray-500">No documents uploaded for this loan.</li>';

        const rawJson = app.raw_application_json ? `<pre class="overflow-auto text-xs bg-gray-50 p-3 rounded">${JSON.stringify(app.raw_application_json, null, 2)}</pre>` : '<p class="text-gray-500">No application data available.</p>';

        const content = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <h4 class="font-bold mb-3">Supporting Documents</h4>
                    <ul>
                        ${docsHtml}
                    </ul>
                </div>
                <div>
                    <h4 class="font-bold mb-3">Raw Application JSON</h4>
                    ${rawJson}
                </div>
            </div>
        `;

        showModal(`Loan Assets - ${app.loan_id}`, content);
    } catch (err) {
        alert('Failed to load loan assets: ' + err.message);
    }
};