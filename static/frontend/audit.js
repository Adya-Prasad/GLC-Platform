import { apiCall, getStatusClass, formatCurrency, showModal } from './utils.js';

let currentTab = 'general';
let analysisData = null;

export async function renderAuditPage() {
    const appId = window.currentAuditAppId;
    if (!appId) {
        return `<div class="p-8 text-center">No application selected. <button onclick="window.navigateTo('applications')" class="text-green-600 font-bold">Go back to applications</button></div>`;
    }

    try {
        analysisData = await apiCall(`/analysis/loan/${appId}/full`);
    } catch (e) {
        console.error(e);
        return `<div class="p-8 text-center text-red-500">Error loading audit data: ${e.message}</div>`;
    }

    const h = analysisData.header;
    const user = JSON.parse(localStorage.getItem('glc_user'));
    const isLender = user?.role === 'lender';

    return `
        <div class="space-y-6 animate-in fade-in duration-300">
            <!-- Header -->
            <div class="info-header">
                <div class="flex flex-wrap justify-between items-start gap-4">
                    <div class="flex-1">
                        <div class="flex items-center gap-3 mb-2">
                            <span class="px-3 py-2 cursor-progress rounded-full text-xs font-bold uppercase ${getStatusClass(h.status)}">${h.status}</span>
                            <span class="text-sm text-gray-500 font-mono">${analysisData.loan_id_str || 'LOAN-' + appId}</span>
                        </div>
                        <h1 class="text-xl font-bold text-[var(--green)]">${h.project_name}</h1>
                        <p class="text-gray-600 text-[15px]">${h.org_name}</p>
                        <div class="flex gap-4 mt-3 text-sm text-gray-600">
                            <span><strong>Sector:</strong> ${h.sector || '-'}</span>
                            <span><strong>Shareholders:</strong> ${h.shareholder_entities}</span>
                        </div>
                    </div>
                    <div class="text-right">
                        <p class="text-gray-600 text-[15px]">Loan Amount</p>
                        <p class="text-2xl font-bold text-amber-700">${formatCurrency(h.amount_requested, h.currency)}</p>
                    </div>
                </div>
            </div>

            <!-- Tabs -->
            <div class="overflow-hidden">
                <div class="flex bg-green-800 mb-4 overflow-x-auto rounded-md" id="tab-buttons">
                    ${renderTabButton('general', 'General Info', 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z')}
                    ${renderTabButton('esg', 'ESG Analysis', 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z')}
                    ${renderTabButton('ai', 'AI Insight', 'M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z')}
                    ${renderTabButton('decision', 'Decision', 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z')}
                </div>
                <div id="tab-content">${renderTabContent('general')}</div>
            </div>

        </div>
    `;
}

function renderTabButton(id, label, icon) {
    const isActive = currentTab === id;
    return `<button onclick="window.switchAuditTab('${id}')" class="flex items-center gap-2 px-5 py-4 text-sm font-medium whitespace-nowrap ${isActive ? 'text-white bg-green-800 ' : 'text-gray-400 hover:text-green-800 hover:bg-[var(--main-bg)] hover: border-y-2 border-green-800 '}">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${icon}"/></svg>
        ${label}
    </button>`;
}

function renderTabContent(tab) {
    if (!analysisData) return '<p>Loading...</p>';
    switch (tab) {
        case 'general': return renderGeneralTab();
        case 'esg': return renderESGTab();
        case 'ai': return renderAITab();
        case 'decision': return renderDecisionTab();
        default: return '<p>Tab not found</p>';
    }
}


