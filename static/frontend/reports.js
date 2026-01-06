import { apiCall } from './utils.js';

export async function renderReports() {
    // Mock reports
    const reports = [
        { id: 1, title: 'Q3 2023 Green Loan Portfolio Report', date: '2023-10-01', status: 'Available' },
        { id: 2, title: 'Annual ESG Impact Assessment', date: '2023-09-15', status: 'Available' },
        { id: 3, title: 'Compliance Audit Log', date: '2023-10-20', status: 'Processing' }
    ];

    return `
         <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div class="bg-gradient-to-br from-green-500 to-green-700 rounded-2xl p-6 text-white shadow-lg">
                <h3 class="font-semibold opacity-90 mb-1">Total Green Assets</h3>
                <p class="text-3xl font-bold">$124.5M</p>
                <div class="mt-4 text-sm opacity-80 flex items-center">
                    <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>
                    +12% from last quarter
                </div>
            </div>
             <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                <h3 class="text-gray-500 text-sm mb-1">Portfolio ESG Score</h3>
                <p class="text-3xl font-bold text-gray-900">76.4</p>
                <div class="w-full bg-gray-100 rounded-full h-2 mt-4">
                    <div class="bg-[var(--green)] h-2 rounded-full" style="width: 76%"></div>
                </div>
            </div>
             <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
                 <h3 class="text-gray-500 text-sm mb-1">Carbon Avoided</h3>
                <p class="text-3xl font-bold text-gray-900">45.2k <span class="text-base font-normal text-gray-500">tCO2e</span></p>
                 <div class="mt-4 text-sm text-green-600 flex items-center">
                    On track for 2024 targets
                </div>
            </div>
        </div>

        <div class="bg-white rounded-2xl p-6 shadow-sm">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-lg font-semibold">Generated Reports</h2>
                <button class="text-[var(--green)] hover:underline text-sm font-medium">View Archive</button>
            </div>
            
            <div class="space-y-4">
                ${reports.map(r => `
                    <div class="flex items-center justify-between p-4 border rounded-xl hover:bg-gray-50 transition-colors">
                        <div class="flex items-center space-x-4">
                            <div class="w-10 h-10 ${r.status === 'Processing' ? 'bg-yellow-50 text-yellow-600' : 'bg-green-50 text-green-600'} rounded-lg flex items-center justify-center">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                            </div>
                            <div>
                                <p class="font-medium text-gray-900">${r.title}</p>
                                <p class="text-xs text-gray-500">Generated on ${r.date}</p>
                            </div>
                        </div>
                        <div class="flex items-center space-x-4">
                            <span class="px-3 py-1 rounded-full text-xs font-medium ${r.status === 'Processing' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700'}">
                                ${r.status}
                            </span>
                             ${r.status === 'Available' ? `
                                <button class="p-2 text-gray-500 hover:text-green-600 transition-colors">
                                    <svg class="w-5 h-5" viewBox="0 0 16 16" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"><path d="m3.25 13.25h9m-8.5-6.5 4 3.5 4-3.5m-4-5v8.5"/></svg>
                                </button>
                             ` : ''}
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}
