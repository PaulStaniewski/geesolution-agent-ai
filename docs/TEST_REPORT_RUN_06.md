# Agent AI — Test Report Run 06

**Project:** Agent AI Chatbot  
**Module:** Conversation Flow  
**Test Scope:** Conversations  
**Test Type:** Manual End-to-End Testing  
**Environment:** Local Development (Docker)  
**Date:** 2026-04-05  
**Tester:** Paweł Staniewski  

---

# 1. Objective

The purpose of this test run was to validate the basic conversation management functionality in the chatbot application.

The tested flow included:

- creation of new conversations
- switching between multiple conversations
- persistence of conversation state after page refresh
- verification of correct conversation isolation in the user interface
- validation of backend API behavior during conversation operations

---

# 2. Environment

Backend:

- Django REST Framework  
- PostgreSQL database  
- REST API endpoints for conversations and messages  

Frontend:

- React  
- Sidebar conversation navigation  
- Axios API integration  
- State management for active conversation  

Infrastructure:

- Docker Compose  
- Django container  
- FastAPI streaming container  
- PostgreSQL container  

Conversation Model:

- user-scoped conversations  
- persistent message storage  
- conversation-based message retrieval  

---

# 3. Test Cases Executed

| Test ID | Test Case               | Result | Notes                                                      |
|--------|-------------------------|-------|-----------------------------------------------------------|
| CONV-01 | Create new conversation | PASS  | Conversation created successfully via POST request        |
| CONV-02 | Switch conversations    | PASS  | Messages loaded correctly per conversation_id             |
| CONV-03 | Refresh conversation    | FAIL  | Active conversation state not restored after page refresh |

---

# 4. Detailed Test Results

## CONV-01 — Create new conversation

### Steps

User logged into the application.

User clicked the **New Conversation** button.

User entered a conversation name and confirmed creation.

### Observed Behavior

Frontend sent:

POST /api/v1/conversations/

Backend returned:

201 Created

Conversation list was refreshed automatically via:

GET /api/v1/conversations/

New conversation appeared in the sidebar and became the active conversation.

No errors were observed in browser console or backend logs.

### Result

Conversation creation functionality works correctly.

---

## CONV-02 — Switch conversations

### Steps

User created two separate conversations.

User opened the first conversation and sent a message.

User switched to a second conversation and sent another message.

User returned to the first conversation.

### Observed Behavior

Each conversation triggered the correct request:

GET /api/v1/messages/?conversation_id=<id>

Messages were loaded separately for each conversation.

Streaming responses were associated with the correct conversation_id.

No message mixing occurred between conversations.

### Result

Conversation switching functionality works correctly and maintains message isolation.

---

## CONV-03 — Refresh conversation

### Steps

User opened an existing conversation containing messages.

User refreshed the browser page.

### Observed Behavior

After page refresh, the application returned to the default empty chat view.

The previously opened conversation was not restored automatically.

Message data remained stored in the backend.

No backend error occurred.

Frontend state for the active conversation was lost.

### Result

Conversation refresh behavior is not fully correct.

Message persistence exists in the backend, but the frontend does not restore the previously active conversation after reload.

---

# 5. Issues Found

## Issue 01 — Active conversation not restored after refresh

Description:

The application does not persist the selected conversation state after a browser refresh.

Impact:

- user returns to an empty chat view
- additional manual interaction required to reopen conversation
- reduced user experience consistency

Severity:

Medium

Technical area:

Frontend state persistence / session restoration

Recommended Fix:

Persist the active conversation ID using:

- localStorage  
or  
- sessionStorage  
or  
- URL state  

and restore the conversation automatically on application bootstrap.

---

# 6. Summary

The conversation management module was tested across three core scenarios.

Total executed tests:

3  

Passed:

2  

Failed:

1  

---

# 7. Conclusion

The conversation flow is mostly stable and functional.

Validated successfully:

- conversation creation via API  
- conversation switching behavior  
- correct message isolation between conversations  
- stable backend conversation handling  

Requires improvement:

- restoration of active conversation after page refresh  

The identified issue is related to frontend state persistence and does not affect backend data integrity.

---

# 8. Conversation Module Status

The conversation module has now been validated across six test runs:

- TEST_REPORT_RUN_01 — Registration  
- TEST_REPORT_RUN_02 — Login  
- TEST_REPORT_RUN_03 — Session / Token Flow  
- TEST_REPORT_RUN_04 — Logout Flow  
- TEST_REPORT_RUN_05 — Permissions / Data Isolation  
- TEST_REPORT_RUN_06 — Conversation Flow  

Conversation management can be considered functionally stable, with one identified usability improvement pending before deployment.