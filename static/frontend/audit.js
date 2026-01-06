
import { apiCall, getStatusClass, formatCurrency } from './utils.js';

export async function renderAuditPage() {
    // Get ID from window state
    const appId = window.currentAuditAppId;
    if (!appId) {
        return `<div class="p-8 text-center">No application selected. <button onclick="window.navigateTo('applications')" class="text-green-600 font-bold">Go back</button></div>`;
    }

    let app, logs, isLender;
    try {
        const user = JSON.parse(localStorage.getItem('glc_user'));
        isLender = user?.role === 'lender';

        // Fetch App Details based on role
        if (isLender) {
            const detail = await apiCall(`/lender/application/${appId}`);
            app = detail.loan_app;
            if (detail.borrower) app.org_name = detail.borrower.org_name;
        } else {
            app = await apiCall(`/borrower/application/${appId}`);
            // If org_name is missing in response, use user's active name or fetch
        }

        // Fetch Audit Logs
        logs = await apiCall(`/audit/LoanApplication/${appId}`);

    } catch (e) {
        console.error(e);
        return `<div class="p-8 text-center text-red-500">Error loading audit data: ${e.message}</div>`;
    }

    // Process dates
    const createdDate = new Date(app.created_at).toLocaleDateString();

    // AI Analysis Mock (in real app, fetch from backend)
    const analysis = app.esg_score
        ? `ESG Score: <b>${app.esg_score}</b>. Based on the uploaded documents, this project shows strong alignment with Green Loan Principles.`
        : "AI Analysis pending. Upload documents and submit for review to generate insights.";

    return `
        <div class="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <!-- Header -->
            <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 flex justify-between items-start">
                <div>
                    <div class="flex items-center gap-3 mb-2">
                         <span class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${getStatusClass(app.status)}">${app.status}</span>
                         <span class="text-sm text-gray-500 font-mono">APP-${app.id}</span>
                    </div>
                    <h1 class="text-2xl font-bold text-gray-900">${app.project_name}</h1>
                    <p class="text-gray-500 mt-1 flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
                        ${app.org_name || 'Organization'}
                    </p>
                </div>
                <div class="text-right">
                     <p class="text-3xl font-bold text-gray-900">${formatCurrency(app.amount_requested, app.currency)}</p>
                     <p class="text-sm text-gray-500 mt-1">Requested Amount</p>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- Left: Details -->
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 h-fit">
                    <h3 class="font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <svg class="w-5 h-5 text-[var(--green)]" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        Key Details
                    </h3>
                    <div class="space-y-4 text-sm">
                        <div class="flex justify-between py-2 border-b border-gray-50">
                            <span class="text-gray-500">Sector</span>
                            <span class="font-medium text-gray-900 text-right">${app.sector}</span>
                        </div>
                        <div class="flex justify-between py-2 border-b border-gray-50">
                            <span class="text-gray-500">Location</span>
                            <span class="font-medium text-gray-900 text-right">${app.location || '-'}</span>
                        </div>
                        <div class="flex justify-between py-2 border-b border-gray-50">
                            <span class="text-gray-500">Submitted On</span>
                            <span class="font-medium text-gray-900 text-right">${createdDate}</span>
                        </div>
                         <div class="flex justify-between py-2 border-b border-gray-50">
                            <span class="text-gray-500">Planned Start</span>
                            <span class="font-medium text-gray-900 text-right">${app.planned_start_date || '-'}</span>
                        </div>
                        <div class="mt-4 pt-2">
                             <span class="text-gray-500 block mb-1">Use of Proceeds</span>
                             <p class="text-gray-900 bg-gray-50 p-3 rounded-lg text-xs leading-relaxed">
                                ${app.use_of_proceeds || 'Not specified'}
                             </p>
                        </div>
                    </div>
                </div>

                <!-- Middle: AI Analysis -->
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 h-fit">
                     <h3 class="font-bold text-gray-900 mb-4 flex items-center gap-2">
                        <svg class="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
                        AI Insight
                    </h3>
                    <div class="bg-gradient-to-br from-purple-50 to-indigo-50 p-5 rounded-xl border border-purple-100">
                        <p class="text-gray-700 text-sm leading-relaxed mb-4">
                            ${analysis}
                        </p>
                         <div class="flex gap-2 flex-wrap">
                            ${(app.kpi_metrics || []).map(k => `<span class="bg-white text-purple-700 px-2 py-1 rounded text-[10px] font-bold shadow-sm border border-purple-100 uppercase">${k}</span>`).join('')}
                        </div>
                    </div>
                </div>

                <!-- Right: Audit Timeline -->
                <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100 h-fit">
                    <h3 class="font-bold text-gray-900 mb-6 flex items-center gap-2">
                        <svg class="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        Audit Trail
                    </h3>
                    
                    <div class="relative border-l-2 border-gray-100 ml-3 space-y-8 pl-6 pb-2">
                        ${logs.map((log, i) => {
        const date = new Date(log.timestamp).toLocaleString();
        return `
                                <div class="relative">
                                    <span class="absolute -left-[31px] bg-white border-2 border-[var(--green)] w-4 h-4 rounded-full"></span>
                                    <div class="flex flex-col">
                                        <span class="text-xs font-bold text-[var(--green)] uppercase tracking-wider mb-1">${log.action}</span>
                                        <span class="text-xs text-gray-500 mb-2 font-mono">${date}</span>
                                        <div class="bg-gray-50 border border-gray-200 rounded p-2 text-xs font-mono text-gray-600 break-words">
                                            ${JSON.stringify(log.data)}
                                        </div>
                                    </div>
                                </div>
                             `;
    }).join('')}
                        
                        ${logs.length === 0 ? '<p class="text-sm text-gray-500 italic">No audit history found.</p>' : ''}
                    </div>
                </div>
            </div>
            
            <div class="text-center pt-8">
                 <button onclick="window.navigateTo('applications')" class="px-6 py-2 bg-gray-100 text-gray-600 font-bold rounded-xl hover:bg-gray-200 transition-colors">Back to Applications</button>
            </div>
        </div>
    `;
}
