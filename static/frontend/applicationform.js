import { apiCall, getCurrentUser, API_BASE } from './utils.js';

// Save/load draft helpers (attached to window so they are available in the form)
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
            if (data.shareholder_entities && window.renderShareholderInputs) {
                window.renderShareholderInputs(data.shareholder_entities);
                setTimeout(() => {
                     for (let i = 1; i <= parseInt(data.shareholder_entities, 10); i++) {
                        if(form.elements[`shareholder_${i}_name`]) form.elements[`shareholder_${i}_name`].value = data[`shareholder_${i}_name`] || '';
                        if(form.elements[`shareholder_${i}_percentage`]) form.elements[`shareholder_${i}_percentage`].value = data[`shareholder_${i}_percentage`] || '';
                    }
                }, 100);
            }
        }
    } catch (e) { console.error("Error loading draft", e); }
};

window.renderShareholderInputs = function(count) {
    const container = document.getElementById('shareholder-details-container');
    if (!container) return;
    
    const form = document.getElementById('loan-form');
    const existingData = form ? new FormData(form) : new FormData();

    let existingFieldsHTML = '';
    const num = parseInt(count, 10);
    
    if (!isNaN(num) && num > 0) {
        for (let i = 1; i <= num; i++) {
            const name = existingData.get(`shareholder_${i}_name`) || '';
            const percentage = existingData.get(`shareholder_${i}_percentage`) || '';
            existingFieldsHTML += `
                <div class="md:col-span-1">
                    <label class="block text-[14px] font-medium text-gray-800 mb-2">Shareholder ${i} Name *</label>
                    <input type="text" name="shareholder_${i}_name" required placeholder="Full legal name" value="${name}" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                </div>
                <div class="md:col-span-1">
                    <label class="block text-[14px] font-medium text-gray-800 mb-2">Shareholder ${i} Ownership (%) *</label>
                    <input type="number" step="0.01" min="0" max="100" name="shareholder_${i}_percentage" value="${percentage}" required placeholder="e.g. 25.5" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                </div>
            `;
        }
    }
    container.innerHTML = existingFieldsHTML;
}

