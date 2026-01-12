# User Login & Registration Guide

Welcome to the Green Lending Cycle (GLC) Platform! This guide helps you get started with account creation and login.

## 1. Getting Started

Navigate to the login page at `http://localhost:8000`. You'll see role selection options.

## 2. User Roles

| Role | Description | Capabilities |
| :--- | :--- | :--- |
| **Borrower** | Companies seeking green loans | Submit applications, upload documents, track status |
| **Lender** | Financial institutions | Review applications, run AI analysis, make decisions |

## 3. Demo Credentials (For Judges)

For quick testing, use these pre-configured accounts:

| Role | Email/Name | Passcode |
| :--- | :--- | :--- |
| **Lender** | lender@glc.com | lender123 |
| **Borrower** | borrower@glc.com | borrower123 |

## 4. Creating a New Account

1. **Select Role**: Click "Enter as Borrower" or "Enter as Lender"
2. **Enter Organization Name**: Your company or bank name
3. **Create Passcode**: Enter a 6-digit passcode
4. **Click Continue**: Account is created and you're logged in

> **Note**: You'll see a "🎉 Welcome!" message confirming your new account.

## 5. Logging In (Existing Users)

1. **Select Role**: Choose your role
2. **Enter Organization Name**: Exactly as registered
3. **Enter Passcode**: Your 6-digit passcode
4. **Click Continue**: You're logged in

> **Note**: You'll see a "✅ Welcome back!" message on successful login.

## 6. After Login

### Borrower Flow
1. **Dashboard**: View your applications overview
2. **New Application**: Submit a green loan request
3. **My Applications**: Track application status
4. **Loan Assets**: Manage uploaded documents
5. **Audit Report**: View detailed ESG analysis

### Lender Flow
1. **Dashboard**: Portfolio overview with all applications
2. **All Applications**: Review pending applications
3. **Loan Assets**: Access all loan documents
4. **Audit Report**: Run AI analysis, make decisions

## 7. Troubleshooting

| Issue | Solution |
| :--- | :--- |
| "Incorrect passcode" | Verify 6-digit code; try demo credentials |
| "User not found" | Check organization name spelling |
| "Network Error" | Ensure server is running (`uvicorn app.main:app --reload`) |
| Page not loading | Clear browser cache (Ctrl+Shift+R) |

## 8. Security Notes

- Passcodes are stored securely
- Sessions persist in browser localStorage
- Log out by clearing browser data or using logout option
- For production, implement proper authentication (OAuth, JWT)

## 9. Quick Start for Judges

1. Open `http://localhost:8000`
2. Click "Enter as Lender"
3. Enter: `lender@glc.com` / `lender123`
4. Explore Dashboard → Click any loan → View Audit Report
5. Go to AI Insight tab → Click "Initiate AI Agent"
6. Chat with documents, save AI report
