# Agent AI — Test Report Run 05

**Project:** Agent AI Chatbot
**Module:** Authentication / Authorization
**Test Scope:** Permissions / Data Isolation
**Test Type:** Manual End-to-End Testing
**Environment:** Local Development (Docker)
**Date:** 2026-03-31
**Tester:** Paweł Staniewski

---

# 1. Objective

The purpose of this test run was to validate authorization rules and data isolation between authenticated users.

The tested flow included:

* access to protected resources without authentication
* prevention of unauthorized access to other user's conversations
* prevention of unauthorized access to other user's documents
* validation of per-user data isolation
* verification of server-side authorization enforcement

---

# 2. Environment

Backend:

* Django REST Framework
* SimpleJWT authentication
* PostgreSQL database
* User-scoped query filtering

Frontend:

* React
* AuthContext session management
* Axios API integration
* Protected route handling

Infrastructure:

* Docker Compose
* Django container
* PostgreSQL container

Authorization Model:

* user-based resource ownership
* row-level data isolation
* authenticated access required for protected resources

---

# 3. Test Cases Executed

| Test ID      | Test Case                         | Result | Notes                                                   |
| ------------ | --------------------------------- | ------ | ------------------------------------------------------- |
| AUTH-PERM-01 | Access without token              | PASS   | User redirected to login without authentication         |
| AUTH-PERM-02 | Access other user's conversations | PASS   | Server returned 404 when accessing foreign conversation |
| AUTH-PERM-03 | Access other user's documents     | PASS   | Document list isolated per user account                 |

---

# 4. Detailed Test Results

## AUTH-PERM-01 — Access without token

### Steps

User removed authentication tokens from LocalStorage.

User attempted to access the protected application view.

### Observed Behavior

The application prevented access to protected resources.

User was redirected to the login screen.

No authenticated session was restored.

### Result

Unauthorized access without authentication is correctly blocked.

---

## AUTH-PERM-02 — Access other user's conversations

### Steps

User A created a conversation and generated messages.

Conversation ID was recorded.

User A logged out.

User B logged into the application.

User B attempted to access the conversation directly using:

GET /api/v1/messages/?conversation_id=277

### Observed Behavior

The server returned:

404 Not Found
{"detail":"No Conversation matches the given query."}

When the same request was executed by the conversation owner (User A), the server returned:

200 OK

### Result

Conversation data is correctly isolated per user account.

Unauthorized users cannot access conversations belonging to other users.

---

## AUTH-PERM-03 — Access other user's documents

### Steps

User A uploaded a document.

User A logged out.

User B logged into the application.

User B accessed the documents list.

### Observed Behavior

User B did not see any documents uploaded by User A.

The documents list remained empty.

### Result

Uploaded documents are correctly isolated per user account.

Unauthorized users cannot view documents belonging to other users.

---

# 5. Issues Found

No issues were identified during permissions testing.

---

# 6. Summary

The authorization and data isolation module passed all test scenarios successfully.

Total executed tests:

3

Passed:

3

Failed:

0

---

# 7. Conclusion

The permissions and authorization system is stable and correctly enforces user-level data isolation.

Validated successfully:

* authentication requirement for protected resources
* prevention of unauthorized access without token
* isolation of conversations between users
* isolation of documents between users
* server-side enforcement of authorization rules

---

# 8. Authentication and Authorization Module Status

The authentication and authorization system has now been validated across five test runs:

* TEST_REPORT_RUN_01 — Registration
* TEST_REPORT_RUN_02 — Login
* TEST_REPORT_RUN_03 — Session / Token Flow
* TEST_REPORT_RUN_04 — Logout Flow
* TEST_REPORT_RUN_05 — Permissions / Data Isolation

Authentication and authorization can be considered functionally complete for the current project stage.
