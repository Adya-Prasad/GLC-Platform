# Frequently Asked Questions

## General Questions

### Q1. What is the GLC Platform?
GLC (Green Lending Cycle) Platform is an AI-powered solution that automates ESG-linked loan assessments. It helps lenders evaluate green loan applications against LMA Green Loan Principles and Sustainability-Linked Loan Principles.

### Q2. Who is this platform for?
- **Borrowers**: Companies seeking green financing for sustainable projects
- **Lenders**: Banks and financial institutions evaluating green loan applications

### Q3. What are Green Loan Principles (GLP)?
GLP are voluntary guidelines by the Loan Market Association (LMA) with four core components:
1. Use of Proceeds
2. Process for Project Evaluation and Selection
3. Management of Proceeds
4. Reporting

---

## Account & Login

### Q4. What are the demo credentials?
| Role | Email | Passcode |
| :--- | :--- | :--- |
| Lender | lender@glc.com | lender123 |
| Borrower | borrower@glc.com | borrower123 |

### Q5. I forgot my passcode. What do I do?
For the hackathon demo, create a new account with a slightly different organization name. In production, a password reset feature would be implemented.

---

## Loan Applications

### Q6. What documents should I upload?
The most important document is `sustainability_report.pdf` - this enables AI analysis. Other helpful documents:
- Project plans
- Environmental impact assessments
- Permits and certifications

### Q7. Why is my ESG Score showing N/A?
ESG Score requires:
- Completed questionnaire responses
- Use of proceeds description
- Project details filled in

Run the AI Agent on the Audit page to trigger score calculation.

### Q8. What is Baseline Year in emissions?
The Baseline Year is the reference year for measuring emission reductions. For example, "reduce emissions by 50% by 2030" means 50% less than the baseline year emissions. It provides a consistent benchmark for tracking progress.

### Q9. Why does shareholder count show "+1"?
The displayed number includes the current lender as a stakeholder in the loan, so it shows `entered_number + 1`.

---

## AI Features

### Q10. How does the AI Agent work?
The AI Agent:
1. Extracts text from your sustainability report (PDF/DOCX)
2. Uses NLP models to identify key ESG metrics
3. Answers 5 LMA Framework questions automatically
4. Generates a summary and essential points

### Q11. What are the 5 LMA Framework Questions?
1. Extract financial statements or financial performance information
2. Extract waste management practices
3. Extract labor and employee practices
4. Extract renewable energy usage or plans
5. Extract environmental protection and pollution control measures

### Q12. Why is the AI chat not responding well?
In local host, make sure Model safetensors are downloaded with Huggingface <br>
The AI works best with:
- Clear, specific questions
- Keywords like "financial", "emissions", "renewable", "waste", "employee"
- Questions about topics covered in the uploaded sustainability report

### Q13. What is the AI Retrieval Insights PDF?
A professionally formatted PDF report containing:
- Executive summary
- Essential points with importance levels
- Quantitative metrics extracted
- Answers to LMA Framework questions
- Analysis confidence score

---

## ESG Scoring

### Q14. How is the ESG Score calculated?
| Factor | Weight |
| :--- | :--- |
| Questionnaire Responses | 30% |
| GLP Alignment | 25% |
| DNSH Compliance | 15% |
| Sector Risk | 10% |
| Data Completeness | 15% |
| Emissions Reporting | 5% |

### Q15. What makes a project GLP Eligible?
- Use of proceeds aligns with green categories (Renewable Energy, Clean Transport, etc.)
- Clear environmental benefits demonstrated
- DNSH criteria satisfied
- No significant carbon lock-in risks

### Q16. What is DNSH (Do No Significant Harm)?
DNSH ensures projects don't cause significant harm to:
- Climate change mitigation
- Climate change adaptation
- Water resources
- Circular economy
- Pollution prevention
- Biodiversity

### Q17. What is Carbon Lock-in Risk?
Risk that a project creates long-term dependency on fossil fuels or high-carbon infrastructure. High-risk indicators include fossil fuel infrastructure, coal projects, and oil/gas pipelines.

---

## Technical Questions

### Q18. What technology stack is used?
| Component | Technology |
| :--- | :--- |
| Backend | Python 3.12 + FastAPI |
| Database | SQLite + SQLAlchemy |
| AI/NLP | HuggingFace Transformers (BART, DistilBERT) |
| Vector Search | FAISS |
| Frontend | Vanilla JavaScript + TailwindCSS |
| PDF Generation | WeasyPrint |

### Q19. How do I run the platform locally?
```bash
# Create environment
conda create --prefix .\.conda_env python=3.12 -y
conda activate .\.conda_env

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn app.main:app --reload --port 8000

# Open browser
http://localhost:8000
```

### Q20. Where are documents stored?
Documents are stored in `loan_assets/LOAN_{id}/` folders. AI-generated reports are saved as `ai_retrieval_insights.pdf` in the same location.

---

## Troubleshooting

### Q21. Page not updating after changes?
Clear browser cache with `Ctrl+Shift+R` (hard refresh).

### Q22. AI Agent taking too long?
First run loads ML models (~30 seconds). Subsequent runs are faster. If timeout occurs, click "Retry".

### Q23. PDF report not generating?
Ensure WeasyPrint is installed: `pip install weasyprint`. If issues persist, the system saves as HTML fallback.

### Q24. API errors in console?
Restart the uvicorn server: `uvicorn app.main:app --reload --port 8000`

---

## Contact & Support

For hackathon demo support or questions, refer to the README.md or project documentation.
