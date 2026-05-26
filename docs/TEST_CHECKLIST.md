# Agent AI — Manual Test Checklist

**Project:** Agent AI Chatbot
**Stack:** Django + FastAPI + Haystack + React + PostgreSQL + pgvector
**Test Type:** Manual End-to-End Testing
**Environment:** Local / Development
**Purpose:** Validate production readiness and system stability

---

# 1. Authentication — Manual Test Checklist

## Registration

| ID          | Test Case               | Steps                                  | Expected Result                   | Priority | Status |
| ----------- | ----------------------- | -------------------------------------- | --------------------------------- | -------- | ------ |
| AUTH-REG-01 | Register new user       | Fill registration form with valid data | User account created successfully | High     | ☑      |
| AUTH-REG-02 | Register existing email | Use email already registered           | Error message displayed           | High     | ☑      |
| AUTH-REG-03 | Invalid email format    | Enter invalid email                    | Validation error                  | Medium   | ☑      |
| AUTH-REG-04 | Empty fields            | Submit empty form                      | Form validation triggered         | High     | ☑      |
| AUTH-REG-05 | Password mismatch       | Enter different passwords              | Error message displayed           | High     | ☑      |

---

## Login

| ID          | Test Case             | Steps                     | Expected Result       | Priority | Status |
| ----------- | --------------------- | ------------------------- | --------------------- | -------- | ------ |
| AUTH-LOG-01 | Valid login           | Enter correct credentials | User logged in        | Critical | ☑      |
| AUTH-LOG-02 | Invalid password      | Enter wrong password      | Login error           | Critical | ☑      |
| AUTH-LOG-03 | Non-existing user     | Enter unknown email       | Login error           | High     | ☑      |
| AUTH-LOG-04 | Empty login fields    | Submit empty form         | Validation error      | High     | ☑      |
| AUTH-LOG-05 | Multiple login clicks | Click login repeatedly    | No duplicate requests | Medium   | ☑      |

---

## Session / JWT

| ID          | Test Case                        | Steps                                              | Expected Result                    | Priority | Status |
| ----------- | -------------------------------- | -------------------------------------------------- | ---------------------------------- | -------- | ------ |
| AUTH-SES-01 | Session persistence              | Refresh page after login                           | User remains logged in             | Critical | ☑      |
| AUTH-SES-02 | Direct access to protected route | Open protected page URL                            | Access granted                     | High     | ☑      |
| AUTH-SES-03 | Missing access token             | Remove token manually                              | Refresh token used or logout       | High     | ☑      |
| AUTH-SES-04 | Invalid refresh token            | Modify refresh token                               | User logged out                    | High     | ☑      |
| AUTH-SES-05 | Expired access token             | Wait for expiration                                | Token refreshed automatically      | Critical | ☑      |
| AUTH-SES-06 | Expired refresh token            | Force expiration                                   | Redirect to login                  | Critical | ☑      |
| AUTH-SES-07 | Stream after token expiration    | Wait for access token to expire, then send message | Session recovery behavior verified | Medium   | ☐      |

---

## Logout

| ID          | Test Case                 | Steps             | Expected Result         | Priority | Status |
| ----------- | ------------------------- | ----------------- | ----------------------- | -------- | ------ |
| AUTH-OUT-01 | Logout                    | Click logout      | User logged out         | Critical | ☑      |
| AUTH-OUT-02 | Refresh after logout      | Refresh page      | User remains logged out | High     | ☑      |
| AUTH-OUT-03 | Browser back after logout | Click back button | Access denied           | Medium   | ☑      |

---

## Permissions

| ID           | Test Case                         | Steps                    | Expected Result | Priority | Status |
| ------------ | --------------------------------- | ------------------------ | --------------- | -------- | ------ |
| AUTH-PERM-01 | Access without token              | Open protected page      | Access denied   | Critical | ☑      |
| AUTH-PERM-02 | Access other user's conversations | Use different user       | Access denied   | Critical | ☑      |
| AUTH-PERM-03 | Access other user's documents     | Try to view foreign data | Access denied   | Critical | ☑      |

---

# 2. Conversation Flow — Manual Test Checklist

## Conversations

| ID      | Test Case               | Steps                 | Expected Result            | Priority | Status   |
| ------- | ----------------------- | --------------------- | -------------------------- | -------- | -------- |
| CONV-01 | Create new conversation | Click new chat        | Conversation created       | Critical | ☑        |
| CONV-02 | Switch conversations    | Select different chat | Correct messages displayed | Critical | ☑        |
| CONV-03 | Refresh conversation    | Refresh page          | Messages persist           | High     | ☐ FAILED |

