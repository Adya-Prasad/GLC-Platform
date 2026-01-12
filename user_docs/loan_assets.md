# Loan Assets Guide

The Loan Assets page is your document management center for all loan-related files and AI-generated reports.

## 1. Overview

Loan Assets provides a centralized view of all documents associated with your loan applications, including uploaded files and AI-generated reports.

## 2. Page Layout

### Header Section
- **Title**: "Reports and Data"
- **Description**: Centrally distributed collection of data and generated reports

### Loan Cards

Each loan application has its own card showing:
- **Loan ID**: Unique identifier (e.g., LOAN_1)
- **Project Name**: Name of the green project
- **Upload Button**: Add new documents to this loan

### Document List

For each loan, documents are displayed with:
- **Filename**: Name of the document
- **File Type**: PDF, DOCX, AI Report, etc.
- **Actions**: View, Download, Share

## 3. Document Types

| Type | Description | Source |
| :--- | :--- | :--- |
| **sustainability_report.pdf** | Annual sustainability/ESG report | User Upload |
| **project_plan.pdf** | Project details and plans | User Upload |
| **environmental_impact.pdf** | Environmental assessments | User Upload |
| **permits.pdf** | Government approvals | User Upload |
| **application_data.json** | Raw application data | System Generated |
| **ai_retrieval_insights.pdf** | AI analysis report | AI Generated |

## 4. AI Retrieval Insights Report

The `ai_retrieval_insights.pdf` is automatically generated when a lender clicks "Save AI Report" on the Audit page.

### Report Contents

| Section | Description |
| :--- | :--- |
| **Header** | GLC Platform branding with report title |
| **Metadata** | Loan ID, Project, Organization, Amount, Confidence, Pages Analyzed |
| **Executive Summary** | AI-generated summary of the sustainability report |
| **Essential Points** | Key findings with importance levels |
| **Quantitative Data** | Extracted metrics (emissions, revenue, targets) |
| **LMA Framework Questions** | Answers to 5 key ESG questions |
| **Footer** | Generation timestamp and confidence score |

### How to Generate

1. Go to **Audit Report** page
2. Select the loan application
3. Navigate to **AI Insight** tab
4. Click **"Initiate AI Agent"** to run analysis
5. Click **"Save AI Report"** (green button)
6. Report appears in Loan Assets

## 5. Document Actions

### View Document
- Click the **eye icon** to preview documents
- PDFs open in a document viewer modal
- Supports zoom and page navigation

### Download Document
- Click the **download icon** to save locally
- Downloads in original format

### Share Document
- Click the **share icon** to copy shareable URL
- URL can be shared with stakeholders

### Upload New Document
- Click **"Upload"** button on loan card
- Select file from your computer
- Supported formats: PDF, DOCX, DOC

## 6. Document Categories

Documents are organized by loan application:

```
loan_assets/
├── LOAN_1/
│   ├── sustainability_report.pdf
│   ├── project_plan.pdf
│   ├── application_data.json
│   └── ai_retrieval_insights.pdf
├── LOAN_2/
│   ├── sustainability_report.pdf
│   └── ai_retrieval_insights.pdf
└── ...
```

## 7. Role-Based Access

| Action | Borrower | Lender |
| :--- | :---: | :---: |
| View own documents | ✓ | ✓ |
| View all documents | ✗ | ✓ |
| Upload documents | ✓ | ✓ |
| Download documents | ✓ | ✓ |
| Generate AI Report | ✗ | ✓ |

## 8. Tips

- **Upload sustainability_report.pdf**: Required for AI analysis to work
- **Check AI Report**: Review the generated insights before making decisions
- **Keep documents organized**: Use clear filenames for easy identification
- **Download for records**: Save important reports locally for compliance
