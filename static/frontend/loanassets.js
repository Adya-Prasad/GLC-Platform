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

    const tableBody = (apps && apps.length > 0)
        ? apps.map(a => `
            <tr>
                <td class="px-6 py-4 font-bold">${a.loan_id || `LOAN-${a.id}`}</td>
                <td class="px-6 py-4">${a.project_name}</td>
                <td class="px-6 py-4">${a.org_name || 'N/A'}</td>
                <td class="px-6 py-4 text-center">
                    <button onclick="window.viewLoanAssets(event, ${a.id})" class="px-3 py-1 rounded-md bg-[var(--green)] text-white text-sm">View Assets</button>
                </td>
            </tr>
        `).join('')
        : `<tr><td colspan="4" class="px-6 py-8 text-center text-gray-500">No loan assets available</td></tr>`;

    return `
        <div class="bg-white rounded-xl p-4">
            <h1 class="text-lg font-bold text-gray-800">Reports and Data</h1>
            <p class="text-[15px] font-medium text-gray-800">A Centrally Distributed Collection of Data and Generated Reports to Manage</p>

            <div class="custom-bg mt-4">
                <div class="flex align-middle justify-between border-b p-2 border-[color:var(--border-color)]">
                    <span class="text-[15px] font-bold text-green-800">Loan ID | Project Name</span>
                    <button class="px-2 py-1 btn-second text-[13px] flex align-middle">Upload</button>
                </div>
                <div class="overflow-x-auto mt-4">
                    <table class="w-full text-left">
                        <thead>
                            <tr class="text-xs text-gray-500 uppercase font-bold">
                                <th class="px-6 py-3">Loan ID</th>
                                <th class="px-6 py-3">Project</th>
                                <th class="px-6 py-3">Organization</th>
                                <th class="px-6 py-3 text-center">Actions</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-gray-100">${tableBody}</tbody>
                    </table>
                </div>
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