### Notes

CONV-03 was executed and failed.

After page refresh, the application returned to the default empty chat view instead of restoring the previously active conversation.

See:

- TEST_REPORT_RUN_06.md

---

## Messaging

| ID      | Test Case              | Steps                   | Expected Result          | Priority | Status  |
| ------- | ---------------------- | ----------------------- | ------------------------ | -------- | ------- |
| CONV-04 | Send message           | Enter message           | Message appears          | Critical | ☑       |
| CONV-05 | Send multiple messages | Send several prompts    | Order preserved          | Critical | ☑       |
| CONV-06 | Empty message          | Click send without text | No message created       | High     | ☑       |
| CONV-07 | Long message           | Send long text          | System handles correctly | Medium   | ☑ FIXED |

### Notes

CONV-07 initially failed due to response truncation caused by insufficient `max_tokens`.

The issue was resolved by increasing the token limit from:

```python
max_tokens = 700

to:

max_tokens = 1500
```

See:

- TEST_REPORT_RUN_07.md
- TEST_REPORT_RUN_07_FIXED.md

---

## Streaming

| ID      | Test Case                 | Steps                | Expected Result           | Priority | Status   |
| ------- | ------------------------- | -------------------- | ------------------------- | -------- | -------- |
| CONV-08 | Streaming response        | Ask complex question | Response streams smoothly | Critical | ☑        |
| CONV-09 | No duplicated output      | Wait for completion  | Message appears once      | Critical | ☑        |
| CONV-10 | Refresh after stream      | Reload page          | Final message stored      | High     | ☐ FAILED |
| CONV-11 | Next message after stream | Send another prompt  | Works normally            | High     | ☑        |

### Notes

CONV-10 was executed and failed.

After page refresh, the final streamed message remained stored in the backend and could be loaded again after manually selecting the conversation.

However, the application did not automatically restore the active conversation after reload and returned to the default empty chat view.

This behavior is consistent with the previously identified issue in:

- CONV-03 — Refresh conversation

See:

- TEST_REPORT_RUN_06.md

## Message History

| ID      | Test Case              | Steps                 | Expected Result   | Priority | Status |
| ------- | ---------------------- | --------------------- | ----------------- | -------- | ------ |
| CONV-12 | Load history           | Reopen conversation   | History visible   | Critical | ☑      |
| CONV-13 | Conversation isolation | Compare conversations | No message mixing | Critical | ☑      |

### Notes

CONV-12 passed when the user manually reopened the conversation.

History loads correctly after selecting the conversation from the sidebar.

Automatic restoration of the active conversation after page refresh is still not implemented and remains covered by:

- CONV-03
- CONV-10

---

# 3. Retrieval / RAG — Manual Test Checklist

| ID     | Test Case                     | Steps                              | Expected Result                      | Priority | Status   |
| ------ | ----------------------------- | ---------------------------------- | ------------------------------------ | -------- | -------- |
| RAG-01 | Query existing documentation  | Ask known topic                    | Relevant answer returned             | Critical | ☑        |
| RAG-02 | Query missing topic           | Ask unknown topic                  | Safe response (no hallucination)     | Critical | ☑        |
| RAG-03 | Reference query               | Ask by component/class name        | Correct document retrieved           | Critical | ☑warning |
| RAG-04 | Conceptual query              | Ask conceptual question            | Context-based explanation            | High     | ☑warning |
| RAG-05 | Comparison query              | Ask to compare two concepts        | Logical comparison generated         | High     | ☑fail    |
| RAG-06 | Practical how-to query        | Ask how to use component           | Actionable answer with example       | High     | ☑        |
| RAG-07 | Retrieval ranking quality     | Observe top docs ranking           | Most relevant document near top      | High     | ☑fail    |
| RAG-08 | Retrieval latency             | Measure retrieval time             | Response within acceptable range     | High     | ☑        |
| RAG-09 | Retrieval caching             | Repeat similar query               | Cached result returned               | High     | ☑        |
| RAG-10 | Source correctness            | Verify cited sources               | Sources match documentation          | Critical | ☑        |
| RAG-11 | Polish query for English docs | Ask in Polish                      | Retrieval still works                | High     | ☑warning |
| RAG-12 | Paraphrased query             | Rephrase same question             | Same result returned                 | High     | ☑fail    |
| RAG-13 | Ambiguous query               | Ask unclear question               | Safe clarification or general answer | Medium   | ☑warning |
| RAG-14 | Multiple repeated queries     | Ask similar queries multiple times | Stable behavior                      | Medium   | ☑warning |
| RAG-15 | Retrieval robustness          | Ask slightly incorrect term        | System still finds relevant doc      | Medium   | ☑fail    |
| RAG-16 | Cold start behavior           | First query after restart          | System responds correctly            | Medium   | ☑warning |
| RAG-17 | Long response stability       | Ask complex question               | No streaming issues                  | Medium   | ☑        |
| RAG-18 | Retrieval fallback behavior   | Weak retrieval result              | Safe answer generated                | Critical | ☑        |