export function renderApplicationForm() {
    setTimeout(() => window.loadDraft && window.loadDraft(), 100);


    return `
        <div class="max-w-4xl mx-auto space-y-8">
                    <div class="mb-2">
                    <h2 class="text-lg font-bold text-gray-800 text-center">Loan Applicaton Assement Form</h2>
                    <p class="text-center">Provide correct loan details for a new or existing loan details (can use by both 'Borrower' and 'Lender')</p>
                </div>
            <div class="bg-white rounded-2xl p-8 border border-[color:var(--border-color)]">
                <form id="loan-form" onsubmit="window.handleApplicationSubmit(event)" class="space-y-10">
                    
                    <section>
                        <h3 class="text-xl font-semibold text-[var(--green)] mb-6 flex items-center">
                            <span class="bg-green-100 text-[var(--green)] w-8 h-8 rounded-full flex items-center justify-center text-sm mr-3">1</span>
                            Organization / Company Details
                        </h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div>
                            <label class="block text-[14px] font-medium text-gray-800 mb-2">Organization Name *</label>
                            <input type="text" name="org_name" required placeholder="Legal entity name" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Contact Email *</label>
                                <input type="email" name="contact_email" required placeholder="contact@org.com" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                             <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Contact Phone *</label>
                                <input type="tel" name="contact_phone" required placeholder="+1 555-0123" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>

                            <!-- Org Details -->
                            <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">GST / Tax ID (in India)</label>
                                <input type="text" name="org_gst" placeholder="Registration number" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                             <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Credit Score</label>
                                <input type="text" name="credit_score" placeholder="e.g. 750" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                            
                            <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Headquarters Location</label>
                                <input type="text" name="location" placeholder="City, Country" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Website</label>
                                <input type="url" name="website" placeholder="https://" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Annual Revenue (USD)*</label>
                                <input type="number" step="0.01" name="annual_revenue" required placeholder="Annual revenue (e.g. 1500000)" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>  
                        </div>
                    </section>

                    <!-- Section 2: Project Information -->
                    <section>
                        <h3 class="text-xl font-semibold text-[var(--green)] mb-6 flex items-center">
                            <span class="bg-green-100 text-[var(--green)] w-8 h-8 rounded-full flex items-center justify-center text-sm mr-3">2</span>
                            Project Information
                        </h3>
                        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                            <div class="col-span-2 md:col-span-1">
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Project Title *</label>
                                <input type="text" name="project_name" required placeholder="e.g., Solar Farm Phase II" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                            <div class="col-span-2 md:col-span-1">
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Project Sector *</label>
                                <select name="sector" required class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                    <option value="Fossil fuel utilities">Fossil fuel utilities</option>
                                    <option value="Oil & gas">Oil & gas</option>
                                    <option value="Mining and quarrying">Mining and quarrying</option>
                                    <option value="Chemicals">Chemicals</option>
                                    <option value="Agriculture, forestry, and fishing">Agriculture, forestry, and fishing</option>
                                    <option value="Aviation">Aviation</option>
                                    <option value="Heavy Industry">Heavy Industry</option>
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
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Project Location *</label>
                                <input type="text" name="project_location" required placeholder="Site address" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Project PIN / ZIP Code *</label>
                                <input type="text" name="project_pin_code" required placeholder="Project site code" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                             <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Project *</label>
                                <select name="project_type" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                    <option value="New Project">New Project (Greenfield)</option>
                                    <option value="Expansion">Expansion (Brownfield)</option>
                                    <option value="Refinancing">Refinancing</option>
                                    <option value="Maintenance">Maintenance / Upgrade</option>
                                </select>
                            </div>
                            
                            <!-- Reporting & Existing Loans -->
                             <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Reporting Frequency *</label>
                                <select name="reporting_frequency" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                    <option value="Annual">Annual</option>
                                    <option value="Half-Yearly">Half-Yearly</option>
                                    <option value="Quarterly">Quarterly</option>
                                </select>
                            </div>
                            
                             <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Existing Loans? *</label>
                                <select name="has_existing_loan" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                    <option value="false">No</option>
                                    <option value="true">Yes</option>
                                </select>
                            </div>
                             <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Planned Start Date *</label>
                                <input type="date" name="planned_start_date" required class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Shareholder Entities *</label>
                                <input type="number" min="0" name="shareholder_entities" required placeholder="Number of shareholder entities" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Amount Requested*</label>
                                <div class="relative">
                                     <span class="absolute left-4 top-3.5 text-gray-500 font-bold">$</span>
                                    <input type="number" name="amount" required class="w-full pl-8 pr-4 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                </div>
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Currency *</label>
                                <select name="currency" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                    <option value="USD">USD - US Dollar</option>
                                    <option value="EUR">EUR - Euro</option>
                                    <option value="INR">INR - Indian Rupee</option>
                                    <option value="GBP">GBP - British Pound</option>
                                </select>
                            </div>
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Project Description (500 words) *</label>
                                <textarea name="project_description" required rows="4" placeholder="Describe the project in detail..." class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]"></textarea>
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
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Detailed "Use of Proceeds" (min 500 words) *</label>
                                <textarea name="use_of_proceeds" required rows="4" placeholder="Describe explicitly how the funds will be utilized..." class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]"></textarea>
                            </div>

                            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                                 <div>
                                    <label class="block text-[14px] font-medium text-gray-800 mb-2">Scope 1 Emissions (tCO2e) *</label>
                                    <input type="number" step="0.01" name="scope1_tco2" required placeholder="0.00" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                </div>
                                <div>
                                    <label class="block text-[14px] font-medium text-gray-800 mb-2">Scope 2 Emissions (tCO2e) *</label>
                                    <input type="number" step="0.01" name="scope2_tco2" required placeholder="0.00" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                </div>
                                <div>
                                    <label class="block text-[14px] font-medium text-gray-800 mb-2">Scope 3 Emissions (tCO2e) *</label>
                                    <input type="number" step="0.01" name="scope3_tco2" required placeholder="0.00" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                </div>
                            </div>
                             <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
                                 <div>
                                    <label class="block text-[14px] font-medium text-gray-800 mb-2">GHG Target Reduction (%)</label>
                                    <input type="text" name="target_reduction" placeholder="e.g. 60" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                </div>
                                <div>
                                    <label class="block text-[14px] font-medium text-gray-800 mb-2">GHG Baseline Year</label>
                                    <input type="number" name="baseline_year" placeholder="YYYY" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                                </div>
                            </div>
                            <div>
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Selected KPIs (Comma separated) *</label>
                                <input type="text" name="kpi_metrics" placeholder="e.g. CO2 reduction, Water saved, Energy efficiency" class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                            </div>
                        </div>
                    </section>

                    <section>
  <h3 class="text-xl font-semibold text-[var(--green)] mb-6 flex items-center">
    <span class="bg-green-100 text-[var(--green)] w-8 h-8 rounded-full flex items-center justify-center text-sm mr-3">4</span>
    ESG Compliance Questionnaire
  </h3>

  <div class="space-y-4 mb-8">
    <p class="text-[15px] text-gray-500">Please select the correct option.</p>

    <!-- Question 1 -->
    <div class="mb-2 rounded-lg text-gray-800">
      <p class="text-[15px] font-medium mb-2">
        1. Does the project have clear environmental benefits? *
      </p>
      <div class="flex gap-4">
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="1_Does_the_project_have_clear_environmental_benefits?" value="high" class="text-green-600">
          <span class="text-[14px]">High</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="1_Does_the_project_have_clear_environmental_benefits?" value="medium" class="text-green-600">
          <span class="text-[14px]">Medium</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="1_Does_the_project_have_clear_environmental_benefits?" value="low" class="text-green-600">
          <span class="text-[14px]">Low/None</span>
        </label>
      </div>
    </div>

    <!-- Question 2 -->
    <div class="mb-2 rounded-lg text-gray-800">
      <p class="text-[15px] font-medium mb-2">
        2. Is data available to measure and report impact? *
      </p>
      <div class="flex gap-4">
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="2_Is_data_available_to_measure_and_report_impact?" value="comprehensive" class="text-green-600">
          <span class="text-[14px]">Comprehensive</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="2_Is_data_available_to_measure_and_report_impact?" value="partial" class="text-green-600">
          <span class="text-[14px]">Partial</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="2_Is_data_available_to_measure_and_report_impact?" value="none" class="text-green-600">
          <span class="text-[14px]">None</span>
        </label>
      </div>
    </div>

    <!-- Question 3 -->
    <div class="mb-2 rounded-lg text-gray-800">
      <p class="text-[15px] font-medium mb-2">
        3. Compliance with local environmental regulations? *
      </p>
      <div class="flex gap-4">
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="3_Compliance_with_local_environmental_regulations?" value="fully_compliant" class="text-green-600">
          <span class="text-[14px]">Fully Compliant</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="3_Compliance_with_local_environmental_regulations?" value="in_progress" class="text-green-600">
          <span class="text-[14px]">In Progress</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="3_Compliance_with_local_environmental_regulations?" value="non_compliant" class="text-green-600">
          <span class="text-[14px]">Non-Compliant</span>
        </label>
      </div>
    </div>

    <!-- Question 4 -->
    <div class="mb-2 rounded-lg text-gray-800">
      <p class="text-[15px] font-medium mb-2">
        4. Any controversy or negative social impact risks? *
      </p>
      <div class="flex gap-4">
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="4_Any_controversy_or_negative_social_impact_risks?" value="none" class="text-green-600">
          <span class="text-[14px]">None</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="4_Any_controversy_or_negative_social_impact_risks?" value="minor" class="text-green-600">
          <span class="text-[14px]">Minor/Mitigated</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="4_Any_controversy_or_negative_social_impact_risks?" value="high" class="text-green-600">
          <span class="text-[14px]">High Risk</span>
        </label>
      </div>
    </div>

    <!-- Question 5 -->
    <div class="mb-2 rounded-lg text-gray-800">
      <p class="text-[15px] font-medium mb-2">
        5. Are you implementing any research and development (R&D) for low-carbon technologies or practices? *
      </p>
      <div class="flex gap-4">
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="5_Are_you_implementing_any_research_and_development_(R&D)_for_low-carbon_technologies_or_practices?" value="yes" class="text-green-600">
          <span class="text-[14px]">Yes</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="5_Are_you_implementing_any_research_and_development_(R&D)_for_low-carbon_technologies_or_practices?" value="no" class="text-green-600">
          <span class="text-[14px]">No</span>
        </label>
      </div>
    </div>

    <!-- Question 6 -->
    <div class="mb-2 rounded-lg text-gray-800">
      <p class="text-[15px] font-medium mb-2">
        6. Have you signed a Union agreement? *
      </p>
      <div class="flex gap-4">
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="6_Have_you_signed_a_Union_agreement?" value="yes" class="text-green-600">
          <span class="text-[14px]">Yes</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="6_Have_you_signed_a_Union_agreement?" value="no" class="text-green-600">
          <span class="text-[14px]">No</span>
        </label>
      </div>
    </div>

    <!-- Question 7 -->
    <div class="mb-2 rounded-lg text-gray-800">
      <p class="text-[15px] font-medium mb-2">
        7. Are you adapting GHG Protocol? *
      </p>
      <div class="flex gap-4">
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="7_Are_you_adapting_GHG_Protocol?" value="yes" class="text-green-600">
          <span class="text-[14px]">Yes</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="7_Are_you_adapting_GHG_Protocol?" value="no" class="text-green-600">
          <span class="text-[14px]">No</span>
        </label>
      </div>
    </div>

    <!-- Question 8 -->
    <div class="mb-2 rounded-lg text-gray-800">
      <p class="text-[15px] font-medium mb-2">
        8. Has the organization published climate-related disclosures or reporting? *
      </p>
      <div class="flex gap-4">
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="8_Has_the_organization_published_climate-related_disclosures_or_reporting?" value="yes" class="text-green-600">
          <span class="text-[14px]">Yes</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="8_Has_the_organization_published_climate-related_disclosures_or_reporting?" value="no" class="text-green-600">
          <span class="text-[14px]">No</span>
        </label>
      </div>
    </div>

    <!-- Question 9 -->
    <div class="mb-2 rounded-lg text-gray-800">
      <p class="text-[15px] font-medium mb-2">
        9. Are there clear, time-bound emissions reduction targets aligned with climate pathways? *
      </p>
      <div class="flex gap-4">
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="9_Are_there_clear,_time-bound_emissions_reduction_targets_aligned_with_climate_pathways?" value="yes" class="text-green-600">
          <span class="text-[14px]">Yes</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="9_Are_there_clear,_time-bound_emissions_reduction_targets_aligned_with_climate_pathways?" value="no" class="text-green-600">
          <span class="text-[14px]">No</span>
        </label>
      </div>
    </div>

    <!-- Question 10 -->
    <div class="mb-2 rounded-lg text-gray-800">
      <p class="text-[15px] font-medium mb-2">
        10. Does the company have plans to phase out or avoid new high-carbon infrastructure? *
      </p>
      <div class="flex gap-4">
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="10_Does_the_company_have_plans_to_phase_out_or_avoid_new_high-carbon_infrastructure?" value="yes" class="text-green-600">
          <span class="text-[14px]">Yes</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="10_Does_the_company_have_plans_to_phase_out_or_avoid_new_high-carbon_infrastructure?" value="no" class="text-green-600">
          <span class="text-[14px]">No</span>
        </label>
      </div>
    </div>

    <!-- Question 11 -->
    <div class="mb-2 rounded-lg text-gray-800">
      <p class="text-[15px] font-medium mb-2">
        11. Does the project involve long-lived high-carbon assets that could inhibit future decarbonisation? *
      </p>
      <div class="flex gap-4">
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="11_Does_the_project_involve_long-lived_high-carbon_assets_that_could_inhibit_future_decarbonisation?" value="yes" class="text-green-600">
          <span class="text-[14px]">Yes</span>
        </label>
        <label class="flex items-center space-x-2 cursor-pointer">
          <input type="radio" name="11_Does_the_project_involve_long-lived_high-carbon_assets_that_could_inhibit_future_decarbonisation?" value="no" class="text-green-600">
          <span class="text-[14px]">No</span>
        </label>
      </div>
    </div>

  </div>
</section>

                        <section>

                        <!-- Documents Section -->
                        <div>
                             <h3 class="text-xl font-semibold text-[var(--green)] mb-6 flex items-center">
                            <span class="bg-green-100 text-[var(--green)] w-8 h-8 rounded-full flex items-center justify-center text-sm mr-3">5</span>Supporting Documents</h3>
                             
                             <div class="mb-6">
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Additional Information (Optional)</label>
                                <textarea name="additional_info" rows="3" placeholder="Any other relevant details..." class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]"></textarea>
                             </div>
                             
                             <div class="mb-6">
                                <label class="block text-[14px] font-medium text-gray-800 mb-2">Cloud Document URL (Optional)</label>
                                <input type="url" name="cloud_doc_url" placeholder="https://drive.google.com/..." class="w-full px-3 p-2 border border-gray-300 rounded-xl focus:outline-none bg-gray-50 text-[14px]">
                             </div>

                             <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                                
                                <div class="border-2 border-dashed border-gray-300 rounded-xl p-4 hover:border-green-300 transition-colors">
                                    <label class="block text-[14px] font-medium text-gray-800 mb-1">Project Report Document * </label>
                                    <p class="text-xs text-gray-500 mb-2">Project Proposal Description (PDF/Docx/Xlsx)</p>
                                    <input type="file" id="file-project-description" accept=".pdf,.docx,.xlsx" class="w-full text-[14px] text-gray-500"/>
                                </div>

                                <div class="border-2 border-dashed border-gray-300 rounded-xl p-4 hover:border-green-300 transition-colors">
                                    <label class="block text-[14px] font-medium text-gray-800 mb-1">Annual Report *</label>
                                    <p class="text-xs text-gray-500 mb-2">Annual Report of Company / Organization (PDF, DOCX, XLSX)</p>
                                    <input type="file" required id="file-annual-report" accept=".pdf,.docx,.xlsx" class="w-full text-[14px] text-gray-500"/>
                                </div>

                                <div class="border-2 border-dashed border-gray-300 rounded-xl p-4 hover:border-green-300 transition-colors">
                                    <label class="block text-[14px] font-medium text-gray-800 mb-1">Sustainability Report *</label>
                                    <p class="text-xs text-gray-500 mb-2">Environmental Social Governance Disclosure Docs (PDF/Docx)</p>
                                    <input type="file" id="file-sustainability-report" accept=".pdf,.docx" class="w-full text-[14px] text-gray-500"/>
                                </div>

                                <div class="border-2 border-dashed border-gray-300 rounded-xl p-4 hover:border-green-300 transition-colors">
                                    <label class="block text-[14px] font-medium text-gray-800 mb-1">Use of Proceeds Document (optional)</label>
                                    <p class="text-xs text-gray-500 mb-2">Supporting evidence for Use of Proceeds (PDF/Docx)</p>
                                    <input type="file" id="file-use-of-proceeds" accept=".pdf,.docx" class="w-full text-[14px] text-gray-500"/>
                                </div>
                                
                                
                                <div class="border-2 border-dashed border-gray-300 rounded-xl p-4 hover:border-green-300 transition-colors">
                                    <label class="block text-[14px] font-medium text-gray-800 mb-1">ESG Certifications & Approvals 1</label>
                                    <p class="text-xs text-gray-500 mb-2">Any primary certification</p>
                                    <input type="file" id="file-cert-1" accept=".pdf,.docx,.xlsx" class="w-full text-[14px] text-gray-500"/>
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
                                <label for="consent_checkbox" class="font-medium text-gray-800">I confirm that the information provided is accurate and agree to the <b class="text-green-600 hover:underline cursor-pointer">Terms and Conditions</b>.</label>
                                <p class="text-gray-500">By checking this box, you acknowledge that any false information may affect the loan assesement quality.</p>
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

    // Helper functions for robust parsing
    const parseOptionalFloat = (val) => {
        if (val === null || val.trim() === '') return null;
        const num = parseFloat(val);
        return isNaN(num) ? null : num;
    };
    const parseOptionalInt = (val) => {
        if (val === null || val.trim() === '') return null;
        const num = parseInt(val, 10);
        return isNaN(num) ? null : num;
    };

    // 1. Data Transformation & Parsing for Payload
    const amount_requested = parseOptionalFloat(data.amount);

    const kpi_metrics = (data.kpi_metrics && typeof data.kpi_metrics === 'string')
        ? data.kpi_metrics.split(',').map(s => s.trim()).filter(s => s)
        : [];
    
    // Create a complete questionnaire object
    const questionnaire_data = {
        q_env_benefits: data['1_Does_the_project_have_clear_environmental_benefits?'] || null,
        q_data_available: data['2_Is_data_available_to_measure_and_report_impact?'] || null,
        q_regulatory_compliance: data['3_Compliance_with_local_environmental_regulations?'] || null,
        q_social_risk: data['4_Any_controversy_or_negative_social_impact_risks?'] || null,
        q_rd_low_carbon: data['5_Are_you_implementing_any_research_and_development_(R&D)_for_low-carbon_technologies_or_practices?'] || null,
        q_union_agreement: data['6_Have_you_signed_a_Union_agreement?'] || null,
        q_adopt_ghg_protocol: data['7_Are_you_adapting_GHG_Protocol?'] || null,
        q_published_climate_disclosures: data['8_Has_the_organization_published_climate-related_disclosures_or_reporting?'] || null,
        q_timebound_targets: data['9_Are_there_clear,_time-bound_emissions_reduction_targets_aligned_with_climate_pathways?'] || null,
        q_phaseout_highcarbon: data['10_Does_the_company_have_plans_to_phase_out_or_avoid_new_high-carbon_infrastructure?'] || null,
        q_long_lived_highcarbon_assets: data['11_Does_the_project_involve_long-lived_high-carbon_assets_that_could_inhibit_future_decarbonisation?'] || null,
    };

    // Collect Shareholders Data
    const shareholder_count = parseOptionalInt(data.shareholder_entities) || 0;
    const shareholders_data = [];
    for (let i = 1; i <= shareholder_count; i++) {
        const sName = data[`shareholder_${i}_name`];
        const sPct = data[`shareholder_${i}_percentage`];
        if (sName || sPct) {
            shareholders_data.push({
                name: sName || '',
                percentage: parseOptionalFloat(sPct)
            });
        }
    }

    const payload = {
        org_name: data.org_name,
        sector: data.sector,
        org_gst: data.org_gst,
        credit_score: parseOptionalInt(data.credit_score),
        annual_revenue: parseOptionalFloat(data.annual_revenue),
        location: data.location,
        website: data.website,
        contact_email: data.contact_email,
        contact_phone: data.contact_phone,

        project_name: data.project_name,
        project_location: data.project_location,
        project_pin_code: data.project_pin_code,
        project_type: data.project_type,
        reporting_frequency: data.reporting_frequency,
        has_existing_loan: data.has_existing_loan === 'true',

        amount_requested: amount_requested,
        currency: data.currency,

        project_description: data.project_description,
        planned_start_date: data.planned_start_date,
        shareholder_entities: shareholder_count,
        shareholders_data: shareholders_data,

        use_of_proceeds_description: data.use_of_proceeds,
        scope1_tco2: parseOptionalFloat(data.scope1_tco2),
        scope2_tco2: parseOptionalFloat(data.scope2_tco2),
        scope3_tco2: parseOptionalFloat(data.scope3_tco2),
        
        ghg_baseline_year: parseOptionalInt(data.baseline_year),
        ghg_target_reduction: parseOptionalFloat(data.target_reduction),
        
        kpi_metrics: kpi_metrics,

        additional_info: data.additional_info || null,
        cloud_doc_url: data.cloud_doc_url || null,
        consent_agreed: data.consent_agreed === 'on',
        questionnaire_data: questionnaire_data
    };

    try {
        const currentUser = getCurrentUser();
        if (!currentUser) throw new Error("User not confirmed. Please reload.");

        // Submit Application Data using standard API Call
        const res = await apiCall('/borrower/apply', {
            method: 'POST',
            body: JSON.stringify(payload)
        });

        // Immediately acknowledge submission and disable submit to avoid duplicates
        const submitBtn = e.target.querySelector('button[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            const origText = submitBtn.innerText;
            submitBtn.innerText = 'Submitting...';
            // Start background uploads so user sees immediate confirmation
            if (res && res.id) {
                const appId = res.id;
                alert(`✅ Application submission initiated with Loan ID: ${appId}. Information is under validation...`);

                (async () => {
                    const uploadQueue = [
                        { id: 'file-project-description', cat: 'project_description' },
                        { id: 'file-annual-report', cat: 'annual_report' },
                        { id: 'file-sustainability-report', cat: 'sustainability_report' },
                        { id: 'file-use-of-proceeds', cat: 'use_of_proceeds' },
                        { id: 'file-cert-1', cat: 'certification_1' }
                    ];

                    let uploadCount = 0;
                    const uploadedFiles = [];

                    for (const item of uploadQueue) {
                        const fileInput = document.getElementById(item.id);
                        if (fileInput && fileInput.files[0]) {
                            const uploadData = new FormData();
                            uploadData.append('file', fileInput.files[0]);
                            uploadData.append('category', item.cat);

                            try {
                                const resp = await fetch(`${API_BASE}/borrower/${appId}/documents`, {
                                    method: 'POST',
                                    body: uploadData
                                });

                                if (resp.ok) {
                                    const json = await resp.json();
                                    uploadCount++;
                                    uploadedFiles.push(json.filename || item.id);
                                } else {
                                    console.error(`Failed to upload ${item.cat}`, resp.statusText);
                                }
                            } catch (e) {
                                console.error(`Failed to upload ${item.cat}`, e);
                            }
                        }
                    }

                    const filesMsg = uploadedFiles.length ? `\n\nFiles uploaded:\n- ${uploadedFiles.join('\n- ')}` : '';
                    alert(`✅ All uploads complete for Loan ID: ${appId}. Documents Uploaded: ${uploadCount}${filesMsg}`);
                    submitBtn.disabled = false;
                    submitBtn.innerText = origText;
                    window.navigateTo('dashboard');
                })();

            } else {
                // If creation failed, re-enable submit button
                submitBtn.disabled = false;
                submitBtn.innerText = origText;
            }
        }

    } catch (err) {
        console.error(err);
        alert('Failed to submit application: ' + err.message);
    }
}