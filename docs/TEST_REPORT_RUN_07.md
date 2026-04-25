# Agent AI — Test Report Run 07

**Project:** Agent AI Chatbot  
**Module:** Messaging  
**Test Scope:** Message Handling and Input Validation  
**Test Type:** Manual End-to-End Testing  
**Environment:** Local Development (Docker)  
**Date:** 2026-04-05  
**Tester:** Paweł Staniewski

---

# 1. Objective

The purpose of this test run was to validate core messaging functionality in the chat system.

The tested flow included:

- sending a single message
- sending multiple messages in sequence
- prevention of empty messages
- handling of long input messages
- system stability during streaming responses

The goal was to ensure that the chat messaging system behaves correctly under normal and edge-case usage scenarios.

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
- Chat interface with streaming responses
- Input validation logic
- Message rendering system

Infrastructure:

- Docker Compose
- Django container
- FastAPI container
- PostgreSQL container

Messaging Model:

- conversation-based message storage
- streaming responses via SSE
- retrieval-based response generation
- persistent message history

---

# 3. Test Cases Executed

| Test ID | Test Case              | Result | Notes                                                   |
| ------- | ---------------------- | ------ | ------------------------------------------------------- |
| CONV-04 | Send message           | PASS   | Message sent and response streamed correctly            |
| CONV-05 | Send multiple messages | PASS   | Message order preserved and responses matched correctly |
| CONV-06 | Empty message          | PASS   | Frontend blocked sending empty message                  |
| CONV-07 | Long message           | FAIL   | Response truncated due to completion length limit       |

---

# 4. Detailed Test Results

---

## CONV-04 — Send message

### Steps

User opened an existing conversation.

User entered a standard message.

User clicked the send button.

### Observed Behavior

The message was successfully sent to the backend.

The streaming response mechanism worked correctly.

The assistant generated a valid response.

The message was stored in the conversation history.

### Result

Message sending functionality works correctly.

---

## CONV-05 — Send multiple messages

### Steps

User sent three messages sequentially in the same conversation.

Messages were sent without delay between them.

### Observed Behavior

Each message triggered a separate request.

Responses were generated correctly.

Message order was preserved.

No duplicate responses were observed.

No message corruption occurred.

### Result

Multiple message handling works correctly.

System maintains message integrity and order.

---

## CONV-06 — Empty message

### Steps

User opened a conversation.

User attempted to send a message without entering any text.

### Observed Behavior

The send button remained disabled.

The frontend prevented message submission.

No request was sent to the backend.

No empty message appeared in the conversation.

### Result

Empty message validation works correctly at the frontend level.

---

## CONV-07 — Long message

### Steps

User sent a long technical question requiring a structured explanation about DocumentStore in Haystack.

The message included multiple subtopics:

- architectural role
- interaction with Retriever
- type selection scenarios
- practical comparison

### Observed Behavior

The system accepted the long message successfully.

Document retrieval was triggered correctly.

Relevant documentation was retrieved.

The assistant began generating a structured response.

However, the response was truncated before completion.

Backend logs indicated:

The completion for index 0 has been truncated before reaching a natural stopping point. Increase the max_tokens parameter to allow for longer completions.

The generated answer ended abruptly in the middle of a section.

### Result

Long message handling is partially functional.

Input processing and retrieval work correctly.

Response generation fails to complete due to insufficient completion length configuration.

---

# 5. Issues Found

---

## Issue 01 — Long responses may be truncated

Description:

Long structured responses may be cut off before completion when the assistant generates extended technical explanations.

Impact:

- incomplete answers for complex prompts
- reduced reliability for documentation-based responses
- degraded user experience

Severity:

Medium

Technical area:

LLM generation settings / completion length configuration

Evidence:
The completion for index 0 has been truncated before reaching a natural stopping point.
Increase the max_tokens parameter to allow for longer completions.

Recommended Fix:

Increase the maximum allowed completion length in the chat generator configuration.

---

# 6. Summary

The messaging system performed correctly in standard scenarios.

Core messaging functionality is stable.

One issue was identified in long-response handling.

Total executed tests:

4

Passed:

3

Failed:

1

---

# 7. Conclusion

The messaging module is functionally stable for normal usage.

Long responses require configuration adjustment before production deployment.

Validated successfully:

- message sending
- message ordering
- empty message validation
- streaming stability

Requires improvement:

- completion length configuration for long responses

---

# 8. Messaging Module Status

The messaging system has now been validated across the following scenarios:

- single message handling
- multiple message handling
- empty message prevention
- long message handling

Messaging functionality is nearly production-ready, pending adjustment of completion length configuration.
