"""Test submit script
Reads test.json (nested sample), transforms into flat payload expected by /borrower/apply, and POSTs to localhost:8000
"""
import json
import sys
import httpx

TEST_FILE = 'test.json'
API_URL = 'http://localhost:8000/api/v1/borrower/apply'

def transform(nested):
    org = nested.get('organization_details', {})
    proj = nested.get('project_information', {})
    green = nested.get('green_qualification_and_kpis', {})
    q = nested.get('esg_compliance_questionnaire', {})

    payload = {
        'org_name': org.get('organization_name'),
        'contact_email': org.get('contact_email'),
        'contact_phone': org.get('contact_phone'),
        'org_gst': org.get('tax_id'),
        'credit_score': org.get('Credit Score'),
        'location': org.get('headquarters_location'),
        'website': org.get('website'),
        'annual_revenue': org.get('annual_revenue'),

        'project_name': proj.get('project_title'),
        'sector': proj.get('project_sector'),
        'project_location': proj.get('project_location'),
        'project_pin_code': proj.get('project_pin_code'),
        'project_type': proj.get('project_type'),
        'reporting_frequency': proj.get('reporting_frequency'),
        'has_existing_loan': True if str(proj.get('existing_loans','')).lower() in ('yes','true') else False,
        'planned_start_date': proj.get('planned_start_date'),
        'shareholder_entities': int(proj.get('shareholder_entities', 0)),
        'amount': proj.get('amount_requested'),
        'currency': proj.get('currency'),
        'project_description': proj.get('project_description'),

        'use_of_proceeds': green.get('use_of_proceeds_description'),
        'scope1_tco2': green.get('scope1_tco2'),
        'scope2_tco2': green.get('scope2_tco2'),
        'scope3_tco2': green.get('scope3_tco2'),
        'ghg_target_reduction': green.get('ghg_target_reduction'),
        'baseline_year': green.get('ghg_baseline_year'),
        'kpi_metrics': green.get('selected_kpis', []),

        'questionnaire_data': q,
        'consent_agreed': True
    }
    return payload


def main():
    try:
        with open(TEST_FILE, 'r', encoding='utf-8') as f:
            nested = json.load(f)
    except Exception as e:
        print('Could not read test.json:', e)
        sys.exit(1)

    payload = transform(nested)
    print('Posting payload to', API_URL)
    try:
        r = httpx.post(API_URL, json=payload, timeout=20)
        print('Status:', r.status_code)
        print(r.text)
    except Exception as e:
        print('Request failed:', e)

if __name__ == '__main__':
    main()