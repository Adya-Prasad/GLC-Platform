import { apiCall, formatCurrency, getStatusClass, getCurrentUser } from './utils.js';

export async function renderBorrowerDashboard() {
    const user = getCurrentUser();

    // Parallel fetch
    const [stats, applications] = await Promise.all([
        apiCall(`/borrower/stats?current_user_id=${user.id}`), // Mocking ID passing if needed
        apiCall('/borrower/applications')
    ]).catch(e => {
        console.error(e);
        return [[], []];
    });

    // Stats Mocks if API returns empty/error or custom format
    // Adjust based on actual API return signature. 
    // Assuming API returns array of {label, value} or properties.
    // user stats might be just an object.
    const statsData = Array.isArray(stats) ? stats : [
        { label: 'Active Loans', value: stats.active_loans || '0' },
        { label: 'Pending Apps', value: stats.pending_applications || '0' },
        { label: 'Total Borrowed', value: stats.total_borrowed || '$0' },
        { label: 'ESG Score', value: stats.esg_score || '-' }
    ];

    return `
        <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            ${statsData.map(s => `
                <div class="bg-white rounded-2xl p-6 shadow-sm card-hover">
                    <p class="text-gray-500 text-sm">${s.label}</p>
                    <p class="text-3xl font-bold text-[var(--green)] mt-2">${s.value}</p>
                </div>
            `).join('')}
        </div>
        
        <div class="bg-white rounded-2xl p-6 shadow-sm">
            <div class="flex justify-between items-center mb-6">
                <h3 class="text-lg font-semibold">Recent Applications</h3>
                <button onclick="window.navigateTo('apply')" class="bg-[var(--green)] text-white px-4 py-2 rounded-lg hover:opacity-90 transition-all">
                    + New Application
                </button>
            </div>
            ${applications.length ? `
                <div class="overflow-x-auto">
                    <table class="w-full">
                        <thead>
                            <tr class="text-left text-gray-500 text-sm border-b">
                                <th class="pb-4">Project</th>
                                <th class="pb-4">Sector</th>
                                <th class="pb-4">Amount</th>
                                <th class="pb-4">Status</th>
                                <th class="pb-4">ESG</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${applications.slice(0, 5).map(a => `
                                <tr class="border-b border-gray-100 hover:bg-gray-50 cursor-pointer" onclick="window.viewApplication(${a.id})">
                                    <td class="py-4 font-medium">${a.project_name}</td>
                                    <td class="py-4">${a.sector}</td>
                                    <td class="py-4">${formatCurrency(a.amount_requested, a.currency)}</td>
                                    <td class="py-4"><span class="px-3 py-1 rounded-full text-xs ${getStatusClass(a.status)}">${a.status}</span></td>
                                    <td class="py-4">
                                        <span class="font-semibold ${a.esg_score >= 70 ? 'text-green-600' : 'text-yellow-600'}">
                                            ${a.esg_score || '-'}
                                        </span>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : '<p class="text-gray-500 text-center py-8">No applications yet. Click "New Application" to get started.</p>'}
        </div>
    `;
}

export async function renderLenderDashboard() {
    // Fetch portfolio summary and all applications
    const [portfolio, applications] = await Promise.all([
        apiCall('/lender/portfolio/summary'),
        apiCall('/lender/applications')
    ]).catch(e => {
        console.error(e);
        return [{}, []];
    });

    const totalLoanAmount = applications.reduce((sum, a) => sum + (a.amount_requested || 0), 0);
    const approvedAmount = applications.filter(a => a.status === 'approved').reduce((sum, a) => sum + (a.amount_requested || 0), 0);
    
    return `
        <div class="space-y-6">
            <!-- Dashboard Header -->
            <div class="flex justify-between items-center">
                <div>
                    <h1 class="text-2xl font-bold text-gray-800">Lender Dashboard</h1>
                    <p class="text-gray-500 text-sm">Green Loan Portfolio Overview</p>
                </div>
                <div class="flex gap-3">
                    <button onclick="window.navigateTo('applications')" class="px-4 py-2 bg-[var(--green)] text-white rounded-lg hover:opacity-90 transition-all flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
                        Review Applications
                    </button>
                </div>
            </div>

            <!-- Key Metrics Row -->
            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                <div class="bg-gradient-to-br from-emerald-500 to-green-600 rounded-xl p-5 text-white">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-emerald-100 text-xs font-medium">Total Applications</p>
                            <p class="text-3xl font-bold mt-1">${portfolio.total_applications || 0}</p>
                        </div>
                        <div class="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                        </div>
                    </div>
                </div>
                
                <div class="bg-gradient-to-br from-blue-500 to-indigo-600 rounded-xl p-5 text-white">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-blue-100 text-xs font-medium">Total Loan Pool</p>
                            <p class="text-2xl font-bold mt-1">${formatCurrency(totalLoanAmount, 'USD')}</p>
                        </div>
                        <div class="w-10 h-10 bg-white/20 rounded-lg flex items-center justify-center">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                        </div>
                    </div>
                </div>
                
                <div class="bg-white rounded-xl p-5 border border-gray-200">
                    <p class="text-gray-500 text-xs font-medium">Approved</p>
                    <p class="text-2xl font-bold text-green-600 mt-1">${portfolio.num_approved || 0}</p>
                    <p class="text-xs text-gray-400 mt-1">${formatCurrency(approvedAmount, 'USD')}</p>
                </div>
                
                <div class="bg-white rounded-xl p-5 border border-gray-200">
                    <p class="text-gray-500 text-xs font-medium">Pending Review</p>
                    <p class="text-2xl font-bold text-yellow-600 mt-1">${portfolio.num_pending || 0}</p>
                    <div class="mt-2 h-1 bg-gray-100 rounded-full overflow-hidden">
                        <div class="h-full bg-yellow-500" style="width: ${portfolio.total_applications ? (portfolio.num_pending / portfolio.total_applications * 100) : 0}%"></div>
                    </div>
                </div>
                
                <div class="bg-white rounded-xl p-5 border border-gray-200">
                    <p class="text-gray-500 text-xs font-medium">Avg ESG Score</p>
                    <p class="text-2xl font-bold ${portfolio.avg_esg_score >= 70 ? 'text-green-600' : portfolio.avg_esg_score >= 50 ? 'text-yellow-600' : 'text-red-500'} mt-1">${portfolio.avg_esg_score || 0}</p>
                    <p class="text-xs text-gray-400 mt-1">out of 100</p>
                </div>
                
                <div class="bg-white rounded-xl p-5 border border-gray-200">
                    <p class="text-gray-500 text-xs font-medium">Green Eligible</p>
                    <p class="text-2xl font-bold text-emerald-600 mt-1">${portfolio.percent_eligible_green?.toFixed(0) || 0}%</p>
                    <p class="text-xs text-gray-400 mt-1">${portfolio.num_green_projects || 0} projects</p>
                </div>
            </div>

            <!-- Main Content Grid -->
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Left Column: Status Overview & Sectors -->
                <div class="space-y-6">
                    <!-- Status Breakdown -->
                    <div class="bg-white rounded-xl p-6 border border-gray-200">
                        <h3 class="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
                            Application Status
                        </h3>
                        <div class="space-y-3">
                            ${renderStatusBar('Approved', portfolio.num_approved || 0, portfolio.total_applications, 'bg-green-500')}
                            ${renderStatusBar('Under Review', portfolio.status_breakdown?.under_review || 0, portfolio.total_applications, 'bg-blue-500')}
                            ${renderStatusBar('Pending', portfolio.status_breakdown?.pending || 0, portfolio.total_applications, 'bg-yellow-500')}
                            ${renderStatusBar('Rejected', portfolio.num_rejected || 0, portfolio.total_applications, 'bg-red-500')}
                        </div>
                    </div>

                    <!-- Sector Distribution -->
                    <div class="bg-white rounded-xl p-6 border border-gray-200">
                        <h3 class="font-semibold text-gray-800 mb-4 flex items-center gap-2">
                            <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"/></svg>
                            Sectors
                        </h3>
                        <div class="space-y-2">
                            ${Object.entries(portfolio.sector_breakdown || {}).length ? 
                                Object.entries(portfolio.sector_breakdown).map(([sector, count]) => `
                                    <div class="flex justify-between items-center p-2 rounded-lg hover:bg-gray-50">
                                        <span class="text-sm text-gray-700">${sector}</span>
                                        <span class="bg-emerald-100 text-emerald-700 px-2 py-1 rounded-full text-xs font-medium">${count}</span>
                                    </div>
                                `).join('') : 
                                '<p class="text-gray-400 text-sm text-center py-4">No sector data</p>'
                            }
                        </div>
                    </div>

                    <!-- Environmental Impact -->
                    <div class="bg-gradient-to-br from-orange-50 to-amber-50 rounded-xl p-6 border border-orange-200">
                        <h3 class="font-semibold text-orange-800 mb-4 flex items-center gap-2">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064"/></svg>
                            Financed Emissions
                        </h3>
                        <div class="text-center">
                            <p class="text-4xl font-bold text-orange-600">${((portfolio.total_financed_co2 || 0) / 1000).toFixed(1)}k</p>
                            <p class="text-sm text-orange-700 mt-1">tCO₂e Total</p>
                        </div>
                        <div class="mt-4 pt-4 border-t border-orange-200">
                            <div class="flex justify-between text-sm">
                                <span class="text-orange-700">Flagged High Risk</span>
                                <span class="font-bold text-orange-800">${portfolio.flagged_count || 0}</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Right Column: Loans Table -->
                <div class="lg:col-span-2">
                    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
                        <div class="px-6 py-4 border-b border-gray-200 flex justify-between items-center">
                            <h3 class="font-semibold text-gray-800 flex items-center gap-2">
                                <svg class="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16"/></svg>
                                All Loan Applications
                            </h3>
                            <span class="text-sm text-gray-500">${applications.length} total</span>
                        </div>
                        <div class="overflow-x-auto max-h-[500px] overflow-y-auto">
                            <table class="w-full">
                                <thead class="bg-gray-50 sticky top-0">
                                    <tr class="text-left text-gray-500 text-xs uppercase tracking-wider">
                                        <th class="px-6 py-3 font-medium">Organization</th>
                                        <th class="px-6 py-3 font-medium">Project</th>
                                        <th class="px-6 py-3 font-medium">Sector</th>
                                        <th class="px-6 py-3 font-medium text-right">Loan Amount</th>
                                        <th class="px-6 py-3 font-medium text-right">Revenue</th>
                                        <th class="px-6 py-3 font-medium text-center">ESG</th>
                                        <th class="px-6 py-3 font-medium text-center">Status</th>
                                    </tr>
                                </thead>
                                <tbody class="divide-y divide-gray-100">
                                    ${applications.length ? applications.map(app => `
                                        <tr class="hover:bg-gray-50 cursor-pointer transition-colors" onclick="window.navigateToAudit(${app.id})">
                                            <td class="px-6 py-4">
                                                <div class="font-medium text-gray-900 text-sm">${app.org_name || '-'}</div>
                                            </td>
                                            <td class="px-6 py-4">
                                                <div class="text-sm text-gray-700">${app.project_name || '-'}</div>
                                            </td>
                                            <td class="px-6 py-4">
                                                <span class="text-xs text-gray-600 bg-gray-100 px-2 py-1 rounded">${app.sector || '-'}</span>
                                            </td>
                                            <td class="px-6 py-4 text-right">
                                                <span class="font-medium text-gray-900">${formatCurrency(app.amount_requested, app.currency)}</span>
                                            </td>
                                            <td class="px-6 py-4 text-right">
                                                <span class="text-sm text-gray-600">${app.annual_revenue ? formatCurrency(app.annual_revenue, 'USD') : '-'}</span>
                                            </td>
                                            <td class="px-6 py-4 text-center">
                                                <span class="inline-flex items-center justify-center w-10 h-10 rounded-full text-sm font-bold ${
                                                    app.esg_score >= 70 ? 'bg-green-100 text-green-700' : 
                                                    app.esg_score >= 50 ? 'bg-yellow-100 text-yellow-700' : 
                                                    app.esg_score ? 'bg-red-100 text-red-700' : 'bg-gray-100 text-gray-500'
                                                }">
                                                    ${app.esg_score || '-'}
                                                </span>
                                            </td>
                                            <td class="px-6 py-4 text-center">
                                                <span class="px-3 py-1 rounded-full text-xs font-medium ${getStatusClass(app.status)}">${app.status || 'pending'}</span>
                                            </td>
                                        </tr>
                                    `).join('') : `
                                        <tr>
                                            <td colspan="7" class="px-6 py-12 text-center text-gray-500">
                                                <svg class="w-12 h-12 mx-auto mb-3 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                                                No loan applications yet
                                            </td>
                                        </tr>
                                    `}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Helper function for status bars
function renderStatusBar(label, count, total, colorClass) {
    const percentage = total > 0 ? (count / total * 100) : 0;
    return `
        <div class="flex items-center gap-3">
            <div class="w-24 text-sm text-gray-600">${label}</div>
            <div class="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
                <div class="${colorClass} h-full rounded-full transition-all duration-500" style="width: ${percentage}%"></div>
            </div>
            <div class="w-8 text-sm font-medium text-gray-700 text-right">${count}</div>
        </div>
    `;
}