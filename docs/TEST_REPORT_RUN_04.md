# Agent AI — Test Report Run 04

**Project:** Agent AI Chatbot  
**Module:** Authentication  
**Test Scope:** Logout Flow  
**Test Type:** Manual End-to-End Testing  
**Environment:** Local Development (Docker)  
**Date:** 2026-03-31  
**Tester:** Paweł Staniewski

---

# 1. Objective

The purpose of this test run was to validate logout behavior and post-logout session security in the authentication system.

The tested flow included:

- user logout behavior
- token removal from LocalStorage
- session persistence after logout
- prevention of session restoration after logout
- browser navigation behavior after logout

---

# 2. Environment

Backend:

- Django REST Framework
- SimpleJWT authentication
- PostgreSQL database

Frontend:

- React
- AuthContext logout handling
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
- manual logout action
- automatic session bootstrap on application load

---

# 3. Test Cases Executed

| Test ID     | Test Case                 | Result | Notes                                       |
| ----------- | ------------------------- | ------ | ------------------------------------------- |
| AUTH-OUT-01 | Logout                    | PASS   | Tokens removed and user redirected to login |
| AUTH-OUT-02 | Refresh after logout      | PASS   | User remained logged out after page refresh |
| AUTH-OUT-03 | Browser back after logout | PASS   | User could not regain authenticated access  |

---

# 4. Detailed Test Results

## AUTH-OUT-01 — Logout

### Steps

User logged into the application and accessed the main application view.

User clicked the Logout button.

### Observed Behavior

User was immediately redirected to the login screen.

All authentication tokens were removed from LocalStorage.

No authenticated session remained active.

### Result

Logout functionality works correctly and terminates the user session securely.

---

## AUTH-OUT-02 — Refresh after logout

### Steps

After performing logout, the browser page was refreshed.

### Observed Behavior

User remained on the login screen.

No authentication tokens were restored.

The session bootstrap logic did not attempt to recover the session.

### Result

Session persistence after logout is correctly prevented.

---

## AUTH-OUT-03 — Browser back after logout

### Steps

User logged into the application and accessed the protected application view.

User performed logout and was redirected to the login screen.

User pressed the browser Back button.

### Observed Behavior

Browser navigation returned to a previous non-authenticated state.

The protected application view was not restored.

No authenticated access could be regained.

Authentication tokens remained absent from LocalStorage.

### Result

Browser navigation after logout does not restore access to protected content.

Post-logout session security is enforced correctly.

---

# 5. Issues Found

No issues were identified during logout testing.

---

# 6. Summary

The logout module passed all test scenarios without errors.

Total executed tests:

3

Passed:

3

Failed:

0

---

# 7. Conclusion

The logout functionality is stable and secure.

Validated successfully:

- secure session termination
- removal of authentication tokens
- prevention of session restoration after logout
- protection against unauthorized access through browser navigation
- correct handling of post-logout application state

---

# 8. Authentication Module Status

The authentication module has now been validated across four test runs:

- TEST_REPORT_RUN_01 — Registration
- TEST_REPORT_RUN_02 — Login
- TEST_REPORT_RUN_03 — Session / Token Flow
- TEST_REPORT_RUN_04 — Logout Flow

Authentication can be considered fully validated for the current project stage.
