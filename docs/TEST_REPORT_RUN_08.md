# Agent AI — Test Report Run 08

**Project:** Agent AI Chatbot  
**Module:** Streaming  
**Test Scope:** Streaming Stability and Post-Stream Behavior  
**Test Type:** Manual End-to-End Testing  
**Environment:** Local Development (Docker)  
**Date:** 2026-04-05  
**Tester:** Paweł Staniewski

---

# 1. Objective

The purpose of this test run was to validate the stability and correctness of the streaming response mechanism in the chat system.

The tested scenarios included:

- streaming response behavior
- prevention of duplicated output
- persistence of streamed messages after refresh
- system stability when sending consecutive messages

The goal was to ensure that the streaming subsystem behaves reliably under normal usage conditions.

---

# 2. Environment

Backend:

- Django REST Framework
- FastAPI streaming service
- Haystack Agent runtime
- OpenAI Chat Generator
- PostgreSQL database

Frontend:

- React
- Streaming chat interface
- Message rendering system
- State management

Infrastructure:

- Docker Compose
- Django container
- FastAPI container
- PostgreSQL container

Streaming Model:

- Server-Sent Events (SSE)
- incremental token streaming
- persistent message storage
- retrieval-based response generation

---

# 3. Test Cases Executed

| Test ID | Test Case                 | Result | Notes                                                     |
| ------- | ------------------------- | ------ | --------------------------------------------------------- |
| CONV-08 | Streaming response        | PASS   | Response streamed smoothly without interruptions          |
| CONV-09 | No duplicated output      | PASS   | Message appeared once, no duplication detected            |
| CONV-10 | Refresh after stream      | FAIL   | Conversation not restored automatically after page reload |
| CONV-11 | Next message after stream | PASS   | System handled consecutive messages correctly             |

---

# 4. Detailed Test Results

---

## CONV-08 — Streaming response

### Steps

User asked a complex question requiring retrieval and structured response.

### Observed Behavior

The streaming mechanism delivered the response progressively.

No interruptions occurred.

The final message was generated successfully.

### Result

Streaming functionality works correctly.

---

## CONV-09 — No duplicated output

### Steps

User asked a question and waited until the streaming response finished.

### Observed Behavior

The assistant response appeared only once.

No duplicated messages were observed.

The message history remained consistent.

### Result

Duplicate streaming issue is resolved.

---

## CONV-10 — Refresh after stream

### Steps

User sent a message.

Streaming completed successfully.

User refreshed the page.

### Observed Behavior

The final message remained stored in the backend database.

The conversation history was still available.

However, the application returned to the default empty chat view instead of restoring the active conversation automatically.

### Result

Streaming persistence works correctly.

Automatic conversation restoration after refresh is not implemented.

---

## CONV-11 — Next message after stream

### Steps

User sent a new message immediately after streaming finished.

### Observed Behavior

The system accepted the new message.

Streaming started normally.

No errors occurred.

Message order remained correct.

### Result

System supports consecutive messaging after streaming.

---

# 5. Issues Found

---

## Issue 01 — Active conversation is not restored after refresh

Description:

After refreshing the page, the application does not automatically restore the previously active conversation.

Impact:

- user returns to empty chat view
- additional manual interaction required

Severity:

Low

Technical area:

Frontend state restoration / UI behavior

Status:

Known issue

Related tests:

- CONV-03
- CONV-10

---

# 6. Summary

The streaming subsystem performed correctly in all runtime scenarios.

Core streaming functionality is stable.

One known UX limitation was identified.

Total executed tests:

4

Passed:

3

Failed:

1

---

# 7. Conclusion

The streaming system is operational and stable.

Message persistence works correctly.

Duplicate streaming issues have been resolved.

Automatic conversation restoration after refresh remains a known UI improvement area.

---

# 8. Streaming Module Status

The streaming subsystem is considered:

Stable and production-ready.

Known limitation:

Active conversation is not restored automatically after page refresh.
