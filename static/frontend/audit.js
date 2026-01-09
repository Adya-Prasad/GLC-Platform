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
            <div class="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
                <div class="flex flex-wrap justify-between items-start gap-4">
                    <div class="flex-1">
                        <div class="flex items-center gap-3 mb-2">
                            <span class="px-3 py-1 rounded-full text-xs font-bold uppercase ${getStatusClass(h.status)}">${h.status}</span>
                            <span class="text-sm text-gray-500 font-mono">${analysisData.loan_id_str || 'LOAN-' + appId}</span>
                        </div>
                        <h1 class="text-2xl font-bold text-gray-900">${h.project_name}</h1>
                        <p class="text-gray-500 mt-1">${h.org_name}</p>
                        <div class="flex gap-4 mt-3 text-sm text-gray-600">
                            <span><strong>Sector:</strong> ${h.sector || '-'}</span>
                            <span><strong>Shareholders:</strong> ${h.shareholder_entities}</span>
                        </div>
                    </div>
                    <div class="text-right">
                        <p class="text-3xl font-bold text-gray-900">${formatCurrency(h.amount_requested, h.currency)}</p>
                        <p class="text-sm text-gray-500 mt-1">Requested Amount</p>
                        ${isLender ? `
                        <div class="mt-3">
                            <select id="status-select" onchange="window.updateLoanStatus(${appId}, this.value)" class="px-3 py-2 border rounded-lg text-sm font-medium">
                                <option value="pending" ${h.status === 'pending' ? 'selected' : ''}>Pending</option>
                                <option value="under_review" ${h.status === 'under_review' ? 'selected' : ''}>Under Review</option>
                                <option value="approved" ${h.status === 'approved' ? 'selected' : ''}>Approved</option>
                                <option value="rejected" ${h.status === 'rejected' ? 'selected' : ''}>Rejected</option>
                            </select>
                        </div>` : ''}
                    </div>
                </div>
            </div>

            <!-- Tabs -->
            <div class="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                <div class="flex border-b overflow-x-auto" id="tab-buttons">
                    ${renderTabButton('general', 'General Info', 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z')}
                    ${renderTabButton('esg', 'ESG Analysis', 'M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z')}
                    ${renderTabButton('stats', 'Statistics', 'M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z')}
                    ${renderTabButton('ai', 'AI Insight', 'M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z')}
                    ${renderTabButton('decision', 'Decision', 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z')}
                </div>
                <div id="tab-content" class="p-6">${renderTabContent('general')}</div>
            </div>

            <div class="text-center pt-4">
                <button onclick="window.navigateTo('applications')" class="px-6 py-2 bg-gray-100 text-gray-600 font-bold rounded-xl hover:bg-gray-200">Back to Applications</button>
            </div>
        </div>
    `;
}

function renderTabButton(id, label, icon) {
    const isActive = currentTab === id;
    return `<button onclick="window.switchAuditTab('${id}')" class="flex items-center gap-2 px-5 py-4 text-sm font-medium whitespace-nowrap ${isActive ? 'text-green-700 border-b-2 border-green-600 bg-green-50' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'}">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${icon}"/></svg>
        ${label}
    </button>`;
}

function renderTabContent(tab) {
    if (!analysisData) return '<p>Loading...</p>';
    switch (tab) {
        case 'general': return renderGeneralTab();
        case 'esg': return renderESGTab();
        case 'stats': return renderStatsTab();
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
    const kpis = g.green_kpis || {};
    const quest = g.questionnaire || {};

    return `
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div class="bg-gray-50 rounded-xl p-5 border">
                <h3 class="font-bold text-gray-800 mb-4">Organization Details</h3>
                ${renderInfoGrid([['Organization', org.org_name], ['Sector', org.sector], ['Location', org.location], ['Website', org.website], ['Annual Revenue', org.annual_revenue ? formatCurrency(org.annual_revenue, 'USD') : '-'], ['Shareholders', org.shareholder_entities]])}
            </div>
            <div class="bg-gray-50 rounded-xl p-5 border">
                <h3 class="font-bold text-gray-800 mb-4">Project Information</h3>
                ${renderInfoGrid([['Project Name', proj.project_name], ['Project Type', proj.project_type], ['Project Location', proj.project_location], ['Planned Start', proj.planned_start_date], ['Loan Tenor', proj.loan_tenor ? proj.loan_tenor + ' months' : '-'], ['Amount', proj.amount_requested ? formatCurrency(proj.amount_requested, proj.currency) : '-']])}
                <div class="mt-4 pt-3 border-t">
                    <p class="text-xs text-gray-500 mb-1">Use of Proceeds</p>
                    <p class="text-sm text-gray-700 bg-white p-3 rounded-lg">${proj.use_of_proceeds || '-'}</p>
                </div>
            </div>
            <div class="bg-gray-50 rounded-xl p-5 border">
                <h3 class="font-bold text-gray-800 mb-4">Green KPIs & Emissions</h3>
                ${renderInfoGrid([['Scope 1 (tCO2)', kpis.scope1_tco2], ['Scope 2 (tCO2)', kpis.scope2_tco2], ['Scope 3 (tCO2)', kpis.scope3_tco2], ['Baseline Year', kpis.baseline_year], ['Target Reduction', kpis.target_reduction ? kpis.target_reduction + '%' : '-'], ['Reporting Freq', kpis.reporting_frequency]])}
                ${kpis.kpi_metrics?.length ? `<div class="mt-3 flex flex-wrap gap-2">${kpis.kpi_metrics.map(k => `<span class="bg-green-100 text-green-700 px-2 py-1 rounded text-xs font-medium">${k}</span>`).join('')}</div>` : ''}
            </div>
            <div class="bg-gray-50 rounded-xl p-5 border">
                <h3 class="font-bold text-gray-800 mb-4">ESG Questionnaire</h3>
                <div class="space-y-2 text-sm max-h-48 overflow-y-auto">
                    ${Object.entries(quest).map(([k, v]) => `<div class="flex justify-between py-1 border-b border-gray-200"><span class="text-gray-600">${formatQuestionKey(k)}</span><span class="font-medium ${v === 'yes' || v === 'fully_compliant' ? 'text-green-600' : v === 'no' || v === 'non_compliant' ? 'text-red-600' : 'text-gray-800'}">${v || '-'}</span></div>`).join('')}
                </div>
            </div>
        </div>
    `;
}

function renderInfoGrid(items) {
    return `<div class="grid grid-cols-2 gap-3 text-sm">${items.map(([label, value]) => `<div class="flex flex-col"><span class="text-gray-500 text-xs">${label}</span><span class="font-medium text-gray-800">${value || '-'}</span></div>`).join('')}</div>`;
}

function formatQuestionKey(key) {
    return key.replace(/^q_/, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
}


// ============ ESG ANALYSIS TAB ============
function renderESGTab() {
    const esg = analysisData.esg_analysis;
    const dnsh = esg.dnsh_summary || {};
    const risk = esg.sector_risk || {};
    const qScore = esg.questionnaire_score || {};

    return `
        <div class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="bg-gradient-to-br from-green-50 to-emerald-100 rounded-xl p-6 border border-green-200 text-center">
                    <p class="text-sm text-green-700 font-medium mb-2">ESG Score</p>
                    <p class="text-5xl font-bold ${esg.esg_score >= 70 ? 'text-green-600' : esg.esg_score >= 50 ? 'text-yellow-600' : 'text-red-600'}">${esg.esg_score || 'N/A'}</p>
                    <p class="text-xs text-gray-600 mt-2">out of 100</p>
                </div>
                <div class="bg-white rounded-xl p-6 border">
                    <p class="text-sm text-gray-600 font-medium mb-3">GLP Eligibility</p>
                    <div class="flex items-center gap-3 mb-3">
                        <span class="w-10 h-10 rounded-full flex items-center justify-center ${esg.glp_eligibility ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-600'}">${esg.glp_eligibility ? '✓' : '✗'}</span>
                        <div>
                            <p class="font-bold ${esg.glp_eligibility ? 'text-green-700' : 'text-red-700'}">${esg.glp_eligibility ? 'Eligible' : 'Not Eligible'}</p>
                            <p class="text-xs text-gray-500">${esg.glp_category || 'Category pending'}</p>
                        </div>
                    </div>
                    <div class="bg-gray-100 rounded-full h-2 overflow-hidden"><div class="h-full bg-green-500" style="width: ${(esg.glp_confidence || 0) * 100}%"></div></div>
                    <p class="text-xs text-gray-500 mt-1">Confidence: ${Math.round((esg.glp_confidence || 0) * 100)}%</p>
                </div>
                <div class="bg-white rounded-xl p-6 border">
                    <p class="text-sm text-gray-600 font-medium mb-3">Sector Risk Level</p>
                    ${renderRiskMeter(risk.score || 50, risk.label || 'Medium Risk')}
                    <p class="text-xs text-gray-600 mt-3 text-center">${risk.description || ''}</p>
                </div>
            </div>

            <div class="bg-white rounded-xl p-6 border">
                <h3 class="font-bold text-gray-800 mb-4">DNSH Assessment (Do No Significant Harm)</h3>
                <div class="flex items-center gap-4 mb-4">
                    <span class="px-4 py-2 rounded-lg font-bold ${dnsh.overall_pass ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}">${dnsh.overall_pass ? '✓ DNSH Passed' : '✗ DNSH Failed'}</span>
                    <span class="text-sm text-gray-600">Passed: ${dnsh.passed_count || 0} | Failed: ${dnsh.failed_count || 0} | Unclear: ${dnsh.unclear_count || 0}</span>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                    ${Object.entries(dnsh.results || {}).map(([key, val]) => `<div class="p-3 rounded-lg border ${val.status === 'pass' ? 'bg-green-50 border-green-200' : val.status === 'fail' ? 'bg-red-50 border-red-200' : 'bg-yellow-50 border-yellow-200'}"><p class="font-medium text-sm capitalize">${key.replace(/_/g, ' ')}</p><p class="text-xs mt-1 ${val.status === 'pass' ? 'text-green-600' : val.status === 'fail' ? 'text-red-600' : 'text-yellow-600'}">${val.status.toUpperCase()}</p></div>`).join('')}
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-white rounded-xl p-6 border">
                    <h3 class="font-bold text-gray-800 mb-4">Carbon Lock-in Risk</h3>
                    <span class="px-3 py-1 rounded-full text-sm font-bold ${esg.carbon_lockin?.risk_level === 'low' ? 'bg-green-100 text-green-700' : esg.carbon_lockin?.risk_level === 'high' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}">${(esg.carbon_lockin?.risk_level || 'unknown').toUpperCase()}</span>
                    <p class="text-sm text-gray-600 mt-3">${esg.carbon_lockin?.assessment || 'Assessment pending'}</p>
                    <p class="text-xs text-blue-600 mt-2">${esg.carbon_lockin?.recommendation || ''}</p>
                </div>
                <div class="bg-white rounded-xl p-6 border">
                    <h3 class="font-bold text-gray-800 mb-4">Questionnaire Score</h3>
                    <div class="flex items-center gap-4 mb-4">
                        <div class="text-4xl font-bold text-purple-600">${qScore.total || 0}</div>
                        <div class="text-sm text-gray-500">/ ${qScore.max_score || 100}</div>
                    </div>
                    <div class="bg-gray-100 rounded-full h-3 overflow-hidden"><div class="h-full bg-purple-500" style="width: ${((qScore.total || 0) / (qScore.max_score || 100)) * 100}%"></div></div>
                </div>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-green-50 rounded-xl p-5 border border-green-200">
                    <h4 class="font-bold text-green-800 mb-3">✓ Green Indicators</h4>
                    <div class="flex flex-wrap gap-2">${(esg.green_indicators || []).length ? esg.green_indicators.map(g => `<span class="bg-green-200 text-green-800 px-3 py-1 rounded-full text-sm">${g}</span>`).join('') : '<span class="text-gray-500 text-sm">None identified</span>'}</div>
                </div>
                <div class="bg-red-50 rounded-xl p-5 border border-red-200">
                    <h4 class="font-bold text-red-800 mb-3">✗ Red Flags</h4>
                    <div class="flex flex-wrap gap-2">${(esg.red_flags || []).length ? esg.red_flags.map(r => `<span class="bg-red-200 text-red-800 px-3 py-1 rounded-full text-sm">${r}</span>`).join('') : '<span class="text-gray-500 text-sm">None identified</span>'}</div>
                </div>
            </div>
        </div>
    `;
}

function renderRiskMeter(score, label) {
    const angle = -90 + (score / 100) * 180;
    return `<div class="flex flex-col items-center">
        <svg viewBox="0 0 200 120" class="w-full max-w-[200px]">
            <path d="M 20 100 A 80 80 0 0 1 180 100" fill="none" stroke="#e5e7eb" stroke-width="16" stroke-linecap="round"/>
            <path d="M 20 100 A 80 80 0 0 1 60 35" fill="none" stroke="#22c55e" stroke-width="16" stroke-linecap="round"/>
            <path d="M 60 35 A 80 80 0 0 1 140 35" fill="none" stroke="#eab308" stroke-width="16"/>
            <path d="M 140 35 A 80 80 0 0 1 180 100" fill="none" stroke="#ef4444" stroke-width="16" stroke-linecap="round"/>
            <g transform="rotate(${angle}, 100, 100)">
                <line x1="100" y1="100" x2="100" y2="35" stroke="#1f2937" stroke-width="3" stroke-linecap="round"/>
                <circle cx="100" cy="100" r="8" fill="#1f2937"/>
            </g>
            <text x="100" y="95" text-anchor="middle" class="text-2xl font-bold" fill="#1f2937">${score}</text>
        </svg>
        <p class="font-bold mt-2" style="color: ${score <= 33 ? '#22c55e' : score <= 66 ? '#eab308' : '#ef4444'}">${label}</p>
    </div>`;
}


// ============ STATISTICS TAB ============
function renderStatsTab() {
    const stats = analysisData.statistics;
    const emissions = stats.emissions || {};
    const financial = stats.financial || {};
    const benchmarks = stats.benchmarks || {};

    return `
        <div class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <!-- Emissions Pie Chart -->
                <div class="bg-white rounded-xl p-6 border">
                    <h3 class="font-bold text-gray-800 mb-4">Emissions Breakdown (tCO2)</h3>
                    <div class="flex items-center gap-6">
                        ${renderEmissionsPie(emissions)}
                        <div class="space-y-3 text-sm">
                            <div class="flex items-center gap-2"><span class="w-4 h-4 rounded bg-blue-500"></span><span>Scope 1: ${emissions.scope1 || 0} tCO2 (${emissions.percentages?.scope1 || 0}%)</span></div>
                            <div class="flex items-center gap-2"><span class="w-4 h-4 rounded bg-green-500"></span><span>Scope 2: ${emissions.scope2 || 0} tCO2 (${emissions.percentages?.scope2 || 0}%)</span></div>
                            <div class="flex items-center gap-2"><span class="w-4 h-4 rounded bg-yellow-500"></span><span>Scope 3: ${emissions.scope3 || 0} tCO2 (${emissions.percentages?.scope3 || 0}%)</span></div>
                            <div class="pt-2 border-t"><strong>Total:</strong> ${emissions.total || 0} tCO2</div>
                        </div>
                    </div>
                    <div class="mt-4 pt-4 border-t grid grid-cols-2 gap-4 text-sm">
                        <div><span class="text-gray-500">Baseline Year:</span> <strong>${emissions.baseline_year || '-'}</strong></div>
                        <div><span class="text-gray-500">Target Reduction:</span> <strong>${emissions.target_reduction || '-'}%</strong></div>
                        <div><span class="text-gray-500">Intensity:</span> <strong>${emissions.intensity_per_million || 0} tCO2/M</strong></div>
                    </div>
                </div>

                <!-- Financial Summary -->
                <div class="bg-white rounded-xl p-6 border">
                    <h3 class="font-bold text-gray-800 mb-4">Financial Summary</h3>
                    <div class="space-y-4">
                        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span class="text-gray-600">Amount Requested</span>
                            <span class="text-xl font-bold text-gray-900">${formatCurrency(financial.amount_requested, financial.currency)}</span>
                        </div>
                        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span class="text-gray-600">Loan Tenor</span>
                            <span class="font-bold text-gray-900">${financial.loan_tenor || '-'} months</span>
                        </div>
                        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span class="text-gray-600">Annual Revenue</span>
                            <span class="font-bold text-gray-900">${financial.annual_revenue ? formatCurrency(financial.annual_revenue, 'USD') : '-'}</span>
                        </div>
                        <div class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                            <span class="text-gray-600">Reporting Frequency</span>
                            <span class="font-bold text-gray-900">${stats.reporting_frequency || '-'}</span>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Benchmarks Comparison -->
            <div class="bg-white rounded-xl p-6 border">
                <h3 class="font-bold text-gray-800 mb-4">ESG Benchmarks Comparison</h3>
                <div class="space-y-4">
                    ${renderBenchmarkBar('This Application', analysisData.esg_analysis?.esg_score || 0, 'green')}
                    ${renderBenchmarkBar('Sector Average', benchmarks.sector_avg_esg || 65, 'blue')}
                    ${renderBenchmarkBar('Portfolio Average', benchmarks.portfolio_avg_esg || 72, 'purple')}
                    ${renderBenchmarkBar('GLP Threshold', benchmarks.glp_threshold || 60, 'gray')}
                </div>
            </div>

            <!-- KPI Metrics -->
            ${stats.kpi_metrics?.length ? `
            <div class="bg-white rounded-xl p-6 border">
                <h3 class="font-bold text-gray-800 mb-4">Selected KPI Metrics</h3>
                <div class="flex flex-wrap gap-3">
                    ${stats.kpi_metrics.map(k => `<span class="bg-emerald-100 text-emerald-700 px-4 py-2 rounded-lg font-medium">${k}</span>`).join('')}
                </div>
            </div>` : ''}
        </div>
    `;
}

function renderEmissionsPie(emissions) {
    const total = emissions.total || 1;
    const s1 = (emissions.scope1 || 0) / total * 100;
    const s2 = (emissions.scope2 || 0) / total * 100;
    const s3 = (emissions.scope3 || 0) / total * 100;
    
    // Simple CSS pie chart
    return `<div class="w-32 h-32 rounded-full" style="background: conic-gradient(#3b82f6 0% ${s1}%, #22c55e ${s1}% ${s1+s2}%, #eab308 ${s1+s2}% 100%);"></div>`;
}

function renderBenchmarkBar(label, value, color) {
    const colors = { green: 'bg-green-500', blue: 'bg-blue-500', purple: 'bg-purple-500', gray: 'bg-gray-400' };
    return `<div>
        <div class="flex justify-between text-sm mb-1"><span class="text-gray-600">${label}</span><span class="font-bold">${value}</span></div>
        <div class="bg-gray-100 rounded-full h-3 overflow-hidden"><div class="${colors[color]} h-full rounded-full" style="width: ${value}%"></div></div>
    </div>`;
}


// ============ AI INSIGHT TAB ============
function renderAITab() {
    const esg = analysisData.esg_analysis;
    const logs = analysisData.audit_logs || [];

    const aiSummary = esg.esg_score 
        ? `Based on comprehensive analysis, this project has an ESG score of <strong>${esg.esg_score}</strong>. ${esg.glp_eligibility ? 'The project qualifies for Green Loan Principles under the category: ' + (esg.glp_category || 'General Green') + '.' : 'The project does not currently meet GLP eligibility criteria.'}`
        : 'AI Analysis pending. Complete the application and upload supporting documents to generate insights.';

    return `
        <div class="space-y-6">
            <div class="bg-gradient-to-br from-purple-50 to-indigo-100 rounded-xl p-6 border border-purple-200">
                <h3 class="font-bold text-purple-800 mb-4 flex items-center gap-2">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"/></svg>
                    AI-Generated Summary
                </h3>
                <p class="text-gray-700 leading-relaxed">${aiSummary}</p>
            </div>

            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div class="bg-white rounded-xl p-6 border">
                    <h3 class="font-bold text-gray-800 mb-4">Key Findings</h3>
                    <ul class="space-y-3">
                        <li class="flex items-start gap-2">
                            <span class="${esg.use_of_proceeds_valid ? 'text-green-500' : 'text-red-500'}">●</span>
                            <span>Use of Proceeds: ${esg.use_of_proceeds_valid ? 'Valid and aligned with GLP' : 'Needs clarification'}</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <span class="${esg.dnsh_summary?.overall_pass ? 'text-green-500' : 'text-red-500'}">●</span>
                            <span>DNSH Criteria: ${esg.dnsh_summary?.overall_pass ? 'All criteria passed' : 'Some criteria need attention'}</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <span class="${esg.carbon_lockin?.risk_level === 'low' ? 'text-green-500' : esg.carbon_lockin?.risk_level === 'high' ? 'text-red-500' : 'text-yellow-500'}">●</span>
                            <span>Carbon Lock-in: ${esg.carbon_lockin?.risk_level || 'Unknown'} risk</span>
                        </li>
                        <li class="flex items-start gap-2">
                            <span class="${esg.sector_risk?.level === 'low' ? 'text-green-500' : esg.sector_risk?.level === 'high' ? 'text-red-500' : 'text-yellow-500'}">●</span>
                            <span>Sector Risk: ${esg.sector_risk?.label || 'Unknown'}</span>
                        </li>
                    </ul>
                </div>

                <div class="bg-white rounded-xl p-6 border">
                    <h3 class="font-bold text-gray-800 mb-4">Recommendations</h3>
                    <ul class="space-y-2 text-sm text-gray-600">
                        ${esg.questionnaire_score?.total < 50 ? '<li class="p-2 bg-yellow-50 rounded">• Improve ESG questionnaire responses for better scoring</li>' : ''}
                        ${!esg.glp_eligibility ? '<li class="p-2 bg-yellow-50 rounded">• Review use of proceeds to align with GLP categories</li>' : ''}
                        ${esg.carbon_lockin?.risk_level !== 'low' ? '<li class="p-2 bg-yellow-50 rounded">• Provide transition plan to address carbon lock-in concerns</li>' : ''}
                        ${esg.dnsh_summary?.unclear_count > 0 ? '<li class="p-2 bg-yellow-50 rounded">• Submit additional documentation for unclear DNSH criteria</li>' : ''}
                        <li class="p-2 bg-green-50 rounded">• Ensure annual reporting on environmental impact</li>
                    </ul>
                </div>
            </div>

            <!-- Audit Trail -->
            <div class="bg-white rounded-xl p-6 border">
                <h3 class="font-bold text-gray-800 mb-4">Audit Trail</h3>
                ${logs.length ? `
                <div class="relative border-l-2 border-gray-200 ml-3 space-y-6 pl-6">
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


// ============ CUSTOM Decision TAB ============
function renderDecisionTab() {
    const docs = analysisData.documents || [];

    return `
        <div class="space-y-6">
            <div class="bg-white rounded-xl p-6 border">
                <h3 class="font-bold text-gray-800 mb-4">Lender Decision</h3>
                <textarea id="lender-decision" class="w-full h-40 p-4 border rounded-lg text-sm resize-none focus:ring-2 focus:ring-green-500 focus:border-green-500" placeholder="Add your decision about this application here..."></textarea>
                <div class="mt-3 flex justify-end">
                    <button onclick="window.saveDecision()" class="px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700">Save Decision</button>
                </div>
            </div>

            <div class="bg-white rounded-xl p-6 border">
                <h3 class="font-bold text-gray-800 mb-4">Uploaded Documents</h3>
                ${docs.length ? `
                <div class="space-y-3">
                    ${docs.map(doc => `
                        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div class="flex items-center gap-3">
                                <svg class="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
                                <div>
                                    <p class="font-medium text-gray-800">${doc.filename}</p>
                                    <p class="text-xs text-gray-500">${doc.category || 'Document'} • ${doc.file_type || 'Unknown'}</p>
                                </div>
                            </div>
                            <span class="px-2 py-1 rounded text-xs font-medium ${doc.extraction_status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}">${doc.extraction_status || 'pending'}</span>
                        </div>
                    `).join('')}
                </div>` : '<p class="text-gray-500 text-sm">No documents uploaded yet.</p>'}
            </div>

            <div class="bg-yellow-50 rounded-xl p-6 border border-yellow-200">
                <h3 class="font-bold text-yellow-800 mb-2">Quick Actions</h3>
                <div class="flex flex-wrap gap-3">
                    <button onclick="window.requestMoreInfo()" class="px-4 py-2 bg-yellow-500 text-white rounded-lg font-medium hover:bg-yellow-600">Request More Info</button>
                    <button onclick="window.scheduleReview()" class="px-4 py-2 bg-blue-500 text-white rounded-lg font-medium hover:bg-blue-600">Schedule Review</button>
                    <button onclick="window.exportReport()" class="px-4 py-2 bg-gray-500 text-white rounded-lg font-medium hover:bg-gray-600">Export Report</button>
                </div>
            </div>
        </div>
    `;
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
    const activeBtn = document.querySelector(`#tab-buttons button:nth-child(${['general','esg','stats','ai','decision'].indexOf(tab) + 1})`);
    if (activeBtn) {
        activeBtn.classList.remove('text-gray-500');
        activeBtn.classList.add('text-green-700', 'border-b-2', 'border-green-600', 'bg-green-50');
    }
};

window.updateLoanStatus = async function(loanId, status) {
    try {
        await apiCall(`/analysis/loan/${loanId}/status?status=${status}`, { method: 'POST' });
        alert('Status updated successfully!');
    } catch (e) {
        alert('Error updating status: ' + e.message);
    }
};

window.saveDecision = function() {
    const decision = document.getElementById('lender-decision')?.value;
    console.log('Saving decision:', decision);
    alert('decision saved! (Demo - would persist to backend)');
};

window.requestMoreInfo = function() { alert('Request sent to borrower for additional information.'); };
window.scheduleReview = function() { alert('Review scheduling feature coming soon.'); };
window.exportReport = function() { alert('Report export feature coming soon.'); };
