ESG_EXTRACTION_PROMPT = """
You are an expert ESG analyst. Based on the following document context, extract key ESG metrics with clear labels.

Context:
{context}

Extract the following (if mentioned):
- Baseline emissions (Scope 1, Scope 2, Scope 3)
- Target emissions (with year)
- Installed renewable capacity or relevant capacity metrics
- Expected energy savings or efficiency gains
- Any specific KPI values mentioned (with units)

Provide your answer as JSON with keys and values.
"""

USE_OF_PROCEEDS_PROMPT = """
You are a financial document specialist. Based on the context below, identify:
1. What the loan proceeds will be used for.
2. Which parts are explicitly green or sustainability related.
3. Any use that does not appear green.

Context:
{context}

Return a JSON with:
- "use_of_proceeds"
- "green_component"
- "non_green_component"
- "allocation_breakdown"
"""

COMPLIANCE_SUMMARY_PROMPT = """
You are an expert in regulatory compliance for ESG loans. Analyze the text below and identify:
- statements of compliance commitments
- permits and certifications
- reporting requirements

Context:
{context}

Return results as clean JSON.
"""

LMA_CHECKLIST_PROMPT = """
You are assessing documents for LMA Green/Transition Loan Principle compliance. Given the context:
{context}

Try to find the answer of this points and summarize into one line:
- use_of_proceeds?
- KPI definitions?
- emissions targets>
- governance statements?

Return JSON as question:answer
"""
