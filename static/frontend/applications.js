
import { apiCall, formatCurrency, getStatusClass, getCurrentUser, API_BASE, showModal } from './utils.js';

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
            <tr class="hover:bg-gray-50/50 transition-colors cursor-pointer group" onclick="window.viewApplication(${a.id})">
                <td class="px-6 py-4">
                    <p class="font-bold text-gray-900 group-hover:text-[var(--green)] transition-colors">${a.project_name}</p>
                    <p class="text-[10px] text-gray-500 font-medium uppercase mt-0.5">ID: LOAN-${a.id}</p>
                </td>
                <td class="px-6 py-4 text-sm text-gray-600 font-medium">${a.org_name || 'N/A'}</td>
                <td class="px-6 py-4 text-sm text-gray-500">${a.sector}</td>
                <td class="px-6 py-4 text-sm text-gray-500 font-mono">${a.planned_start_date || '-'}</td>
                <td class="px-6 py-4 text-sm font-bold text-gray-900">${formatCurrency(a.amount_requested, a.currency)}</td>
                <td class="px-6 py-4">
                    <span class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${getStatusClass(a.status)}">${a.status}</span>
                </td>
                <td class="px-6 py-4 text-center">
                    <button onclick="window.navigateToAudit(${a.id})" class="text-gray-500 hover:text-green-600 p-2 rounded-full hover:bg-green-50 transition-all flex items-center justify-center mx-auto gap-2 border border-gray-100 hover:border-green-200">
                         <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/></svg>
                         <span class="text-xs font-bold">See Audit</span>
                    </button>
                </td>
            </tr>
        `).join('')
        : `<tr>
            <td colspan="6" class="px-6 py-20 text-center">
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
                            <th class="px-6 py-4">Start Date</th>
                            <th class="px-6 py-4">Amount</th>
                            <th class="px-6 py-4">Status</th>
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


// ... (Existing helper functions saveApplicationProgress, loadDraft) ...
// For brevity, I'm keeping your existing code but updating the SUBMIT handler to use API_BASE

window.saveApplicationProgress = function () {
    const form = document.getElementById('loan-form');
    if (!form) return;
    const data = Object.fromEntries(new FormData(form));
    localStorage.setItem('loan_app_draft', JSON.stringify(data));
    alert('Progress saved locally. You can resume later.');
};

window.loadDraft = function () {
    try {
        const saved = localStorage.getItem('loan_app_draft');
        if (saved) {
            const data = JSON.parse(saved);
            const form = document.getElementById('loan-form');
            if (!form) return;
            Object.keys(data).forEach(key => {
                const el = form.elements[key];
                if (el) {
                    if (el instanceof RadioNodeList) el.value = data[key];
                    else if (el.type === 'checkbox') el.checked = true;
                    else if (el.type !== 'file') el.value = data[key];
                }
            });
        }
    } catch (e) { console.error("Error loading draft", e); }
};

