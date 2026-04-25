# TEST REPORT — RUN 09

**Project:** Agent AI Chatbot
**Module:** Conversation Flow / Streaming / Message History
**Test Type:** Manual End-to-End Testing
**Environment:** Local / Development
**Date:** 2026-04-04
**Tester:** Pawel Staniewski

---

# Objective

Validate stability of conversation handling, streaming responses, message persistence, and conversation isolation behavior after recent system fixes.

The goal of this test run was to confirm that:

* streaming responses are delivered correctly
* no duplicated messages are generated
* messages are properly stored in the database
* conversations remain isolated
* message history loads correctly when reopening conversations
* system behavior remains stable after multiple interactions

---

# Environment

Backend:

* Django REST API
* FastAPI streaming endpoint
* Haystack Agent architecture
* PostgreSQL with pgvector

Frontend:

* React + Vite
* SSE streaming via EventSource
* Sidebar-based conversation navigation

Infrastructure:

* Docker Compose (local development)
* JWT authentication (access + refresh tokens)

---

# Test Scenarios

---

## CONV-08 — Streaming response

**Steps**

1. Send a complex question to the chatbot
2. Observe streaming behavior

**Expected Result**

Response streams smoothly without interruptions.

**Result**

PASS

Streaming response was delivered correctly and progressively in the UI.

---

## CONV-09 — No duplicated output

**Steps**

1. Send a message
2. Wait for streaming completion
3. Observe message list
4. Verify database entries in Django Admin

**Expected Result**

Only one message is created and displayed.

**Result**

PASS

No duplicated messages were detected in the UI or database.
Retriever guard and streaming logic behaved correctly.

---

## CONV-10 — Refresh after stream

**Steps**

1. Send a message
2. Wait for streaming to finish
3. Refresh the page (F5)

**Expected Result**

Final message remains stored.

**Result**

PASS

Message persisted correctly in the database after refresh.
Conversation data remained intact.

Note:

The active conversation was not automatically restored after refresh.
Manual selection from the sidebar correctly loaded the message history.

---

## CONV-11 — Next message after stream

**Steps**

1. Send a message
2. Wait for streaming to finish
3. Send another message

**Expected Result**

System continues normal operation.

**Result**

PASS

Subsequent messages were processed correctly.
No errors or state corruption occurred.

---

## CONV-12 — Load history

**Steps**

1. Send multiple messages
2. Switch to another conversation
3. Return to the original conversation

**Expected Result**

Conversation history is visible.

**Result**

PASS

Message history loaded correctly after selecting the conversation.

---

## CONV-13 — Conversation isolation

**Steps**

1. Create two separate conversations
2. Send different messages to each
3. Switch between conversations

**Expected Result**

Messages remain isolated per conversation.

**Result**

PASS

No message mixing was observed.
Conversation isolation logic functioned correctly.

---

# Known Issues

---

## CONV-03 — Refresh conversation

Status:

FAILED

Description:

After page refresh, the application returns to the default empty chat view instead of restoring the previously active conversation automatically.

Impact:

Low

Reason:

Conversation data is preserved and accessible.
This issue affects user experience but does not affect data integrity.

---

# Stability Assessment

Conversation system behavior is stable.

Verified capabilities:

* streaming response handling
* message persistence
* conversation switching
* message history loading
* conversation isolation
* database consistency
* retry-safe streaming logic

System reliability is considered:

STABLE

---

# Conclusion

Conversation handling and streaming functionality operate correctly under normal usage conditions.

All critical conversation flow scenarios passed successfully.

The system demonstrates consistent behavior across:

* streaming interactions
* conversation switching
* message persistence
* history retrieval

One known usability issue remains:

automatic restoration of the active conversation after page refresh.

This issue does not impact system correctness or data safety.

The conversation subsystem is considered production-ready.

---
