# Agent AI — Test Report Run 14

Project: Agent AI Chatbot  
Module: UI / UX  
Test Scope: Chat UI  
Test Type: Manual End-to-End Testing  
Environment: Local Development  
Date: 2026-04-06  
Tester: Paweł Staniewski

---

# 1. Objective

The purpose of this test run was to validate the stability, usability, and rendering behavior of the chat user interface during normal operation.

The tested scenarios focused on:

- automatic scrolling behavior
- streaming stability
- markdown and code block rendering
- layout stability for long responses

The goal was to confirm that the chat interface remains visually stable and predictable during streaming responses and extended content rendering.

---

# 2. Environment

## Backend

- Django REST Framework
- FastAPI (streaming endpoint)
- Haystack v2 Agent architecture

## Frontend

- React
- Streaming chat interface
- Markdown renderer
- Auto-scroll logic
- Stable message layout

## Database

- PostgreSQL
- pgvector extension

## Streaming

- Server-Sent Events (SSE)
- Incremental response rendering
- Deterministic message completion handling

---

# 3. Test Cases Executed

| Test ID | Test Case           | Result | Notes                                        |
| ------- | ------------------- | ------ | -------------------------------------------- |
| UI-04   | Auto-scroll         | PASS   | Scroll follows streaming messages correctly  |
| UI-05   | No flicker          | PASS   | UI remains stable after streaming completion |
| UI-06   | Markdown rendering  | PASS   | Code blocks and markdown rendered correctly  |
| UI-07   | Long message layout | PASS   | Layout stable for extended responses         |

---

# 4. Detailed Notes

## UI-04 — Auto-scroll

A message was sent to the chat interface to trigger a streamed response.

Observed behavior:

- chat automatically scrolled during streaming
- newest message remained visible
- no manual scrolling required
- scroll behavior remained stable

Additional observation:

Auto-scroll remained locked to the bottom during streaming, preventing temporary manual scrolling until message completion.

Result:

PASS

Recommendation:

Consider implementing conditional auto-scroll logic that temporarily disables auto-scroll when the user scrolls upward.

---

## UI-05 — No flicker

A streamed response was generated and allowed to complete.

Observed behavior:

- message content rendered incrementally
- no visual flicker observed
- layout remained stable
- message container did not shift position

Result:

PASS

---

## UI-06 — Markdown rendering

A message requesting code output was submitted.

Observed behavior:

- code block rendered correctly
- syntax highlighting applied
- indentation preserved
- layout remained stable
- scroll behavior remained functional

Additional elements verified:

- markdown list rendering
- text formatting stability
- consistent message container width

Result:

PASS

---

## UI-07 — Long message layout

A message requesting a detailed technical explanation was submitted.

Observed behavior:

- long message rendered correctly
- text wrapped properly
- message container remained within layout boundaries
- scroll functionality remained stable
- no layout overflow detected

Result:

PASS

---

# 5. Issues Found

No functional issues were detected during Chat UI testing.

---

# 6. Summary

The chat interface demonstrated stable behavior during streaming, message rendering, and extended content display.

All tested scenarios completed successfully without functional failures.

One minor usability improvement opportunity was identified regarding temporary auto-scroll control during streaming responses.

---

## Result

Total executed tests:

4

Passed:

4

Failed:

0

Warnings:

0

---

## Conclusion

The Chat UI module is considered:

STABLE

The system demonstrated:

- reliable auto-scroll behavior
- stable streaming rendering
- correct markdown formatting
- consistent layout integrity
- predictable message display behavior

The chat interface is suitable for production-level usage.

---

# 7. Recommendation

Proceed to the next validation phase focused on:

Navigation behavior.

Next testing scope:

- conversations sidebar
- documents sidebar
- sidebar switching stability

---

Next planned report:

TEST_REPORT_RUN_15 — Navigation Validation