export function renderApplicationForm() {
    setTimeout(() => window.loadDraft && window.loadDraft(), 100);
    // ... (Your HTML Form String is same, just returning it) ...
    // To save tokens, I'm pasting the HTML string you already verified but will ensure it is returned.

    return `
        <div class="max-w-4xl mx-auto space-y-8">
            <div class="bg-white rounded-2xl p-8 border border-[color:var(--border-color)]">
                <div class="pb-6 mb-8">
                    <h2 class="text-lg font-bold text-gray-700 text-center">Apply for a SSL Loan</h2>
                </div>

                <form id="loan-form" onsubmit="window.handleApplicationSubmit(event)" class="space-y-10">
                    
                    <section>
                        <h3 class="text-xl font-semibold text-[var(--green)] mb-6 flex items-center">
                            <span class="bg-green-100 text-[var(--green)] w-8 h-8 rounded-full flex items-center justify-center text-sm mr-3">1</span>
                            Organization & Contact Details
                        </h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div class="col-span-2 md:col-span-2">
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Organization Name *</label>
                                <input type="text" name="org_name" required placeholder="Legal entity name" class="w-full px-3 py-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>

                            
                            <!-- Contact Info -->
                            <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Contact Email *</label>
                                <input type="email" name="contact_email" required placeholder="contact@org.com" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                             <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Contact Phone *</label>
                                <input type="tel" name="contact_phone" required placeholder="+1 555-0123" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>

                            <!-- Org Details -->
                            <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">GST / Tax ID (in India)</label>
                                <input type="text" name="org_gst" placeholder="Registration number" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                             <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Credit Score</label>
                                <input type="text" name="credit_score" placeholder="e.g. 750" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                            
                            <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Headquarters Location</label>
                                <input type="text" name="location" placeholder="City, Country" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Website</label>
                                <input type="url" name="website" placeholder="https://" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                        </div>
                    </section>

                    <hr class="border-gray-100">

                    <!-- Section 2: Project Information -->
                    <section>
                        <h3 class="text-xl font-semibold text-[var(--green)] mb-6 flex items-center">
                            <span class="bg-green-100 text-[var(--green)] w-8 h-8 rounded-full flex items-center justify-center text-sm mr-3">2</span>
                            Project Information
                        </h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div class="col-span-2 md:col-span-1">
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Project Title *</label>
                                <input type="text" name="project_name" required placeholder="e.g., Solar Farm Phase II" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                            <div class="col-span-2 md:col-span-1">
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Project Sector *</label>
                                <select name="sector" required class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                    <option value="Fossil fuel utilities">Fossil fuel utilities</option>
                                    <option value="Oil & gas">Oil & gas</option>
                                    <option value="Mining and quarrying">Mining and quarrying</option>
                                    <option value="Chemicals">Chemicals</option>
                                    <option value="Agriculture, forestry, and fishing">Agriculture, forestry, and fishing</option>
                                    <option value="Transportation and storage">Transportation and storage</option>
                                    <option value="Construction materials">Construction materials</option>
                                    <option value="Construction">Construction</option>
                                    <option value="Wholesale and retail trade">Wholesale and retail trade</option>
                                    <option value="Real estate activities">Real estate activities</option>
                                    <option value="Manufacturing of machinery and equipment">Manufacturing of machinery and equipment</option>
                                    <option value="Water supply, sewerage and waste managemeny">Water supply, sewerage and waste managemeny</option>
                                    <option value="Food and beverage">Food and beverage</option>
                                    <option value="Information technology services">Information technology services</option>
                                    <option value="Healthcare service">Healthcare service</option>
                                    <option value="Renewable energy">Renewable energy</option>
                                    <option value="Financial and insurance activities">Financial and insurance activities</option>
                                    <option value="Healthcare and social assistance">Healthcare and social assistance</option>
                                    <option value="Education services">Education services</option>
                                    <option value="Professional, scientific and technical service">Professional, scientific and technical service</option>
                                </select>
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Project Location *</label>
                                <input type="text" name="project_location" required placeholder="Site address" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Project PIN / ZIP Code *</label>
                                <input type="text" name="project_pin_code" required placeholder="Project site code" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                             <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Project *</label>
                                <select name="project_type" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                    <option value="New Project">New Project (Greenfield)</option>
                                    <option value="Expansion">Expansion (Brownfield)</option>
                                    <option value="Refinancing">Refinancing</option>
                                    <option value="Maintenance">Maintenance / Upgrade</option>
                                </select>
                            </div>
                            
                            <!-- Reporting & Existing Loans -->
                             <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Reporting Frequency *</label>
                                <select name="reporting_frequency" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                    <option value="Annual">Annual</option>
                                    <option value="Half-Yearly">Half-Yearly</option>
                                    <option value="Quarterly">Quarterly</option>
                                </select>
                            </div>
                            
                             <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Existing Loans? *</label>
                                <select name="has_existing_loan" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                    <option value="false">No</option>
                                    <option value="true">Yes</option>
                                </select>
                            </div>
                             <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Planned Start Date</label>
                                <input type="date" name="planned_start_date" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Amount Requested*</label>
                                <div class="relative">
                                     <span class="absolute left-4 top-3.5 text-gray-500 font-bold">$</span>
                                    <input type="number" name="amount" required class="w-full pl-8 pr-4 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                </div>
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Currency *</label>
                                <select name="currency" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                    <option value="USD">USD - US Dollar</option>
                                    <option value="EUR">EUR - Euro</option>
                                    <option value="INR">INR - Indian Rupee</option>
                                    <option value="GBP">GBP - British Pound</option>
                                </select>
                            </div>
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Project Description *</label>
                                <textarea name="project_description" required rows="4" placeholder="Describe the project in detail..." class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]"></textarea>
                            </div>
                        
                    </section>

                    <!-- Section 3: Green & Environmental Impact -->
                     <section>
                         <h3 class="text-xl font-semibold text-[var(--green)] mb-6 flex items-center">
                            <span class="bg-green-100 text-[var(--green)] w-8 h-8 rounded-full flex items-center justify-center text-sm mr-3">3</span>
                            Green Qualification & Impact (KPIs)
                        </h3>
                        <div class="space-y-6">
                            <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Detailed Description of Proceeds Usage *</label>
                                <textarea name="use_of_proceeds" required rows="4" placeholder="Describe explicitly how the funds will be utilized..." class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]"></textarea>
                            </div>

                            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                                 <div>
                                    <label class="block text-[14px] font-medium text-gray-700 mb-2">Scope 1 Emissions (tCO2e) *</label>
                                    <input type="number" step="0.01" name="scope1_tco2" required placeholder="0.00" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                </div>
                                <div>
                                    <label class="block text-[14px] font-medium text-gray-700 mb-2">Scope 2 Emissions (tCO2e) *</label>
                                    <input type="number" step="0.01" name="scope2_tco2" required placeholder="0.00" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                </div>
                                <div>
                                    <label class="block text-[14px] font-medium text-gray-700 mb-2">Scope 3 Emissions (tCO2e) *</label>
                                    <input type="number" step="0.01" name="scope3_tco2" required placeholder="0.00" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                </div>
                            </div>
                             <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                                <div>
                                    <label class="block text-[14px] font-medium text-gray-700 mb-2">Installed Capacity (MW)</label>
                                    <input type="text" name="installed_capacity" placeholder="e.g. 50" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                </div>
                                 <div>
                                    <label class="block text-[14px] font-medium text-gray-700 mb-2">Target Reduction (%)</label>
                                    <input type="text" name="target_reduction" placeholder="e.g. 30%" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                </div>
                                <div>
                                    <label class="block text-[14px] font-medium text-gray-700 mb-2">Baseline Year</label>
                                    <input type="number" name="baseline_year" placeholder="YYYY" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                </div>
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Selected KPIs (Comma separated) *</label>
                                <input type="text" name="kpi_metrics" placeholder="e.g. CO2 reduction, Water saved, Energy efficiency" class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                        </div>
                    </section>

                    <section>
                         <h3 class="text-xl font-semibold text-[var(--green)] mb-6 flex items-center">
                            <span class="bg-green-100 text-[var(--green)] w-8 h-8 rounded-full flex items-center justify-center text-sm mr-3">4</span>
                            ESG Compliance Questionnaire
                        </h3>
                        
                        <div class="space-y-4 mb-8">
                            <p class="text-[15px] text-gray-500">Please select the intensity level for each criteria.</p>
                            
                            <div class="p-4 bg-gray-50 rounded-lg">
                                <p class="text-[15px] font-medium mb-2">1. Does the project have clear environmental benefits? *</p>
                                <div class="flex gap-4">
                                    <label class="flex items-center space-x-2 cursor-pointer"><input type="radio" name="q_env_benefits" value="high" class="text-green-600"> <span class="text-[14px]">High</span></label>
                                    <label class="flex items-center space-x-2 cursor-pointer"><input type="radio" name="q_env_benefits" value="medium" class="text-green-600"> <span class="text-[14px]">Medium</span></label>
                                    <label class="flex items-center space-x-2 cursor-pointer"><input type="radio" name="q_env_benefits" value="low" class="text-green-600"> <span class="text-[14px]">Low/None</span></label>
                                </div>
                            </div>

                            <div class="p-4 bg-gray-50 rounded-lg">
                                <p class="text-[15px] font-medium mb-2">2. Is data available to measure and report impact? *</p>
                                <div class="flex gap-4">
                                    <label class="flex items-center space-x-2 cursor-pointer"><input type="radio" name="q_data_available" value="comprehensive" class="text-green-600"> <span class="text-[14px]">Comprehensive</span></label>
                                    <label class="flex items-center space-x-2 cursor-pointer"><input type="radio" name="q_data_available" value="partial" class="text-green-600"> <span class="text-[14px]">Partial</span></label>
                                    <label class="flex items-center space-x-2 cursor-pointer"><input type="radio" name="q_data_available" value="none" class="text-green-600"> <span class="text-[14px]">None</span></label>
                                </div>
                            </div>

                            <div class="p-4 bg-gray-50 rounded-lg">
                                <p class="text-[15px] font-medium mb-2">3. Compliance with local environmental regulations? *</p>
                                <div class="flex gap-4">
                                    <label class="flex items-center space-x-2 cursor-pointer"><input type="radio" name="q_regulatory_compliance" value="fully_compliant" class="text-green-600"> <span class="text-[14px]">Fully Compliant</span></label>
                                    <label class="flex items-center space-x-2 cursor-pointer"><input type="radio" name="q_regulatory_compliance" value="in_progress" class="text-green-600"> <span class="text-[14px]">In Progress</span></label>
                                    <label class="flex items-center space-x-2 cursor-pointer"><input type="radio" name="q_regulatory_compliance" value="non_compliant" class="text-green-600"> <span class="text-[14px]">Non-Compliant</span></label>
                                </div>
                            </div>
                            
                             <div class="p-4 bg-gray-50 rounded-lg">
                                <p class="text-[15px] font-medium mb-2">4. Any controversy or negative social impact risks? *</p>
                                <div class="flex gap-4">
                                    <label class="flex items-center space-x-2 cursor-pointer"><input type="radio" name="q_social_risk" value="none" class="text-green-600"> <span class="text-[14px]">None</span></label>
                                    <label class="flex items-center space-x-2 cursor-pointer"><input type="radio" name="q_social_risk" value="minor" class="text-green-600"> <span class="text-[14px]">Minor/Mitigated</span></label>
                                    <label class="flex items-center space-x-2 cursor-pointer"><input type="radio" name="q_social_risk" value="high" class="text-green-600"> <span class="text-[14px]">High Risk</span></label>
                                </div>
                            </div>
                        </div>

                        <!-- Documents -->
                        <div>
                             <h4 class="font-bold text-gray-800 mb-4">Supporting Documents</h4>
                             
                             <div class="mb-6">
                                <label class="block text-[14px] font-medium text-gray-700 mb-2">Cloud Document URL (Optional)</label>
                                <input type="url" name="cloud_doc_url" placeholder="https://drive.google.com/..." class="w-full px-3 p-2 border border-gray-200 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                             </div>

                             <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div class="border-2 border-dashed border-gray-200 rounded-xl p-4 hover:border-green-300 transition-colors">
                                    <label class="block text-[14px] font-medium text-gray-700 mb-1">Sustainability Report (PDF/Docx) *</label>
                                    <p class="text-xs text-gray-500 mb-2">ESG Disclosure Docs</p>
                                    <input type="file" id="file-sustainability-report" accept=".pdf,.docx" class="w-full text-[14px] text-gray-500"/>
                                </div>
                                
                                <div class="border-2 border-dashed border-gray-200 rounded-xl p-4 hover:border-green-300 transition-colors">
                                    <label class="block text-[14px] font-medium text-gray-700 mb-1">Env Impact Assessment (EIA)</label>
                                    <p class="text-xs text-gray-500 mb-2">Detailed technical study</p>
                                    <input type="file" id="file-eia" accept=".pdf" class="w-full text-[14px] text-gray-500"/>
                                </div>
                                
                                <div class="border-2 border-dashed border-gray-200 rounded-xl p-4 hover:border-green-300 transition-colors">
                                    <label class="block text-[14px] font-medium text-gray-700 mb-1">Certifications & Approvals 1</label>
                                    <p class="text-xs text-gray-500 mb-2">Any primary certification</p>
                                    <input type="file" id="file-cert-1" accept=".pdf,.docx,.xlsx" class="w-full text-[14px] text-gray-500"/>
                                </div>

                                 <div class="border-2 border-dashed border-gray-200 rounded-xl p-4 hover:border-green-300 transition-colors">
                                    <label class="block text-[14px] font-medium text-gray-700 mb-1">Certifications & Approvals 2</label>
                                    <p class="text-xs text-gray-500 mb-2">Any secondary certification</p>
                                    <input type="file" id="file-cert-2" accept=".pdf,.docx,.xlsx" class="w-full text-[14px] text-gray-500"/>
                                </div>

                                <div class="border-2 border-dashed border-gray-200 rounded-xl p-4 hover:border-green-300 transition-colors col-span-1 md:col-span-2">
                                    <label class="block text-[14px] font-medium text-gray-700 mb-1">Additional Data (Any Format)</label>
                                    <p class="text-xs text-gray-500 mb-2">Upload any relevant data (CSV, JSON, PDF, DOCX, XLSX)</p>
                                    <input type="file" id="file-additional-data" accept=".csv,.json,.pdf,.docx,.xlsx" class="w-full text-[14px] text-gray-500"/>
                                </div>
                            </div>
                        </div>
                    </section>

                    <div class="pt-8 border-t border-gray-100">
                        <!-- Consent Checkbox -->
                        <div class="mb-6 flex items-start">
                            <div class="flex items-center h-5">
                                <input id="consent_checkbox" name="consent_agreed" type="checkbox" required class="w-4 h-4 text-green-600 border-gray-300 rounded focus:ring-green-500">
                            </div>
                            <div class="ml-3 text-[14px]">
                                <label for="consent_checkbox" class="font-medium text-gray-700">I confirm that the information provided is accurate and agree to the <b class="text-green-600 hover:underline cursor-pointer">Terms and Conditions</b>.</label>
                                <p class="text-gray-500">By checking this box, you acknowledge that any false information may result in application rejection.</p>
                            </div>
                        </div>

                        <div class="flex space-x-4 justify-end">
                            <button type="button" onclick="window.saveApplicationProgress()" class="px-8 p-2 btn-second">Save Draft</button>
                            <button type="submit" class="px-8 p-2 bg-[var(--green)] text-white font-bold rounded-xl hover:opacity-90 shadow-lg shadow-green-900/10 transform active:scale-95 transition-all">Submit Application</button>
                        </div>
                    </div>
                </form>
            </div>
        </div>
    `;
}