// ============ GENERAL INFO TAB ============
function renderGeneralTab() {
    const g = analysisData.general_info;
    const org = g.organization || {};
    const proj = g.project || {};
    const quest = g.questionnaire || {};
    const logs = analysisData.audit_logs || [];

    return `
        <div class="space-y-6">
        <div class="columns-2 text-[14px]">
            <!-- Organization Details Table -->
            <div class="bg-white rounded-xl border border-[color:var(--border-color)] overflow-hidden">
                <div class="bg-gray-50 px-5 py-3 border-b">
                    <h3 class="font-bold text-gray-800">Organization / Company Details</h3>
                </div>
                <table class="w-full text-sm">
                    <tbody>
                        ${renderTableRow('Organization Name', org.org_name)}
                        ${renderTableRow('Sector / Industry', org.sector)}
                        ${renderTableRow('Headquarters Location', org.location)}
                        ${renderTableRow('Contact Email', org.contact_email)}
                        ${renderTableRow('Contact Phone', org.contact_phone)}
                        ${renderTableRow('Tax ID / GST', org.tax_id)}
                        ${renderTableRow('Credit Score', org.credit_score)}
                        ${renderTableRow('Website', org.website, 'link')}
                        ${renderTableRow('Annual Revenue', org.annual_revenue ? formatCurrency(org.annual_revenue, 'USD') : null)}
                    </tbody>
                </table>
            </div>

            <!-- Project Information Table -->
            <div class="bg-white rounded-xl border border-[color:var(--border-color)] overflow-hidden">
                <div class="bg-gray-50 px-5 py-3 border-b">
                    <h3 class="font-bold text-gray-800">Project / Loan Information</h3>
                </div>
                <table class="w-full text-sm">
                    <tbody>
                        ${renderTableRow('Project Name', proj.project_name)}
                        ${renderTableRow('Project Sector', proj.project_sector || org.sector)}
                        ${renderTableRow('Project Type', proj.project_type)}
                        ${renderTableRow('Project Location', proj.project_location)}
                        ${renderTableRow('Project PIN/ZIP Code', proj.project_pin_code)}
                        ${renderTableRow('Planned Start Date', proj.planned_start_date)}
                        ${renderTableRow('Amount Requested', proj.amount_requested ? formatCurrency(proj.amount_requested, proj.currency || 'USD') : null)}
                        ${renderTableRow('Loan Tenor', proj.loan_tenor ? proj.loan_tenor + ' months' : null)}
                        ${renderTableRow('Reporting Frequency', proj.reporting_frequency)}
                        ${renderTableRow('Existing Loans', proj.existing_loans)}
                        ${renderTableRow('Shareholder Entities', proj.shareholder_entities)}
                    </tbody>
                </table>

            </div>
            </div>

            <div class="columns-2 text-[14px]">
                <div class="px-5 py-4 bg-white mb-6 rounded-xl border border-[color:var(--border-color)]">
                    <p class="font-medium text-gray-500 mb-2">Project Description</p>
                    <p class="text-gray-800 leading-relaxed">${proj.project_description || '-'}</p>
                </div>
                <div class="px-5 py-4 bg-white rounded-xl border border-[color:var(--border-color)]">
                    <p class="font-medium text-gray-500 mb-2 ">Use of Proceeds</p>
                    <p class="text-gray-800 leading-relaxed">${proj.use_of_proceeds || '-'}</p>
                </div>

                <div class="bg-white rounded-xl border overflow-hidden border-[color:var(--border-color)]">
                    <div class="bg-gray-50 px-5 py-3 border-b">
                        <h3 class="font-bold text-gray-800">ESG Compliance Questionnaire</h3>
                    </div>
                    <table class="w-full text-sm">
                        <tbody>
                            ${Object.entries(quest).map(([k, v]) => `
                                <tr class="border-b last:border-b-0 hover:bg-gray-50">
                                    <td class="px-3 py-2 text-gray-600 w-3/4">${formatQuestionKey(k)}</td>
                                    <td class="px-3 py-2 text-right font-medium ${v === 'yes' || v === 'fully_compliant' ? 'text-green-600' : v === 'no' || v === 'non_compliant' ? 'text-red-600' : 'text-gray-800'}">${v || '-'}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Audit Trail  -->
            <div class="bg-white rounded-xl p-6 border">
                <h3 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
                    <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    Audit Trail Acttions History
                </h3>
                ${logs.length ? `
                <div class="relative border-l-2 border-gray-200 ml-3 space-y-4 pl-6 max-h-64 overflow-y-auto">
                    ${logs.slice(0, 10).map(log => `
                        <div class="relative">
                            <span class="absolute -left-[29px] bg-white border-2 border-green-500 w-4 h-4 rounded-full"></span>
                            <div class="flex flex-col">
                                <span class="text-xs font-bold text-green-700 uppercase">${log.action}</span>
                                <span class="text-xs text-gray-500 font-mono">${new Date(log.timestamp).toLocaleString()}</span>
                                <div class="bg-gray-50 border rounded p-2 text-xs font-mono text-gray-600 mt-1">${JSON.stringify(log.data)}</div>
                            </div>
                        </div>
                    `).join('')}
                </div>` : '<p class="text-gray-500 text-sm">No audit history found.</p>'}
            </div>
        </div>
    `;
}

function renderTableRow(label, value, type = 'text') {
    const displayValue = value || '-';
    let valueHtml = `<span class="text-gray-800">${displayValue}</span>`;
    
    if (type === 'link' && value) {
        valueHtml = `<a href="${value}" target="_blank" class="text-blue-600 hover:underline">${value}</a>`;
    }
    
    return `
        <tr class="border-b last:border-b-0 hover:bg-gray-50">
            <td class="px-3 py-2 text-gray-500 w-1/3">${label}</td>
            <td class="px-3 py-2 font-medium">${valueHtml}</td>
        </tr>
    `;
}

function formatQuestionKey(key) {
    // Remove number prefix like "1_", "2_" etc and clean up
    return key
        .replace(/^\d+_/, '')
        .replace(/_/g, ' ')
        .replace(/\?$/, '?')
        .replace(/\b\w/g, c => c.toUpperCase());
}


// ============ ESG ANALYSIS TAB ============
function renderESGTab() {
    const esg = analysisData.esg_analysis;
    const dnsh = esg.dnsh_summary || {};
    const risk = esg.sector_risk || {};
    const kpis = analysisData.general_info?.green_kpis || {};
    const proj = analysisData.general_info?.project || {};
    const pincode = proj.project_pin_code || '';

    return `
        <div class="space-y-6">
            <!-- Project Location Map & Environmental Data Section -->
            <div class="grid grid-cols-1 lg:grid-cols-10 gap-4">
                <!-- Map Section (60%) -->
                <div class="lg:col-span-7 bg-white rounded-xl border overflow-hidden">
                    <div class="bg-gradient-to-r from-yellow-600 to-orange-800 px-4 py-2 flex justify-between items-center">
                        <h3 class="font-bold text-white text-sm flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
                            Project Location
                        </h3>
                        <span class="text-xs text-blue-100">${proj.project_location || ''} ${pincode ? '(' + pincode + ')' : ''}</span>
                    </div>
                    <div id="project-map" class="bg-gray-100 relative" style="height: 500px;">
                        <div id="map-loading" class="absolute inset-0 flex items-center justify-center bg-gray-50">
                            <div class="text-center">
                                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-2"></div>
                                <p class="text-sm text-gray-500">Loading map...</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Green / Red Indicators (40%) -->
                <div class="lg:col-span-3 space-y-4">
                    <div class="bg-green-100 rounded-xl p-5 border border-[color:var(--green)]">
                        <h4 class="font-bold text-green-800 mb-3">✓ Green Indicators</h4>
                        <div class="flex flex-wrap gap-2">${(esg.green_indicators || []).length ? esg.green_indicators.map(g => `<span class="bg-green-200 text-green-800 px-3 py-1 rounded-full text-sm">${g}</span>`).join('') : '<span class="text-gray-500 text-sm">None identified</span>'}</div>
                    </div>
                    <div class="bg-red-100 rounded-xl p-5 border border-red-200">
                        <h4 class="font-bold text-red-800 mb-3">✗ Red Flags</h4>
                        <div class="flex flex-wrap gap-2">${(esg.red_flags || []).length ? esg.red_flags.map(r => `<span class="bg-red-200 text-red-800 px-3 py-1 rounded-full text-sm">${r}</span>`).join('') : '<span class="text-gray-500 text-sm">None identified</span>'}</div>
                    </div>
                    ${kpis.kpi_metrics?.length ? `
                    <div class="mt-4 p-5 bg-white rounded-lg border border-[color:var(--green)]">
                        <p class="text-xs text-gray-500 mb-2">Selected KPI Metrics</p>
                        <div class="flex flex-wrap gap-2">
                            ${kpis.kpi_metrics.map(k => `<span class="bg-green-800/30 text-green-800 px-3 py-1 rounded-full text-sm font-medium">${k}</span>`).join('')}
                        </div>
                    </div>` : ''}
                </div>
            </div>

            <!-- Top Row: Score + GLP + Risk Meter -->
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <!-- ESG Score Card - Professional Design -->
                <div class="bg-gradient-to-br from-green-50 to-emerald-100 rounded-xl border border-green-200 overflow-hidden">
                    <div class="bg-gradient-to-r from-emerald-600 to-green-600 px-4 py-2">
                        <p class="text-sm text-white font-medium flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
                            ESG Composite Score
                        </p>
                    </div>
                    <div class="p-5 text-center">
                        ${renderESGScoreGauge(esg.esg_score)}
                        <div class="mt-3 grid grid-cols-3 gap-2 text-xs">
                            <div class="text-center">
                                <div class="w-2 h-2 rounded-full bg-red-500 mx-auto mb-1"></div>
                                <span class="text-gray-500">0-49</span>
                            </div>
                            <div class="text-center">
                                <div class="w-2 h-2 rounded-full bg-yellow-500 mx-auto mb-1"></div>
                                <span class="text-gray-500">50-69</span>
                            </div>
                            <div class="text-center">
                                <div class="w-2 h-2 rounded-full bg-green-500 mx-auto mb-1"></div>
                                <span class="text-gray-500">70-100</span>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- GLP Eligibility Card - Professional Design -->
                <div class="bg-white rounded-xl border border-[color:var(--border-color)] overflow-hidden">
                    <div class="bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2">
                        <p class="text-sm text-white font-medium flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                            GLP Eligibility Status
                        </p>
                    </div>
                    <div class="p-5">
                        <div class="flex items-center gap-4 mb-4">
                            <div class="w-14 h-14 rounded-full flex items-center justify-center ${esg.glp_eligibility ? 'bg-green-100 border-2 border-green-500' : 'bg-red-100 border-2 border-red-400'}">
                                ${esg.glp_eligibility ? 
                                    '<svg class="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg>' : 
                                    '<svg class="w-8 h-8 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/></svg>'}
                            </div>
                            <div>
                                <p class="text-lg font-bold ${esg.glp_eligibility ? 'text-green-700' : 'text-red-600'}">${esg.glp_eligibility ? 'Eligible' : 'Not Eligible'}</p>
                                <p class="text-sm text-gray-600">${esg.glp_category || 'Pending Classification'}</p>
                            </div>
                        </div>
                        <div class="space-y-2">
                            <div class="flex justify-between text-sm">
                                <span class="text-gray-500">Confidence Level</span>
                                <span class="font-medium ${(esg.glp_confidence || 0) >= 0.7 ? 'text-green-600' : (esg.glp_confidence || 0) >= 0.4 ? 'text-yellow-600' : 'text-red-500'}">${Math.round((esg.glp_confidence || 0) * 100)}%</span>
                            </div>
                            <div class="bg-gray-200 rounded-full h-2 overflow-hidden">
                                <div class="h-full transition-all duration-500 ${(esg.glp_confidence || 0) >= 0.7 ? 'bg-green-500' : (esg.glp_confidence || 0) >= 0.4 ? 'bg-yellow-500' : 'bg-red-400'}" style="width: ${(esg.glp_confidence || 0) * 100}%"></div>
                            </div>
                            <p class="text-xs text-gray-400 mt-2">${esg.glp_eligibility ? 'Meets LMA Green Loan Principles criteria' : 'Review use of proceeds and project details'}</p>
                        </div>
                    </div>
                </div>
                
                <!-- Sector Risk Card -->
                <div class="bg-white rounded-xl border border-[color:var(--border-color)] overflow-hidden">
                    <div class="bg-gradient-to-r from-amber-500 to-orange-500 px-4 py-2">
                        <p class="text-sm text-white font-medium flex items-center gap-2">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
                            Sector Risk Assessment
                        </p>
                    </div>
                    <div class="p-5">
                        ${renderRiskMeter(risk.score || 50, risk.label || 'Medium Risk')}
                        <p class="text-xs text-gray-600 mt-3 text-center leading-relaxed">${risk.description || 'Risk assessment based on industry sector classification'}</p>
                    </div>
                </div>
            </div>
            
            <!-- Environment Sustainability Section -->
            <div class="grid grid-cols-2 gap-5">
                    <!-- Climate Data Table -->
                    <div class="bg-white rounded-xl border overflow-hidden">
                        <div class="bg-gradient-to-r from-cyan-500 to-blue-500 px-4 py-2">
                            <h3 class="font-bold text-white text-sm flex items-center gap-2">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"/></svg>
                                Climate Data
                            </h3>
                        </div>
                        <div id="climate-table" class="p-3">
                            <div class="flex items-center justify-center py-6">
                                <div class="animate-pulse text-gray-400 text-sm">Loading climate data...</div>
                            </div>
                        </div>
                    </div>

                    <!-- Gaseous Breakdown Table -->
                    <div class="bg-white rounded-xl border overflow-hidden">
                        <div class="bg-gradient-to-r from-emerald-500 to-teal-500 px-4 py-2">
                            <h3 class="font-bold text-white text-sm flex items-center gap-2">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>Gaseous Breakdowns
                            </h3>
                        </div>
                        <div id="air-quality-table" class="p-3">
                            <div class="flex items-center justify-center py-6">
                                <div class="animate-pulse text-gray-400 text-sm">Loading air quality data...</div>
                            </div>
                        </div>
                    </div>
                </div>

            <!-- Green KPIs & Emissions Section with charts and graphs  -->

            <!-- Emissions Reduction Chart -->
            <div class="rounded-xl border overflow-hidden">
                <div class="bg-gradient-to-r from-[#059669] to-[#4c7d3a] px-5 py-3">
                    <h3 class="font-bold text-white flex items-center gap-2">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"/></svg>
                        Emissions Reduction Pathway</h3>
                </div>
            <div class="grid grid-cols-2">
                <div class="p-5 bg-white">
                    <div id="emissions-chart" class="h-64">
                        ${renderEmissionsReductionChart(kpis)}
                    </div>
                    <div class="flex justify-center gap-6 mt-4 text-sm">
                        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-blue-500"></span> Scope 1</div>
                        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-green-500"></span> Scope 2</div>
                        <div class="flex items-center gap-2"><span class="w-3 h-3 rounded-full bg-amber-500"></span> Scope 3</div>
                    </div>
                </div>
                
                <div>
                <div class="bg-white px-5 py-3 border-b">
                    <h3 class="font-bold text-emerald-800">Green KPIs & Emissions Data</h3>
                </div>
                <div class="p-3 mt-3">
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                        <div class="bg-blue-700/30 rounded-lg p-4 text-center">
                            <p class="text-xs text-blue-600 font-medium">Scope 1</p>
                            <p class="text-2xl font-bold text-blue-700">${kpis.scope1_tco2 || 0}</p>
                            <p class="text-xs text-gray-500">tCO₂e</p>
                        </div>
                        <div class="bg-green-700/30 rounded-lg p-4 text-center">
                            <p class="text-xs text-green-600 font-medium">Scope 2</p>
                            <p class="text-2xl font-bold text-green-700">${kpis.scope2_tco2 || 0}</p>
                            <p class="text-xs text-gray-500">tCO₂e</p>
                        </div>
                        <div class="bg-yellow-700/30 rounded-lg p-4 text-center">
                            <p class="text-xs text-yellow-600 font-medium">Scope 3</p>
                            <p class="text-2xl font-bold text-yellow-700">${kpis.scope3_tco2 || 0}</p>
                            <p class="text-xs text-gray-500">tCO₂e</p>
                        </div>
                        <div class="bg-white rounded-lg p-4 text-center border border-[color:var(--border-color)]">
                            <p class="text-xs text-purple-600 font-medium">Total</p>
                            <p class="text-2xl font-bold text-purple-700">${(kpis.scope1_tco2 || 0) + (kpis.scope2_tco2 || 0) + (kpis.scope3_tco2 || 0)}</p>
                            <p class="text-xs text-gray-500">tCO₂e</p>
                        </div>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                        <div class="flex justify-between p-3 bg-white rounded-lg border border-[color:var(--border-color)]">
                            <span class="text-gray-600 text-sm">Target Year</span>
                            <span class="font-bold text-gray-800">${kpis.baseline_year || '-'}</span>
                        </div>
                        <div class="flex justify-between p-3 bg-white rounded-lg border border-[color:var(--border-color)]">
                            <span class="text-gray-600 text-sm">Target Reduction</span>
                            <span class="font-bold text-gray-800">${kpis.target_reduction ? kpis.target_reduction + '%' : '-'}</span>
                        </div>
                        <div class="flex justify-between p-3 bg-white rounded-lg border border-[color:var(--border-color)]">
                            <span class="text-gray-600 text-sm">Reporting Frequency</span>
                            <span class="font-bold text-gray-800">${kpis.reporting_frequency || '-'}</span>
                        </div>
                    </div>
                </div>
                </div>

            </div>
            </div>

            <!-- DNSH Assessment -->
            <div class="bg-white rounded-xl p-6 border border-[color:var(--border-color)]">
                <h3 class="font-bold text-gray-800 mb-4">DNSH Assessment (Do No Significant Harm)</h3>
                <div class="flex items-center gap-4 mb-4">
                    <span class="px-4 py-2 rounded-lg font-bold ${dnsh.overall_pass ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">${dnsh.overall_pass ? '✓ DNSH Passed' : '✗ DNSH Failed'}</span>
                    <span class="text-sm text-gray-600">Passed: ${dnsh.passed_count || 0} | Failed: ${dnsh.failed_count || 0} | Unclear: ${dnsh.unclear_count || 0}</span>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                    ${Object.entries(dnsh.results || {}).map(([key, val]) => `<div class="p-3 rounded-lg border ${val.status === 'pass' ? 'bg-green-100/80 border-green-300' : val.status === 'fail' ? 'bg-red-100/80 border-red-300' : 'bg-amber-100/80 border-amber-300'}"><p class="font-medium text-sm capitalize">${key.replace(/_/g, ' ')}</p><p class="text-xs mt-1 ${val.status === 'pass' ? 'text-green-700' : val.status === 'fail' ? 'text-red-700' : 'text-yellow-700'}">${val.status.toUpperCase()}</p></div>`).join('')}
                </div>
            </div>  

            <!-- Carbon Lock-in Risk -->
            <div class="bg-white rounded-xl p-6 border border-[color:var(--border-color)]">
                <h3 class="font-bold text-gray-800 mb-4">Carbon Lock-in Risk</h3>
                <span class="px-3 py-1 rounded-full text-sm font-bold ${esg.carbon_lockin?.risk_level === 'low' ? 'bg-green-100 text-green-700' : esg.carbon_lockin?.risk_level === 'high' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}">${(esg.carbon_lockin?.risk_level || 'unknown').toUpperCase()}</span>
                <p class="text-sm text-gray-600 mt-3">${esg.carbon_lockin?.assessment || 'Assessment pending'}</p>
                <p class="text-xs text-blue-600 mt-2">${esg.carbon_lockin?.recommendation || ''}</p>
            </div>

            <!-- LMA GLP Four Core Components Compliance -->
            ${renderGLPComplianceSection(esg.glp_compliance)}

            <!-- SLL Compliance (if applicable) -->
            ${esg.sll_compliance?.applicable ? renderSLLComplianceSection(esg.sll_compliance) : ''}
        </div>
    `;
}

function renderGLPComplianceSection(glp) {
    if (!glp) return '';
    const components = glp.components || {};
    
    return `
        <div class="bg-white rounded-xl border overflow-hidden">
            <div class="bg-gradient-to-r from-[#059669] to-[#4c7d3a] px-5 py-3 flex justify-between items-center">
                <h3 class="font-bold text-white flex items-center gap-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/></svg>
                    LMA Green Loan Principles - Four Core Components
                </h3>
                <span class="px-3 py-1 rounded-full text-sm font-bold ${glp.overall_compliant ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}">
                    ${glp.score}/${glp.max_score} Compliant
                </span>
            </div>
            <div class="p-5">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    ${renderGLPComponent('Use of Proceeds', components.use_of_proceeds, '💰')}
                    ${renderGLPComponent('Project Evaluation', components.project_evaluation, '📋')}
                    ${renderGLPComponent('Management of Proceeds', components.management_of_proceeds, '🏦')}
                    ${renderGLPComponent('Reporting', components.reporting, '📊')}
                </div>
                <div class="mt-4 pt-4 border-t">
                    <div class="flex items-center gap-3">
                        <span class="text-sm text-gray-600">Overall GLP Compliance:</span>
                        <div class="flex-1 bg-gray-100 rounded-full h-3 overflow-hidden">
                            <div class="h-full ${glp.percentage >= 75 ? 'bg-[color:var(--green)]' : glp.percentage >= 50 ? 'bg-yellow-500' : 'bg-red-500'}" style="width: ${glp.percentage}%"></div>
                        </div>
                        <span class="font-bold ${glp.percentage >= 75 ? 'text-green-600' : glp.percentage >= 50 ? 'text-yellow-600' : 'text-red-600'}">${glp.percentage}%</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderGLPComponent(name, comp, icon) {
    if (!comp) return '';
    return `
        <div class="p-4 rounded-lg border ${comp.compliant ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}">
            <div class="flex items-center gap-2 mb-2">
                <span class="text-xl">${icon}</span>
                <span class="${comp.compliant ? 'text-green-600' : 'text-gray-400'}">${comp.compliant ? '✓' : '○'}</span>
            </div>
            <p class="font-medium text-sm ${comp.compliant ? 'text-green-800' : 'text-gray-600'}">${name}</p>
            <p class="text-xs text-gray-500 mt-1 line-clamp-2">${comp.details || ''}</p>
        </div>
    `;
}

function renderSLLComplianceSection(sll) {
    if (!sll || !sll.applicable) return '';
    const components = sll.components || {};
    
    return `
        <div class="bg-white rounded-xl border overflow-hidden">
            <div class="bg-gradient-to-r from-indigo-600 to-blue-600 px-5 py-3 flex justify-between items-center">
                <h3 class="font-bold text-white flex items-center gap-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                    LMA Sustainability-Linked Loan Principles
                </h3>
                <span class="px-3 py-1 rounded-full text-sm font-bold bg-purple-100 text-purple-800">
                    ${sll.score}/${sll.max_score} Components
                </span>
            </div>
            <div class="p-5">
                <div class="grid grid-cols-2 md:grid-cols-5 gap-3">
                    ${renderSLLComponent('KPI Selection', components.kpi_selection)}
                    ${renderSLLComponent('SPT Calibration', components.spt_calibration)}
                    ${renderSLLComponent('Loan Characteristics', components.loan_characteristics)}
                    ${renderSLLComponent('Reporting', components.reporting)}
                    ${renderSLLComponent('Verification', components.verification)}
                </div>
            </div>
        </div>
    `;
}

function renderSLLComponent(name, comp) {
    if (!comp) return '';
    return `
        <div class="p-3 rounded-lg border text-center ${comp.compliant ? 'bg-indigo-100 border-indigo-200' : 'bg-slate-100 border-gray-200'}">
            <span class="text-lg ${comp.compliant ? 'text-purple-600' : 'text-gray-400'}">${comp.compliant ? '✓' : '○'}</span>
            <p class="font-medium text-xs mt-1 ${comp.compliant ? 'text-indigo-800' : 'text-gray-700'}">${name}</p>
        </div>
    `;
}

function renderRiskMeter(score, label) {
    const angle = -90 + (score / 100) * 180;
    return `<div class="flex flex-col items-center">
        <svg viewBox="0 0 200 120" class="w-full max-w-[200px]">
            <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#e5e7eb" stroke-width="20" stroke-linecap="round"/>
            <path d="M 20 100 A 80 80 0 0 1 60 35" fill="none" stroke="#22c55e" stroke-width="20" stroke-linecap="round"/>
            <path d="M 60 35 A 80 80 0 0 1 140 35" fill="none" stroke="#eab308" stroke-width="20"/>
            <path d="M 140 35 A 80 80 0 0 1 180 100" fill="none" stroke="#ef4444" stroke-width="20" stroke-linecap="round"/>
            <g transform="rotate(${angle}, 100, 100)">
                <line x1="100" y1="100" x2="100" y2="35" stroke="#1f2937" stroke-width="3" stroke-linecap="round"/>
                <circle cx="100" cy="100" r="8" fill="#2a3546ff"/>
            </g>
            <text x="100" y="95" text-anchor="middle" class="text-2xl font-bold" fill="#1f2937">${score}</text>
        </svg>
        <p class="font-bold mt-2" style="color: ${score <= 33 ? '#22c55e' : score <= 66 ? '#eab308' : '#ef4444'}">${label}</p>
    </div>`;
}

// ESG Score Gauge - Professional circular gauge
function renderESGScoreGauge(score) {
    const displayScore = score !== null && score !== undefined ? score : 0;
    const hasScore = score !== null && score !== undefined;
    
    // Calculate color based on score
    let color, bgColor, label;
    if (!hasScore) {
        color = '#9ca3af';
        bgColor = '#f3f4f6';
        label = 'Pending';
    } else if (displayScore >= 70) {
        color = '#22c55e';
        bgColor = '#dcfce7';
        label = 'Strong';
    } else if (displayScore >= 50) {
        color = '#eab308';
        bgColor = '#fef9c3';
        label = 'Moderate';
    } else {
        color = '#ef4444';
        bgColor = '#fee2e2';
        label = 'Needs Improvement';
    }
    
    // Calculate stroke dasharray for circular progress
    const circumference = 2 * Math.PI * 45;
    const progress = hasScore ? (displayScore / 100) * circumference : 0;
    
    return `
        <div class="relative inline-flex items-center justify-center">
            <svg class="w-32 h-32 transform -rotate-90">
                <circle cx="64" cy="64" r="45" stroke="#e5e7eb" stroke-width="10" fill="none"/>
                <circle cx="64" cy="64" r="45" stroke="${color}" stroke-width="10" fill="none" 
                    stroke-dasharray="${circumference}" 
                    stroke-dashoffset="${circumference - progress}"
                    stroke-linecap="round"
                    class="transition-all duration-1000"/>
            </svg>
            <div class="absolute flex flex-col items-center justify-center">
                <span class="text-3xl font-bold" style="color: ${color}">${hasScore ? displayScore : 'N/A'}</span>
                <span class="text-xs text-gray-500">${hasScore ? '/100' : ''}</span>
            </div>
        </div>
        <p class="mt-2 text-sm font-medium" style="color: ${color}">${label}</p>
        ${!hasScore ? '<p class="text-xs text-gray-400 mt-1">Complete questionnaire for score</p>' : ''}
    `;
}

// Emissions Reduction Chart using SVG
function renderEmissionsReductionChart(kpis) {
    const scope1 = kpis.scope1_tco2 || 0;
    const scope2 = kpis.scope2_tco2 || 0;
    const scope3 = kpis.scope3_tco2 || 0;
    const targetReduction = kpis.target_reduction || 30;
    const baselineYear = kpis.baseline_year || new Date().getFullYear() + 5;
    const currentYear = new Date().getFullYear();
    
    if (scope1 === 0 && scope2 === 0 && scope3 === 0) {
        return `<div class="flex items-center justify-center h-full text-gray-500">
            <div class="text-center">
                <svg class="w-12 h-12 mx-auto mb-2 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/></svg>
                <p>No emissions data available</p>
                <p class="text-xs mt-1">Add scope emissions in the application form</p>
            </div>
        </div>`;
    }
    
    const reductionFactor = (100 - targetReduction) / 100;
    const scope1Target = Math.round(scope1 * reductionFactor);
    const scope2Target = Math.round(scope2 * reductionFactor);
    const scope3Target = Math.round(scope3 * reductionFactor);
    
    const maxValue = Math.max(scope1, scope2, scope3, 1);
    const chartWidth = 700;
    const chartHeight = 200;
    const padding = 50;
    const graphHeight = chartHeight - padding;
    
    const scaleY = (val) => chartHeight - padding - (val / maxValue) * graphHeight;
    
    return `
        <svg viewBox="0 0 ${chartWidth} ${chartHeight}" class="w-full h-full">
            <!-- Grid lines -->
            <g stroke="#e5e7eb" stroke-width="1">
                ${[0, 0.25, 0.5, 0.75, 1].map(p => `
                    <line x1="${padding}" y1="${scaleY(maxValue * p)}" x2="${chartWidth - padding}" y2="${scaleY(maxValue * p)}" stroke-dasharray="4"/>
                `).join('')}
            </g>
            
            <!-- Y-axis labels -->
            <g fill="#6b7280" font-size="10">
                <text x="${padding - 5}" y="${scaleY(maxValue)}" text-anchor="end" dominant-baseline="middle">${maxValue}</text>
                <text x="${padding - 5}" y="${scaleY(maxValue * 0.5)}" text-anchor="end" dominant-baseline="middle">${Math.round(maxValue * 0.5)}</text>
                <text x="${padding - 5}" y="${scaleY(0)}" text-anchor="end" dominant-baseline="middle">0</text>
            </g>
            
            <!-- X-axis labels -->
            <g fill="#6b7280" font-size="11">
                <text x="${padding}" y="${chartHeight - 10}" text-anchor="middle">${currentYear}</text>
                <text x="${chartWidth - padding}" y="${chartHeight - 10}" text-anchor="middle">${baselineYear}</text>
            </g>
            
            <!-- Area fills -->
            <defs>
                <linearGradient id="scope1Grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#3b82f6;stop-opacity:0.3"/>
                    <stop offset="100%" style="stop-color:#3b82f6;stop-opacity:0.05"/>
                </linearGradient>
                <linearGradient id="scope2Grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#22c55e;stop-opacity:0.3"/>
                    <stop offset="100%" style="stop-color:#22c55e;stop-opacity:0.05"/>
                </linearGradient>
                <linearGradient id="scope3Grad" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" style="stop-color:#f59e0b;stop-opacity:0.3"/>
                    <stop offset="100%" style="stop-color:#f59e0b;stop-opacity:0.05"/>
                </linearGradient>
            </defs>
            
            <!-- Scope 1 Area -->
            <path d="M ${padding} ${scaleY(scope1)} L ${chartWidth - padding} ${scaleY(scope1Target)} L ${chartWidth - padding} ${scaleY(0)} L ${padding} ${scaleY(0)} Z" fill="url(#scope1Grad)"/>
            <line x1="${padding}" y1="${scaleY(scope1)}" x2="${chartWidth - padding}" y2="${scaleY(scope1Target)}" stroke="#3b82f6" stroke-width="3"/>
            
            <!-- Scope 2 Area -->
            <path d="M ${padding} ${scaleY(scope2)} L ${chartWidth - padding} ${scaleY(scope2Target)} L ${chartWidth - padding} ${scaleY(0)} L ${padding} ${scaleY(0)} Z" fill="url(#scope2Grad)"/>
            <line x1="${padding}" y1="${scaleY(scope2)}" x2="${chartWidth - padding}" y2="${scaleY(scope2Target)}" stroke="#22c55e" stroke-width="3"/>
            
            <!-- Scope 3 Area -->
            <path d="M ${padding} ${scaleY(scope3)} L ${chartWidth - padding} ${scaleY(scope3Target)} L ${chartWidth - padding} ${scaleY(0)} L ${padding} ${scaleY(0)} Z" fill="url(#scope3Grad)"/>
            <line x1="${padding}" y1="${scaleY(scope3)}" x2="${chartWidth - padding}" y2="${scaleY(scope3Target)}" stroke="#f59e0b" stroke-width="3"/>
            
            <!-- Start points -->
            <circle cx="${padding}" cy="${scaleY(scope1)}" r="5" fill="#3b82f6"/>
            <circle cx="${padding}" cy="${scaleY(scope2)}" r="5" fill="#22c55e"/>
            <circle cx="${padding}" cy="${scaleY(scope3)}" r="5" fill="#f59e0b"/>
            
            <!-- End points -->
            <circle cx="${chartWidth - padding}" cy="${scaleY(scope1Target)}" r="5" fill="#3b82f6"/>
            <circle cx="${chartWidth - padding}" cy="${scaleY(scope2Target)}" r="5" fill="#22c55e"/>
            <circle cx="${chartWidth - padding}" cy="${scaleY(scope3Target)}" r="5" fill="#f59e0b"/>
            
            <!-- Value labels at start -->
            <text x="${padding + 10}" y="${scaleY(scope1) - 8}" fill="#3b82f6" font-size="11" font-weight="bold">${scope1}</text>
            <text x="${padding + 10}" y="${scaleY(scope2) - 8}" fill="#22c55e" font-size="11" font-weight="bold">${scope2}</text>
            <text x="${padding + 10}" y="${scaleY(scope3) - 8}" fill="#f59e0b" font-size="11" font-weight="bold">${scope3}</text>
            
            <!-- Value labels at end -->
            <text x="${chartWidth - padding - 10}" y="${scaleY(scope1Target) - 8}" fill="#3b82f6" font-size="11" font-weight="bold" text-anchor="end">${scope1Target}</text>
            <text x="${chartWidth - padding - 10}" y="${scaleY(scope2Target) - 8}" fill="#22c55e" font-size="11" font-weight="bold" text-anchor="end">${scope2Target}</text>
            <text x="${chartWidth - padding - 10}" y="${scaleY(scope3Target) - 8}" fill="#f59e0b" font-size="11" font-weight="bold" text-anchor="end">${scope3Target}</text>
            
            <!-- Target reduction label -->
            <text x="${chartWidth / 2}" y="20" fill="#6b7280" font-size="12" text-anchor="middle">Target: ${targetReduction}% reduction by ${baselineYear}</text>
        </svg>
    `;
}


// ============ AI INSIGHT TAB ============
function renderAITab() {
    const docAnalysis = analysisData.document_analysis || null;
    // More robust check for analysis data
    const hasAnalysis = docAnalysis && (
        docAnalysis.summary || 
        docAnalysis.essential_points?.length > 0 || 
        Object.keys(docAnalysis.extraction_answers || {}).length > 0 ||
        docAnalysis.confidence > 0
    );
    
    // Check user role - only lenders can take actions
    const user = JSON.parse(localStorage.getItem('glc_user'));
    const isLender = user?.role === 'lender';
    const disabledClass = !isLender ? 'opacity-50 cursor-not-allowed' : '';
    const disabledAttr = !isLender ? 'disabled' : '';
    
    // Debug log
    console.log('AI Tab - hasAnalysis:', hasAnalysis, 'isLender:', isLender, 'docAnalysis:', docAnalysis);
    
    return `
        <div class="space-y-4">
            ${!isLender ? `
            <div class="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center gap-2">
                <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                <span class="text-sm text-amber-800">View-only mode. Only lenders can perform AI analysis and chat.</span>
            </div>
            ` : ''}
            
            <!-- AI Action Bar -->
            <div id="ai_action" class="bg-gradient-to-r from-indigo-600 to-blue-600 p-4 rounded-xl flex flex-wrap items-center justify-between gap-3">
                <div class="flex items-center gap-3 text-white">
                    <div class="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                        <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/></svg>
                    </div>
                    <div>
                        <p class="font-semibold">AI Agent, with embedded memory context</p>
                        <p class="text-sm text-white/80">${hasAnalysis ? 'Analysis complete - Ready to chat' : 'Click to analyze sustainability reports ➔'}</p>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    ${isLender ? `
                    <button id="save-ai-btn" onclick="window.saveAIRetrievalPDF()" class="px-5 py-2.5 bg-emerald-500 text-white font-semibold rounded-lg hover:bg-emerald-600 transition-colors flex items-center gap-2 shadow-md ${!hasAnalysis ? 'opacity-50 cursor-not-allowed' : ''}" ${!hasAnalysis ? 'disabled title="Run AI Agent first"' : ''}>
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                        Save AI Report
                    </button>
                    ` : ''}
                    <button id="ai-agent-btn" onclick="window.initiateAIAgent()" class="px-5 py-2.5 bg-white text-indigo-700 font-semibold rounded-lg hover:bg-indigo-50 transition-colors flex items-center gap-2 ${disabledClass}" ${disabledAttr}>
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg>
                        ${hasAnalysis ? 'Re-analyze' : 'Initiate AI Agent'}
                    </button>
                </div>
            </div>

            <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
                <!-- Data Performance Section - Full Width -->
                <div class="lg:col-span-2 rounded-xl border border-purple-200 overflow-hidden flex flex-col">
                    <div class="bg-gradient-to-r from-indigo-600 to-blue-600 px-5 py-3 flex-shrink-0">
                        <h3 class="font-bold text-white flex items-center gap-2">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                            AI Analysis Results
                        </h3>
                    </div>
                    <div id="data-performance-content" class="p-5 bg-gradient-to-br from-purple-50 to-indigo-100 flex-1 overflow-y-auto">
                        ${hasAnalysis ? renderDataPerformance(docAnalysis) : renderEmptyDataPerformance()}
                    </div>
                </div>

                <!-- Document Chat Section -->
                <div class="lg:col-span-1 bg-indigo-950/40 rounded-xl border border-purple-200 overflow-hidden text-white flex flex-col" style="min-height: 500px; max-height: 600px;">
                    <div class="bg-gradient-to-r from-indigo-600 to-blue-600 px-5 py-3 flex-shrink-0">
                        <h3 class="font-bold text-white flex items-center gap-2">
                            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
                            Chat with Documents
                        </h3>
                    </div>
                    <div id="doc-chat-messages" class="flex-1 overflow-y-auto p-3 space-y-3">
                        <div class="text-center text-sm text-white/70 py-4">
                            ${!isLender ? '🔒 Chat is available for lenders only' : hasAnalysis ? 'Agent is ready! Ask questions about the documents' : '⚠ Run AI Agent first to enable chat'}
                        </div>
                    </div>
                    <div class="p-3 flex-shrink-0 border-t border-purple-300/30">
                        <div class="flex gap-2">
                            <input type="text" id="doc-chat-input" placeholder="${!isLender ? 'Chat disabled for borrowers' : 'Ask about KPIs, emissions, targets...'}" 
                                class="flex-1 text-white px-4 py-2 border rounded-full bg-indigo-950/10 border-slate-300 placeholder-white/60 text-sm ${disabledClass}"
                                onkeypress="if(event.key==='Enter') window.sendDocChat()" ${!hasAnalysis || !isLender ? 'disabled' : ''}>
                            <button onclick="window.sendDocChat()" class="px-4 py-2 border border-slate-300 bg-indigo-950/10 text-white rounded-full hover:bg-white/10 transition-colors ${disabledClass}" ${!hasAnalysis || !isLender ? 'disabled' : ''}>
                                Send
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderEmptyDataPerformance() {
    return `
        <div class="flex flex-col items-center justify-center h-full py-8">
            <p class="text-gray-700 font-medium mb-2">AI Agent Not Initiated</p>
            <p class="text-sm text-gray-500 text-center max-w-md">Click "Initiate AI Agent" to analyze uploaded sustainability reports and annual reports using RAG-based extraction.</p>
        </div>
    `;
}

function renderDataPerformance(data) {
    const quantitative = data.quantitative_data || [];
    const qualitative = data.qualitative_data || [];
    const essentialPoints = data.essential_points || [];
    const extractions = data.extraction_answers || {};
    
    return `
        <div class="space-y-6">
            <!-- Executive Summary - Full Width -->
            ${data.summary ? `
            <div class="bg-white rounded-xl p-5 border border-indigo-200 shadow-sm">
                <h4 class="font-bold text-indigo-800 mb-3 text-base flex items-center gap-2">
                    <span class="text-lg">📄</span> Executive Summary
                </h4>
                <p class="text-[14px] text-gray-700 leading-relaxed">${data.summary}</p>
                <div class="mt-3 flex items-center gap-4 text-xs text-gray-500">
                    <span>📊 Confidence: ${Math.round((data.confidence || 0) * 100)}%</span>
                    <span>📑 Pages Analyzed: ${data.pages_analyzed || 0}</span>
                </div>
            </div>` : ''}

            <!-- Essential Points - Full Width -->
            ${essentialPoints.length ? `
            <div>
                <h4 class="font-bold text-gray-800 mb-4 flex items-center gap-2 text-base">
                    <span class="text-lg">💡</span> Key Findings
                </h4>
                <div class="grid grid-cols-1 gap-4">
                    ${essentialPoints.map(p => `
                        <div class="p-4 rounded-xl border shadow-sm ${p.importance === 'critical' ? 'bg-red-50 border-red-200' : p.importance === 'high' ? 'bg-amber-50 border-amber-200' : 'bg-white border-gray-200'}">
                            <div class="flex items-center gap-3 mb-2">
                                <span class="px-3 py-1 rounded-full text-xs font-bold ${p.importance === 'critical' ? 'bg-red-100 text-red-700' : p.importance === 'high' ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-600'}">${p.importance.toUpperCase()}</span>
                                <span class="font-semibold text-[15px] text-gray-800">${p.title}</span>
                                <span class="text-xs text-gray-400 ml-auto">${p.category}</span>
                            </div>
                            <p class="text-[14px] text-gray-600 leading-relaxed">${p.description}</p>
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}

            <!-- Quantitative Metrics - Full Width -->
            ${quantitative.length ? `
            <div>
                <h4 class="font-bold text-gray-800 mb-4 flex items-center gap-2 text-base">
                    <span class="text-lg">📊</span> Extracted Metrics
                </h4>
                <div class="bg-white border rounded-xl overflow-hidden shadow-sm">
                    <table class="w-full text-[14px]">
                        <thead class="bg-blue-50">
                            <tr>
                                <th class="px-4 py-3 text-left text-blue-800 font-semibold">Metric</th>
                                <th class="px-4 py-3 text-right text-blue-800 font-semibold">Value</th>
                                <th class="px-4 py-3 text-center text-blue-800 font-semibold">Category</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${quantitative.map(q => `
                                <tr class="border-t hover:bg-gray-50">
                                    <td class="px-4 py-3 text-gray-700">${q.metric}</td>
                                    <td class="px-4 py-3 text-right font-mono font-semibold text-gray-900">${q.value} ${q.unit}</td>
                                    <td class="px-4 py-3 text-center">
                                        <span class="px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">${q.category}</span>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>` : ''}

            <!-- Qualitative Information - Full Width -->
            ${qualitative.length ? `
            <div>
                <h4 class="font-bold text-gray-800 mb-4 flex items-center gap-2 text-base">
                    <span class="text-lg">📝</span> Qualitative Insights
                </h4>
                <div class="grid grid-cols-1 gap-3">
                    ${qualitative.map(q => `
                        <div class="p-4 bg-white rounded-xl border shadow-sm">
                            <div class="flex items-center justify-between mb-2">
                                <span class="font-semibold text-[14px] text-gray-800">${q.topic}</span>
                                <span class="px-3 py-1 rounded-full text-xs bg-emerald-100 text-emerald-700">${q.lma_component}</span>
                            </div>
                            <p class="text-[14px] text-gray-600 leading-relaxed">${q.description}</p>
                            <p class="text-xs text-gray-400 mt-2">Source: ${q.source}</p>
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}

            <!-- LMA Framework Questions - Full Width -->
            ${Object.keys(extractions).length ? `
            <div>
                <h4 class="font-bold text-gray-800 mb-4 flex items-center gap-2 text-base">
                    <span class="text-lg">📋</span> LMA Framework Analysis
                </h4>
                <div class="grid grid-cols-1 gap-4">
                    ${Object.entries(extractions).map(([q, a]) => `
                        <div class="p-5 bg-white rounded-xl border shadow-sm">
                            <p class="font-semibold text-[15px] text-indigo-700 mb-3 flex items-start gap-2">
                                <span class="text-indigo-500">❓</span> ${q}
                            </p>
                            <p class="text-[14px] text-gray-700 leading-relaxed pl-6 ${(a.includes('Not found') || a.includes('not clearly stated')) ? 'italic text-gray-400' : ''}">${a}</p>
                        </div>
                    `).join('')}
                </div>
            </div>` : ''}
        </div>
    `;
}


// ============ CUSTOM Decision TAB ============
function renderDecisionTab() {
    const h = analysisData.header;
    const esg = analysisData.esg_analysis;
    const currentStatus = h.status || 'pending';
    
    // Check user role - only lenders can take actions
    const user = JSON.parse(localStorage.getItem('glc_user'));
    const isLender = user?.role === 'lender';
    const disabledClass = !isLender ? 'opacity-50 cursor-not-allowed' : '';
    const disabledAttr = !isLender ? 'disabled' : '';
    
    // LMA GLP Compliance Summary
    const glpCompliance = {
        useOfProceeds: esg.use_of_proceeds_valid,
        projectEvaluation: esg.glp_eligibility,
        managementOfProceeds: true, // Assumed tracked
        reporting: !!analysisData.statistics?.reporting_frequency,
        dnsh: esg.dnsh_summary?.overall_pass,
        externalReview: false // Would need SPO
    };
    const glpScore = Object.values(glpCompliance).filter(Boolean).length;
    
    return `
        <div class="space-y-6">
            ${!isLender ? `
            <div class="bg-amber-50 border border-amber-200 rounded-lg p-3 flex items-center gap-2">
                <svg class="w-5 h-5 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                <span class="text-sm text-amber-800">View-only mode. Only lenders can change status, save notes, and take actions.</span>
            </div>
            ` : ''}
            
            <!-- Status Change Card -->
            <div class="bg-gradient-to-r from-indigo-600 to-blue-600 rounded-xl p-6 text-white">
                <h3 class="font-bold text-lg mb-4 flex items-center gap-2">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                    Loan Application Decision
                </h3>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                        <p class="text-sm text-gray-300 mb-2">Current Status</p>
                        <span class="px-4 py-2 rounded-lg text-sm font-bold inline-block ${getStatusBgClass(currentStatus)}">${currentStatus.replace('_', ' ').toUpperCase()}</span>
                    </div>
                    <div>
                        <p class="text-sm text-gray-300 mb-2">Change Status To</p>
                        <div class="flex gap-3">
                            <select id="new-status-select" class="flex-1 px-4 py-2 rounded-lg text-gray-800 font-medium border-0 focus:ring-2 focus:ring-green-500 ${disabledClass}" ${disabledAttr}>
                                <option value="pending" ${currentStatus === 'pending' ? 'selected' : ''}>Pending</option>
                                <option value="under_review" ${currentStatus === 'under_review' ? 'selected' : ''}>Under Review</option>
                                <option value="approved" ${currentStatus === 'approved' ? 'selected' : ''}>Approved</option>
                                <option value="rejected" ${currentStatus === 'rejected' ? 'selected' : ''}>Rejected</option>
                            </select>
                            <button onclick="window.confirmStatusChange()" class="px-6 py-2 bg-[var(--green)] hover:bg-green-600 text-white rounded-lg font-medium transition-colors ${disabledClass}" ${disabledAttr}>
                                Confirm
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- LMA GLP Compliance Checklist -->
            <div class="bg-white rounded-xl border overflow-hidden">
                <div class="bg-gradient-to-r from-[#059669] to-[#4c7d3a] px-5 py-3 border-b flex justify-between items-center">
                    <h3 class="font-bold text-emerald-800">LMA Green Loan Principles Compliance</h3>
                    <span class="px-3 py-1 rounded-full text-sm font-bold ${glpScore >= 5 ? 'bg-green-100 text-green-700' : glpScore >= 3 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}">
                        ${glpScore}/6 Components
                    </span>
                </div>
                <div class="p-5">
                    <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                        ${renderGLPCheckItem('Use of Proceeds', glpCompliance.useOfProceeds, 'Proceeds applied to eligible green projects')}
                        ${renderGLPCheckItem('Project Evaluation', glpCompliance.projectEvaluation, 'Clear environmental objectives communicated')}
                        ${renderGLPCheckItem('Management of Proceeds', glpCompliance.managementOfProceeds, 'Proceeds tracked in dedicated account')}
                        ${renderGLPCheckItem('Reporting', glpCompliance.reporting, 'Annual reporting commitment in place')}
                        ${renderGLPCheckItem('DNSH Assessment', glpCompliance.dnsh, 'Do No Significant Harm criteria passed')}
                        ${renderGLPCheckItem('External Review', glpCompliance.externalReview, 'Second Party Opinion obtained')}
                    </div>
                </div>
            </div>

            <!-- Decision Recommendation -->

            <!-- Reviewer Notes -->
            <div class="bg-white rounded-xl p-6 border">
                <h3 class="font-bold text-gray-800 mb-4">Reviewer Notes</h3>
                <textarea id="lender-decision" class="w-full h-32 p-4 border rounded-lg text-sm resize-none focus:ring-2 focus:ring-green-500 focus:border-green-500 ${disabledClass}" placeholder="${!isLender ? 'Only lenders can add notes' : 'Add your notes and decision rationale here...'}" ${disabledAttr}></textarea>
                <div class="mt-3 flex justify-between items-center">
                    <p class="text-xs text-gray-500">${!isLender ? 'View-only mode for borrowers' : 'Notes will be saved to the audit trail'}</p>
                    <button onclick="window.saveDecision()" class="px-4 py-2 bg-[var(--green)] text-white rounded-lg font-medium hover:bg-gray-800 ${disabledClass}" ${disabledAttr}>Save Notes</button>
                    
                </div>
            </div>
        </div>
    `;
}

function renderGLPCheckItem(label, passed, description) {
    return `
        <div class="p-3 rounded-lg border ${passed ? 'bg-green-50 border-green-200' : 'bg-gray-50 border-gray-200'}">
            <div class="flex items-center gap-2 mb-1">
                <span class="${passed ? 'text-green-600' : 'text-gray-400'}">${passed ? '✓' : '○'}</span>
                <span class="font-medium text-sm ${passed ? 'text-green-800' : 'text-gray-600'}">${label}</span>
            </div>
            <p class="text-xs text-gray-500">${description}</p>
        </div>
    `;
}

function getStatusBgClass(status) {
    const classes = {
        'pending': 'bg-yellow-500 text-yellow-900',
        'under_review': 'bg-blue-500 text-white',
        'approved': 'bg-green-500 text-white',
        'rejected': 'bg-red-500 text-white'
    };
    return classes[status] || 'bg-gray-500 text-white';
}

// ============ GLOBAL FUNCTIONS ============
window.switchAuditTab = function(tab) {
    currentTab = tab;
    const content = document.getElementById('tab-content');
    if (content) content.innerHTML = renderTabContent(tab);
    
    // Update tab button styles
    document.querySelectorAll('#tab-buttons button').forEach(btn => {
        btn.classList.remove('text-green-700', 'border-b-2', 'border-green-600', 'bg-green-50');
        btn.classList.add('text-gray-500');
    });
    const activeBtn = document.querySelector(`#tab-buttons button:nth-child(${['general','esg','ai','decision'].indexOf(tab) + 1})`);
    if (activeBtn) {
        activeBtn.classList.remove('text-gray-500');
        activeBtn.classList.add('text-green-700', 'border-b-2', 'border-green-600', 'bg-green-50');
    }
};

window.updateLoanStatus = async function(loanId, status) {
    try {
        await apiCall(`/analysis/loan/${loanId}/status?status=${status}`, { method: 'POST' });
        return true;
    } catch (e) {
        console.error('Error updating status:', e);
        throw e;
    }
};

window.confirmStatusChange = async function() {
    // Check user role - only lenders can change status
    const user = JSON.parse(localStorage.getItem('glc_user'));
    if (user?.role !== 'lender') {
        alert('Only lenders can change loan status.');
        return;
    }
    
    const selectEl = document.getElementById('new-status-select');
    if (!selectEl) return;
    
    const newStatus = selectEl.value;
    const appId = window.currentAuditAppId;
    const currentStatus = analysisData.header?.status;
    
    if (newStatus === currentStatus) {
        alert('Status is already set to ' + newStatus.replace('_', ' '));
        return;
    }
    
    const confirmMsg = `Are you sure you want to change the status from "${currentStatus?.replace('_', ' ').toUpperCase()}" to "${newStatus.replace('_', ' ').toUpperCase()}"?`;
    if (!confirm(confirmMsg)) return;
    
    try {
        // Show loading state
        selectEl.disabled = true;
        
        await window.updateLoanStatus(appId, newStatus);
        
        // Update local data
        analysisData.header.status = newStatus;
        
        // Re-render the decision tab to show updated status
        const content = document.getElementById('tab-content');
        if (content && currentTab === 'decision') {
            content.innerHTML = renderTabContent('decision');
        }
        
        // Update header status badge
        const headerStatusBadge = document.querySelector('.info-header .px-3.py-1.rounded-full');
        if (headerStatusBadge) {
            headerStatusBadge.className = `px-3 py-1 rounded-full text-xs font-bold uppercase ${getStatusClass(newStatus)}`;
            headerStatusBadge.textContent = newStatus.replace('_', ' ');
        }
        
        // Show success message
        showStatusToast('Status updated successfully!', 'success');
        
    } catch (e) {
        alert('Error updating status: ' + e.message);
        selectEl.disabled = false;
    }
};

function showStatusToast(message, type) {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 px-6 py-3 rounded-lg text-white font-medium shadow-lg z-50 animate-in slide-in-from-bottom duration-300 ${type === 'success' ? 'bg-green-600' : 'bg-red-600'}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.classList.add('opacity-0', 'transition-opacity');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

window.saveDecision = async function() {
    // Check user role - only lenders can save notes
    const user = JSON.parse(localStorage.getItem('glc_user'));
    if (user?.role !== 'lender') {
        alert('Only lenders can save reviewer notes.');
        return;
    }
    
    const decision = document.getElementById('lender-decision')?.value;
    if (!decision?.trim()) {
        alert('Please enter your notes before saving.');
        return;
    }
    
    const appId = window.currentAuditAppId;
    if (!appId) return;
    
    try {
        await apiCall(`/analysis/loan/${appId}/notes?notes=${encodeURIComponent(decision)}`, { method: 'POST' });
        showStatusToast('Notes saved successfully!', 'success');
    } catch (e) {
        console.error('Error saving notes:', e);
        showStatusToast('Failed to save notes', 'error');
    }
};

// Load reviewer notes when Decision tab is shown
async function loadReviewerNotes() {
    const appId = window.currentAuditAppId;
    if (!appId) return;
    
    try {
        const data = await apiCall(`/analysis/loan/${appId}/notes`);
        const textarea = document.getElementById('lender-decision');
        if (textarea && data.notes) {
            textarea.value = data.notes;
        }
    } catch (e) {
        console.error('Error loading notes:', e);
    }
}

window.scheduleReview = function() {
    // Check user role - only lenders can schedule reviews
    const user = JSON.parse(localStorage.getItem('glc_user'));
    if (user?.role !== 'lender') {
        alert('Only lenders can schedule reviews.');
        return;
    }
    alert('Review scheduling feature coming soon.'); 
};

window.requestDocuments = function() {
    // Check user role - only lenders can request documents
    const user = JSON.parse(localStorage.getItem('glc_user'));
    if (user?.role !== 'lender') {
        alert('Only lenders can request documents.');
        return;
    }
    alert('Document request feature coming soon.');
};

window.generateReport = function() {
    // Check user role - only lenders can generate reports
    const user = JSON.parse(localStorage.getItem('glc_user'));
    if (user?.role !== 'lender') {
        alert('Only lenders can generate reports.');
        return;
    }
    alert('Report generation feature coming soon.');
};

// ============ MAP AND CLIMATE FUNCTIONS ============
let mapInstance = null;

async function loadMapAndClimate() {
    const proj = analysisData.general_info?.project || {};
    const pincode = proj.project_pin_code;
    
    if (!pincode) {
        showMapError('No pincode available for this project');
        showEnvDataError('Location data required');
        return;
    }
    
    try {
        // Fetch location data from backend
        const response = await apiCall(`/location/full/${pincode}?country=India`);
        
        if (response.location) {
            initializeMap(response.location);
            
            // Fetch environmental data using coordinates
            const lat = response.location.lat;
            const lon = response.location.lon;
            
            try {
                const envData = await apiCall(`/environment/data?lat=${lat}&lon=${lon}`);
                renderClimateTable(envData.climate);
                renderAirQualityTable(envData.air_quality);
            } catch (envError) {
                console.error('Error loading environmental data:', envError);
                showEnvDataError('Environmental data unavailable');
            }
        }
    } catch (error) {
        console.error('Error loading location data:', error);
        showMapError('Could not load map');
        showEnvDataError('Location data unavailable');
    }
}

function showEnvDataError(message) {
    const climateTable = document.getElementById('climate-table');
    const airTable = document.getElementById('air-quality-table');
    
    const errorHtml = `<div class="flex items-center justify-center py-4 text-gray-500 text-sm">${message}</div>`;
    
    if (climateTable) climateTable.innerHTML = errorHtml;
    if (airTable) airTable.innerHTML = errorHtml;
}

function renderClimateTable(climate) {
    const container = document.getElementById('climate-table');
    if (!container || !climate) return;
    
    container.innerHTML = `
        <table class="w-full text-[14px]">
            <tbody>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Temperature</td><td class="py-1.5 text-right font-medium">${climate.temperature ?? '-'}°C</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Feels Like</td><td class="py-1.5 text-right font-medium">${climate.feels_like ?? '-'}°C</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Temp Max</td><td class="py-1.5 text-right font-medium">${climate.temp_max ?? '-'}°C</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Temp Min</td><td class="py-1.5 text-right font-medium">${climate.temp_min ?? '-'}°C</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Humidity</td><td class="py-1.5 text-right font-medium">${climate.humidity ?? '-'}%</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Pressure</td><td class="py-1.5 text-right font-medium">${climate.pressure ?? '-'} hPa</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Wind Speed</td><td class="py-1.5 text-right font-medium">${climate.wind_speed ?? '-'} km/h</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Wind Direction</td><td class="py-1.5 text-right font-medium">${climate.wind_direction ?? '-'}°</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Wind Max</td><td class="py-1.5 text-right font-medium">${climate.wind_max ?? '-'} km/h</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Cloud Cover</td><td class="py-1.5 text-right font-medium">${climate.cloud_cover ?? '-'}%</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Precipitation</td><td class="py-1.5 text-right font-medium">${climate.precipitation_daily ?? '-'} mm</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">UV Index</td><td class="py-1.5 text-right font-medium">${climate.uv_index ?? '-'}</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Elevation</td><td class="py-1.5 text-right font-medium">${climate.elevation ?? '-'} m</td></tr>
                <tr><td class="py-1.5 text-gray-500">Condition</td><td class="py-1.5 text-right font-medium">${climate.weather_description ?? '-'}</td></tr>
            </tbody>
        </table>
    `;
}

function renderAirQualityTable(airQuality) {
    const container = document.getElementById('air-quality-table');
    if (!container || !airQuality) return;
    
    const aqiColors = {
        'green': 'bg-green-100 text-green-700',
        'yellow': 'bg-yellow-100 text-yellow-700',
        'orange': 'bg-orange-100 text-orange-700',
        'red': 'bg-red-100 text-red-700',
        'purple': 'bg-purple-100 text-purple-700',
        'maroon': 'bg-red-200 text-red-800'
    };
    
    const aqiClass = aqiColors[airQuality.aqi_color] || 'bg-gray-100 text-gray-700';
    
    container.innerHTML = `
        <div class="mb-2 text-center">
            <span class="px-3 py-1 rounded-full text-xs font-bold ${aqiClass}">${airQuality.aqi_category || 'Unknown'}</span>
        </div>
        <table class="w-full text-[14px]">
            <tbody>
                <tr class="border-b"><td class="py-1.5 text-gray-500">PM2.5</td><td class="py-1.5 text-right font-medium">${airQuality.pm2_5 ?? '-'} µg/m³</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">PM10</td><td class="py-1.5 text-right font-medium">${airQuality.pm10 ?? '-'} µg/m³</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Ozone (O₃)</td><td class="py-1.5 text-right font-medium">${airQuality.ozone ?? '-'} µg/m³</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">NO₂</td><td class="py-1.5 text-right font-medium">${airQuality.nitrogen_dioxide ?? '-'} µg/m³</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">SO₂</td><td class="py-1.5 text-right font-medium">${airQuality.sulphur_dioxide ?? '-'} µg/m³</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">CO</td><td class="py-1.5 text-right font-medium">${airQuality.carbon_monoxide ?? '-'} µg/m³</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Ammonia</td><td class="py-1.5 text-right font-medium">${airQuality.ammonia ?? '-'} µg/m³</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Dust</td><td class="py-1.5 text-right font-medium">${airQuality.dust ?? '-'} µg/m³</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">Aerosol Depth</td><td class="py-1.5 text-right font-medium">${airQuality.aerosol_optical_depth ?? '-'}</td></tr>
                <tr class="border-b"><td class="py-1.5 text-gray-500">UV Index</td><td class="py-1.5 text-right font-medium">${airQuality.uv_index ?? '-'}</td></tr>
                <tr><td class="py-1.5 text-gray-500">UV Clear Sky</td><td class="py-1.5 text-right font-medium">${airQuality.uv_index_clear_sky ?? '-'}</td></tr>
            </tbody>
        </table>
    `;
}

function initializeMap(location) {
    const mapContainer = document.getElementById('project-map');
    const loadingEl = document.getElementById('map-loading');
    
    if (!mapContainer) return;
    
    // Load Leaflet CSS if not already loaded
    if (!document.querySelector('link[href*="leaflet"]')) {
        const link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
        document.head.appendChild(link);
    }
    
    // Load Leaflet JS if not already loaded
    if (!window.L) {
        const script = document.createElement('script');
        script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
        script.onload = () => createMap(location, mapContainer, loadingEl);
        document.head.appendChild(script);
    } else {
        createMap(location, mapContainer, loadingEl);
    }
}

function createMap(location, mapContainer, loadingEl) {
    // Hide loading
    if (loadingEl) loadingEl.style.display = 'none';
    
    // Destroy existing map if any
    if (mapInstance) {
        mapInstance.remove();
        mapInstance = null;
    }
    
    const lat = location.lat || 20.5937;
    const lon = location.lon || 78.9629;
    const locationName = location.display_name || location.name || 'Project Location';
    
    // Create map
    mapInstance = L.map(mapContainer).setView([lat, lon], 12);
    
    // Add Stadia Alidade Satellite tiles
    L.tileLayer('https://tiles.stadiamaps.com/tiles/alidade_satellite/{z}/{x}/{y}{r}.jpg', {
        attribution: '© CNES | Stadia Maps',
        maxZoom: 80,
        minZoom: 0
    }).addTo(mapInstance);
    
    // Add circle border around project location (no fill, just border)
    L.circle([lat, lon], {
        color: '#dd1c0eff',      // Orange border
        weight: 3,             // Border thickness
        opacity: 1,            // Full opacity for border
        fillColor: '#f97316',
        fillOpacity: 0,        // No fill - transparent inside
        radius: 6000            
    }).addTo(mapInstance).bindPopup(`<strong>${locationName}</strong>`);
       
}

function showMapError(message) {
    const loadingEl = document.getElementById('map-loading');
    if (loadingEl) {
        loadingEl.innerHTML = `
            <div class="text-center">
                <span class="text-3xl">🗺️</span>
                <p class="text-sm text-gray-500 mt-2">${message}</p>
            </div>
        `;
    }
}

// Override switchAuditTab to load map when ESG tab is selected
const originalSwitchTab = window.switchAuditTab;
window.switchAuditTab = function(tab) {
    originalSwitchTab(tab);
    
    // Load map and climate when ESG tab is shown
    if (tab === 'esg') {
        setTimeout(() => loadMapAndClimate(), 100);
    }
    
    // Load reviewer notes when Decision tab is shown
    if (tab === 'decision') {
        setTimeout(() => loadReviewerNotes(), 100);
    }
};

// Also load on initial render if ESG tab is active
if (currentTab === 'esg') {
    setTimeout(() => loadMapAndClimate(), 500);
}


// ============ DOCUMENT ANALYSIS FUNCTIONS ============
window.initiateAIAgent = async function() {
    // Check user role - only lenders can initiate AI analysis
    const user = JSON.parse(localStorage.getItem('glc_user'));
    if (user?.role !== 'lender') {
        alert('Only lenders can initiate AI analysis.');
        return;
    }
    
    const appId = window.currentAuditAppId;
    if (!appId) return;
    
    const btn = document.getElementById('ai-agent-btn');
    const container = document.getElementById('data-performance-content');
    const chatMessages = document.getElementById('doc-chat-messages');
    
    if (!container) return;
    
    // Update button state
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path></svg> Processing...`;
    }
    
    // Show loading with progress info
    let dots = 0;
    const loadingInterval = setInterval(() => {
        dots = (dots + 1) % 4;
        const dotsStr = '.'.repeat(dots);
        const statusEl = document.getElementById('ai-status-text');
        if (statusEl) statusEl.textContent = `Processing documents${dotsStr}`;
    }, 500);
    
    container.innerHTML = `
        <div class="flex flex-col items-center justify-center h-full py-8">
            <div class="animate-spin rounded-full h-12 w-12 border-4 border-indigo-200 border-t-indigo-600 mb-4"></div>
            <p id="ai-status-text" class="text-gray-700 font-medium">Processing documents...</p>
            <p class="text-sm text-gray-500 mt-1">It may take few minutes to show result</p>
            <p class="text-xs text-gray-400 mt-3">Indexing documents → Loading models → Extracting answers</p>
        </div>
    `;
    
    try {
        const data = await apiCall(`/documents/analyze/${appId}`);
        clearInterval(loadingInterval);
        
        // Store in analysisData
        analysisData.document_analysis = data;
        
        // Render results
        container.innerHTML = renderDataPerformance(data);
        
        // Enable chat
        if (chatMessages) {
            chatMessages.innerHTML = `<div class="text-center text-sm text-white/70 py-2">✓ Ready to chat about documents</div>`;
        }
        const chatInput = document.getElementById('doc-chat-input');
        if (chatInput) chatInput.disabled = false;
        
        // Update button
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/></svg> Re-analyze`;
        }
        
        // Enable Save AI Report button
        const saveBtn = document.getElementById('save-ai-btn');
        if (saveBtn) {
            saveBtn.disabled = false;
            saveBtn.classList.remove('opacity-50', 'cursor-not-allowed');
            saveBtn.removeAttribute('title');
        }
        
    } catch (error) {
        clearInterval(loadingInterval);
        console.error('AI Agent error:', error);
        
        const errorMsg = error.message || 'Unknown error';
        const isTimeout = errorMsg.includes('timed out');
        
        container.innerHTML = `
            <div class="flex flex-col items-center justify-center h-full py-8">
                <div class="text-5xl mb-4">${isTimeout ? '⏳' : '⚠️'}</div>
                <p class="text-gray-700 font-medium mb-2">${isTimeout ? 'Still Processing...' : 'Analysis Failed'}</p>
                <p class="text-sm text-gray-500 text-center max-w-md">${isTimeout ? 'AI models are loading. Please wait and try again in a moment.' : errorMsg}</p>
                <button onclick="window.initiateAIAgent()" class="mt-4 px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 text-sm">
                    ${isTimeout ? 'Check Again' : 'Retry'}
                </button>
            </div>
        `;
        
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"/></svg> Retry`;
        }
    }
};

// Keep for backward compatibility
window.loadDocumentAnalysis = window.initiateAIAgent;

window.sendDocChat = async function() {
    // Check user role - only lenders can use chat
    const user = JSON.parse(localStorage.getItem('glc_user'));
    if (user?.role !== 'lender') {
        alert('Only lenders can use the document chat.');
        return;
    }
    
    const input = document.getElementById('doc-chat-input');
    const messagesContainer = document.getElementById('doc-chat-messages');
    const appId = window.currentAuditAppId;
    
    if (!input || !messagesContainer || !appId) return;
    
    const message = input.value.trim();
    if (!message) return;
    
    input.value = '';
    
    // Add user message
    messagesContainer.innerHTML += `
        <div class="flex justify-end">
            <div class="bg-emerald-600 text-white px-3 py-2 rounded-lg rounded-br-none max-w-[85%] text-sm">${escapeHtml(message)}</div>
        </div>
    `;
    
    // Add loading
    const loadingId = 'chat-' + Date.now();
    messagesContainer.innerHTML += `
        <div id="${loadingId}" class="flex justify-start">
            <div class="bg-white/20 px-3 py-2 rounded-lg rounded-bl-none text-sm">
                <span class="animate-pulse">Thinking...</span>
            </div>
        </div>
    `;
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    
    try {
        const response = await apiCall('/documents/chat', {
            method: 'POST',
            body: JSON.stringify({ message, loan_id: appId })
        });
        
        document.getElementById(loadingId)?.remove();
        
        const confClass = response.confidence >= 0.5 ? 'text-green-400' : 'text-yellow-400';
        messagesContainer.innerHTML += `
            <div class="flex justify-start">
                <div class="bg-white/10 px-3 py-2 rounded-lg rounded-bl-none max-w-[85%]">
                    <p class="text-sm">${escapeHtml(response.response)}</p>
                    <p class="text-xs ${confClass} mt-1">${Math.round(response.confidence * 100)}% confidence</p>
                </div>
            </div>
        `;
    } catch (error) {
        document.getElementById(loadingId)?.remove();
        messagesContainer.innerHTML += `
            <div class="flex justify-start">
                <div class="bg-red-500/20 text-red-200 px-3 py-2 rounded-lg rounded-bl-none text-sm">Error: ${error.message || 'Failed to get response'}</div>
            </div>
        `;
    }
    
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
};

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============ SAVE AI RETRIEVAL PDF ============
window.saveAIRetrievalPDF = async function() {
    const user = JSON.parse(localStorage.getItem('glc_user'));
    if (user?.role !== 'lender') {
        alert('Only lenders can save AI reports.');
        return;
    }
    
    const appId = window.currentAuditAppId;
    if (!appId) {
        alert('No loan application selected.');
        return;
    }
    
    // Check if analysis has been run
    if (!analysisData?.document_analysis) {
        alert('No AI analysis data available. Please run "Initiate AI Agent" first.');
        return;
    }
    
    const btn = document.getElementById('save-ai-btn');
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = `<svg class="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Generating...`;
    }
    
    try {
        const response = await apiCall(`/documents/save-ai-report/${appId}`, {
            method: 'POST'
        });
        
        if (response.success) {
            alert('AI Retrieval Insights report saved successfully! You can find it in Loan Assets.');
            if (btn) {
                btn.innerHTML = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/></svg> Saved!`;
                setTimeout(() => {
                    btn.disabled = false;
                    btn.innerHTML = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg> Save AI Report`;
                }, 2000);
            }
        } else {
            throw new Error(response.message || 'Failed to save report');
        }
    } catch (error) {
        alert('Failed to save AI report: ' + (error.message || 'Unknown error'));
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg> Save AI Report`;
        }
    }
};

