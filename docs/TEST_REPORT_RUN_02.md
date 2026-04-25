# Agent AI — Test Report Run 02

**Project:** Agent AI Chatbot  
**Module:** Authentication  
**Test Scope:** Login Flow  
**Test Type:** Manual End-to-End Testing  
**Environment:** Local Development (Docker)  
**Date:** 2026-03-30  
**Tester:** Paweł Staniewski  

---

# 1. Objective

The purpose of this test run was to validate the login functionality of the authentication system.

The tested flow included:

- successful login
- invalid password handling
- non-existing user handling
- form validation
- prevention of duplicate login requests

---

# 2. Environment

Backend:

- Django REST Framework
- SimpleJWT authentication
- PostgreSQL database

Frontend:

- React
- AuthContext state management
- JWT token handling
- Axios API integration

Infrastructure:

- Docker Compose
- Django container
- PostgreSQL container

Authentication Model:

- email-based login
- password authentication
- JWT access + refresh tokens

---

# 3. Test Cases Executed

| Test ID | Test Case | Result | Notes |
|--------|-----------|--------|------|
| AUTH-LOG-01 | Valid login | PASS | User authenticated successfully |
| AUTH-LOG-02 | Invalid password | PASS | Error message displayed |
| AUTH-LOG-03 | Non-existing user | PASS | Error message displayed |
| AUTH-LOG-04 | Empty login fields | PASS | Form validation triggered |
| AUTH-LOG-05 | Multiple login clicks | PASS | No duplicate requests detected |

---

# 4. Detailed Test Results

## AUTH-LOG-01 — Valid login

### Steps

User entered valid email and password and clicked Sign in.

### Observed Behavior

System response:

POST /api/v1/token/ → 200 OK  
GET /api/v1/me/ → 200 OK  
GET /api/v1/conversations/ → 200 OK  
GET /api/v1/documents/ → 200 OK  

### Result

User was successfully authenticated and redirected to the main application view.

---

## AUTH-LOG-02 — Invalid password

### Steps

User entered valid email and incorrect password.

### Observed Behavior

POST /api/v1/token/ → 400 Bad Request  

Frontend displayed:

Invalid email or password.

### Result

System correctly rejected authentication attempt.

---

## AUTH-LOG-03 — Non-existing user

### Steps

User entered an email address not present in the system.

### Observed Behavior

POST /api/v1/token/ → 400 Bad Request  

Frontend displayed:

Invalid email or password.

### Result

System correctly handled login attempt without revealing whether the account exists.

This behavior follows security best practices.

---

## AUTH-LOG-04 — Empty login fields

### Steps

User attempted to submit login form without filling required fields.

### Observed Behavior

Browser validation triggered:

Please fill out this field.

Invalid email format triggered:

Please enter an email address.

### Result

Frontend validation correctly prevented form submission.

---

## AUTH-LOG-05 — Multiple login clicks

### Steps

User repeatedly clicked the Sign in button multiple times in rapid succession.

### Observed Behavior

Only one API request was sent:

POST /api/v1/token/

Button became disabled during login process.

### Result

System successfully prevented duplicate login requests.

This behavior is controlled by:

isLoggingIn state  
disabled button logic  

---

# 5. Issues Found

No functional issues detected during login testing.

---

# 6. Summary

The login module passed all executed test scenarios.

Total executed tests:

5

Passed:

5

Failed:

0

---

# 7. Conclusion

The login flow is considered stable and production-ready.

Validated successfully:

- credential authentication
- error handling
- frontend validation
- request control
- security behavior
- session initialization

---

# Next Planned Test Run

TEST_REPORT_RUN_03

Scope:

- session persistence after page refresh
- logout functionality
- token expiration handling
- protected endpoint access control