---

# 4. Quiz System — Manual Test Checklist

## Quiz Generation

| ID      | Test Case             | Steps                | Expected Result | Priority | Status |
| ------- | --------------------- | -------------------- | --------------- | -------- | ------ |
| QUIZ-01 | Generate quiz         | Request quiz         | Quiz generated  | Critical | ☑      |
| QUIZ-02 | Missing document quiz | Request invalid quiz | Safe response   | High     | ☑      |
| QUIZ-03 | Quiz structure        | Inspect quiz         | Valid format    | Critical | ☑      |

---

## Quiz Evaluation

| ID      | Test Case               | Steps               | Expected Result     | Priority | Status |
| ------- | ----------------------- | ------------------- | ------------------- | -------- | ------ |
| QUIZ-04 | Evaluate correct format | Submit answers      | Correct evaluation  | Critical | ☑      |
| QUIZ-05 | Evaluate invalid format | Submit wrong format | Error handled       | High     | ☑      |
| QUIZ-06 | Quiz consistency        | Evaluate quiz       | Same quiz evaluated | Critical | ☑      |
| QUIZ-07 | Multiple quizzes        | Generate new quiz   | No state mixing     | High     | ☑      |

---

# 5. UI / UX — Manual Test Checklist

## General UI

| ID    | Test Case      | Steps            | Expected Result         | Priority | Status |
| ----- | -------------- | ---------------- | ----------------------- | -------- | ------ |
| UI-01 | Initial load   | Open application | No visual glitches      | Critical | ☑      |
| UI-02 | Loading states | Trigger loading  | Clear loading indicator | High     | ☑      |
| UI-03 | Error messages | Trigger error    | User-friendly message   | High     | ☑      |

---

## Chat UI

| ID    | Test Case           | Steps               | Expected Result     | Priority | Status |
| ----- | ------------------- | ------------------- | ------------------- | -------- | ------ |
| UI-04 | Auto-scroll         | Send messages       | Scroll follows chat | Critical | ☑      |
| UI-05 | No flicker          | Finish streaming    | Stable UI           | Critical | ☑      |
| UI-06 | Markdown rendering  | Generate code block | Proper formatting   | High     | ☑      |
| UI-07 | Long message layout | Send long response  | Layout intact       | High     | ☑      |

---

## Navigation

| ID    | Test Case             | Steps           | Expected Result        | Priority | Status |
| ----- | --------------------- | --------------- | ---------------------- | -------- | ------ |
| UI-08 | Conversations sidebar | Open sidebar    | Correct list displayed | Critical | ☐      |
| UI-09 | Documents sidebar     | Open documents  | Files displayed        | High     | ☐      |
| UI-10 | Sidebar switching     | Toggle sidebars | Layout stable          | High     | ☐      |

---

## Responsiveness

| ID    | Test Case        | Steps         | Expected Result | Priority | Status |
| ----- | ---------------- | ------------- | --------------- | -------- | ------ |
| UI-11 | Desktop layout   | Resize window | Layout stable   | Critical | ☐      |
| UI-12 | Mobile layout    | Open on phone | Responsive UI   | Critical | ☐      |
| UI-13 | Refresh behavior | Reload page   | State restored  | High     | ☐      |

---

## Error Handling

| ID    | Test Case         | Steps            | Expected Result     | Priority | Status |
| ----- | ----------------- | ---------------- | ------------------- | -------- | ------ |
| UI-14 | Backend offline   | Stop backend     | Error message shown | High     | ☐      |
| UI-15 | Streaming failure | Interrupt stream | Recovery possible   | High     | ☐      |

---

# Usage

Change status during testing:

```

☐ → ☑

```

Example:

```

| AUTH-LOG-01 | Valid login | ... | ... | Critical | ☑ |

```

```

```