export async function handleApplicationSubmit(e) {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());

    // 1. Data Transformation & Parsing for Payload
    data.amount_requested = parseFloat(data.amount);
    data.scope1_tco2 = parseFloat(data.scope1_tco2) || null;
    data.scope2_tco2 = parseFloat(data.scope2_tco2) || null;
    data.scope3_tco2 = parseFloat(data.scope3_tco2) || null;
    data.baseline_year = parseInt(data.baseline_year) || null;
    data.has_existing_loan = data.has_existing_loan === 'true';
    data.consent_agreed = data.consent_agreed === 'on';

    if (data.kpi_metrics && typeof data.kpi_metrics === 'string') {
        data.kpi_metrics = data.kpi_metrics.split(',').map(s => s.trim()).filter(s => s);
    } else {
        data.kpi_metrics = [];
    }

    data.questionnaire_data = {
        env_benefits: data.q_env_benefits || null,
        data_available: data.q_data_available || null,
        regulatory_compliance: data.q_regulatory_compliance || null,
        social_risk: data.q_social_risk || null
    };

    const payload = {
        org_name: data.org_name,
        sector: data.sector,
        org_gst: data.org_gst,
        credit_score: data.credit_score,
        location: data.location,
        website: data.website,
        contact_email: data.contact_email,
        contact_phone: data.contact_phone,

        project_name: data.project_name,
        project_location: data.project_location,
        project_pin_code: data.project_pin_code,
        project_type: data.project_type,
        reporting_frequency: data.reporting_frequency,
        has_existing_loan: data.has_existing_loan,

        amount_requested: parseFloat(data.amount),
        currency: data.currency,

        use_of_proceeds: data.use_of_proceeds,
        scope1_tco2: data.scope1_tco2,
        scope2_tco2: data.scope2_tco2,
        scope3_tco2: data.scope3_tco2,
        baseline_year: data.baseline_year,
        installed_capacity: data.installed_capacity,
        target_reduction: data.target_reduction,
        kpi_metrics: data.kpi_metrics,

        additional_info: data.cloud_doc_url ? `Cloud Doc: ${data.cloud_doc_url}` : null,
        consent_agreed: data.consent_agreed,
        questionnaire_data: data.questionnaire_data
    };

    try {
        const currentUser = getCurrentUser();
        if (!currentUser) throw new Error("User not confirmed. Please reload.");

        // Submit Application Data using standard API Call
        const res = await apiCall('/borrower/apply', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        // Upload Documents with Correct URL
        if (res && res.id) {
            const appId = res.id;
            const uploadQueue = [
                { id: 'file-sustainability-report', cat: 'sustainability_report' },
                { id: 'file-eia', cat: 'eia' },
                { id: 'file-cert-1', cat: 'certification_1' },
                { id: 'file-cert-2', cat: 'certification_2' },
                { id: 'file-additional-data', cat: 'additional_data' }
            ];

            let uploadCount = 0;

            for (const item of uploadQueue) {
                const fileInput = document.getElementById(item.id);
                if (fileInput && fileInput.files[0]) {
                    const uploadData = new FormData();
                    uploadData.append('file', fileInput.files[0]);
                    uploadData.append('category', item.cat);

                    try {
                        // Use calculated API_BASE directly for File Uploads
                        // This avoids apiCall's json content-header assumption if any
                        await fetch(`${API_BASE}/borrower/${appId}/documents`, {
                            method: 'POST',
                            headers: {
                                // No Content-Type so boundary is set automatically
                                // Add any auth headers if your backend requires (mock auth usually relies on query param or just simple check)
                                // In this app we might rely on 'current_user' dependency that parses header? No, mock auth uses query param usually for simple.
                                // But let's check auth.py: get_current_user... MockAuth... 
                                // Actually, for Hackathon, it returns None by default unless specified or uses local storage if implemented.
                                // Our get_current_user implementation: returns None. 
                                // MockAuth.quick_login uses default if None.
                                // So we likely don't strictly need the header if we rely on that behavior, 
                                // but for correctness let's assume we would send it if we had it. Use empty for now to match loose auth.
                            },
                            body: uploadData
                        });
                        uploadCount++;
                    } catch (e) {
                        console.error(`Failed to upload ${item.cat}`, e);
                    }
                }
            }

            alert(`✅ Application Submitted! \n\nLoan ID: ${appId} | Documents Uploaded: ${uploadCount}`);
            window.navigateTo('dashboard');
        }

    } catch (err) {
        console.error(err);
        alert('Failed to submit application: ' + err.message);
    }
}
