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
    const portfolio = await apiCall('/lender/portfolio/summary');

    return `
        <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
            <div class="bg-white rounded-2xl p-5 shadow-sm">
                <p class="text-gray-500 text-xs">Total Apps</p>
                <p class="text-2xl font-bold text-[var(--green)]">${portfolio.total_applications}</p>
            </div>
            <div class="bg-white rounded-2xl p-5 shadow-sm">
                <p class="text-gray-500 text-xs">Approved</p>
                <p class="text-2xl font-bold text-green-600">${portfolio.num_approved}</p>
            </div>
            <div class="bg-white rounded-2xl p-5 shadow-sm">
                <p class="text-gray-500 text-xs">Pending</p>
                <p class="text-2xl font-bold text-yellow-600">${portfolio.num_pending}</p>
            </div>
            <div class="bg-white rounded-2xl p-5 shadow-sm">
                <p class="text-gray-500 text-xs">Avg ESG</p>
                <p class="text-2xl font-bold text-purple-600">${portfolio.avg_esg_score}</p>
            </div>
            <div class="bg-white rounded-2xl p-5 shadow-sm">
                <p class="text-gray-500 text-xs">Financed CO₂</p>
                <p class="text-2xl font-bold text-orange-600">${(portfolio.total_financed_co2 / 1000).toFixed(0)}k</p>
            </div>
            <div class="bg-white rounded-2xl p-5 shadow-sm">
                <p class="text-gray-500 text-xs">Green %</p>
                <p class="text-2xl font-bold text-[var(--green)]">${portfolio.percent_eligible_green?.toFixed(0) || 0}%</p>
            </div>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-white rounded-2xl p-6 shadow-sm">
                <h3 class="font-semibold mb-4">Quick Actions</h3>
                <div class="space-y-3">
                    <button onclick="window.navigateTo('applications')" class="w-full py-3 px-4 bg-green-50 hover:bg-green-100 text-green-700 rounded-xl text-left flex items-center justify-between transition-colors">
                        Review Applications <span>→</span>
                    </button>
                    <button onclick="window.navigateTo('portfolio')" class="w-full py-3 px-4 bg-gray-50 hover:bg-gray-100 text-gray-700 rounded-xl text-left flex items-center justify-between transition-colors">
                        View Portfolio <span>→</span>
                    </button>
                </div>
            </div>
            <div class="bg-white rounded-2xl p-6 shadow-sm">
                <h3 class="font-semibold mb-4">Sector Distribution</h3>
                <div class="space-y-2">
                    ${Object.entries(portfolio.sector_breakdown || {}).map(([k, v]) => `
                        <div class="flex justify-between items-center">
                            <span class="text-sm">${k}</span>
                            <span class="bg-green-100 text-green-700 px-2 py-1 rounded text-xs">${v}</span>
                        </div>
                    `).join('') || '<p class="text-gray-500">No data</p>'}
                </div>
            </div>
        </div>
    `;
}