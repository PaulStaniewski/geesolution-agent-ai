# Agent AI — Test Report Run 03

**Project:** Agent AI Chatbot  
**Module:** Authentication  
**Test Scope:** Session / Token Flow  
**Test Type:** Manual End-to-End Testing  
**Environment:** Local Development (Docker)  
**Date:** 2026-03-30  
**Tester:** Paweł Staniewski

---

# 1. Objective

The purpose of this test run was to validate session persistence and JWT token lifecycle behavior in the authentication system.

The tested flow included:

- session persistence after page refresh
- direct access to protected routes
- recovery from missing access token
- invalid refresh token handling
- access token renewal behavior
- logout behavior when refresh token is missing or invalid

---

# 2. Environment

Backend:

- Django REST Framework
- SimpleJWT authentication
- PostgreSQL database

Frontend:

- React
- AuthContext session bootstrap
- JWT token storage in LocalStorage
- Axios API integration

Infrastructure:

- Docker Compose
- Django container
- PostgreSQL container

Authentication Model:

- email-based authentication
- JWT access token
- JWT refresh token
- automatic session bootstrap on application load

---

# 3. Test Cases Executed

| Test ID     | Test Case                        | Result | Notes                                          |
| ----------- | -------------------------------- | ------ | ---------------------------------------------- |
| AUTH-SES-01 | Session persistence              | PASS   | User remained logged in after page refresh     |
| AUTH-SES-02 | Direct access to protected route | PASS   | Access preserved in new tab when authenticated |
| AUTH-SES-03 | Missing access token             | PASS   | Session restored using refresh token           |
| AUTH-SES-04 | Invalid refresh token            | PASS   | User redirected to login                       |
| AUTH-SES-05 | Expired access token             | PASS   | Access token recovery logic validated          |
| AUTH-SES-06 | Expired refresh token            | PASS   | User redirected to login                       |

---

# 4. Detailed Test Results

## AUTH-SES-01 — Session persistence

### Steps

User logged in successfully and refreshed the browser page.

### Observed Behavior

User remained authenticated after refresh.

### Result

Session persistence works correctly.

---

## AUTH-SES-02 — Direct access to protected route

### Steps

User opened the application in a new browser tab while authenticated.

### Observed Behavior

User remained logged in and the protected application view was accessible.

After logout, opening a new tab and refreshing preserved the logged-out state.

### Result

Protected route access and session bootstrap work correctly.

---

## AUTH-SES-03 — Missing access token

### Steps

While logged in, the access token stored in LocalStorage was manually removed.  
The refresh token remained valid.  
The page was then refreshed.

### Observed Behavior

User remained authenticated after refresh.

### Result

The application successfully restored the session using the refresh token.

### Note

This scenario initially failed during testing because the session bootstrap logic did not attempt token refresh when access token was missing.

The issue was fixed by updating the bootstrap flow to:

- detect missing access token
- attempt refresh using refresh token
- restore session automatically

---

## AUTH-SES-04 — Invalid refresh token

### Steps

While logged in, the refresh token was manually replaced with an invalid value.  
The access token was removed.  
The page was then refreshed.

### Observed Behavior

User was redirected to the login screen.

### Result

The application correctly cleared the invalid session and forced re-authentication.

---

## AUTH-SES-05 — Expired access token

### Steps

The access token lifetime was temporarily reduced for testing purposes.

User logged in and waited until the access token expired.

A protected API request was then triggered.

### Observed Behavior

The initial request returned:

401 Unauthorized

The application automatically performed:

POST /api/v1/token/refresh/ -> 200

The original request was then retried successfully:

GET /api/v1/messages/ -> 200

User remained authenticated during the process.

### Result

The automatic token refresh and request retry mechanism works correctly.

---

## AUTH-SES-06 — Expired refresh token

### Steps

Refresh token was missing or invalid during session restore attempt.

### Observed Behavior

User was redirected to the login screen.

### Result

The application correctly forced logout when refresh token could not be used.

---

# 5. Issues Found

## BUG-002 — Session bootstrap did not recover when access token was missing

**Status:** Fixed during testing  
**Severity:** Medium

**Description:**  
When access token was removed from LocalStorage but refresh token was still valid, the application immediately cleared the session instead of attempting refresh.

**Resolution:**  
The bootstrapAuthSession logic was updated to attempt refresh token recovery when access token is missing.

---

# 6. Summary

The session and token lifecycle module passed all test scenarios after one fix in bootstrap logic.

Total executed tests:

6

Passed:

6

Failed:

0

---

# 7. Conclusion

The authentication session lifecycle is stable and production-ready.

Validated successfully:

- persistent login after refresh
- direct access to protected views
- session recovery using refresh token
- logout on invalid refresh token
- logout on missing refresh token
- access token recovery behavior

---

# 8. Authentication Module Status

The authentication module has now been validated across three test runs:

- TEST_REPORT_RUN_01 — Registration
- TEST_REPORT_RUN_02 — Login
- TEST_REPORT_RUN_03 — Session / Token Flow

Authentication can be considered functionally complete for the current project stage.
