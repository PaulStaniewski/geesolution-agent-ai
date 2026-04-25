# Agent AI — Test Report Run 12

**Project:** Agent AI Chatbot  
**Module:** Quiz System  
**Test Scope:** Quiz Evaluation  
**Test Type:** Manual End-to-End Testing  
**Environment:** Local Development  
**Date:** 2026-04-06  
**Tester:** Paweł Staniewski

---

# 1. Objective

The purpose of this test run was to validate the quiz evaluation functionality of the Agent AI application.

The tested flow included:

- parsing user answers to a generated quiz
- evaluating answers against the correct answer key
- handling invalid answer formats safely
- ensuring deterministic evaluation behavior
- verifying state consistency across multiple quizzes

The goal was to confirm that the system reliably evaluates quiz responses and maintains stable behavior under repeated and multi-quiz scenarios.

---

# 2. Environment

## Backend

- Django REST Framework
- FastAPI (streaming endpoint)
- Haystack v2 Agent architecture
- Custom quiz evaluation tool (`quiz_evaluator`)
- Stateful conversation session handling

## Frontend

- React
- Streaming chat interface
- Markdown rendering
- Stable message layout
- Auto-scroll behavior

## Database

- PostgreSQL
- pgvector extension

## State Management

- conversation-bound quiz state (`last_quiz`)
- deterministic evaluation pipeline
- session persistence across multiple messages

---

# 3. Test Cases Executed

| Test ID | Test Case               | Result | Notes                                                   |
| ------- | ----------------------- | ------ | ------------------------------------------------------- |
| QUIZ-04 | Evaluate correct format | PASS   | Answers parsed and evaluated correctly                  |
| QUIZ-05 | Evaluate invalid format | FAIL   | System accepted ambiguous input instead of rejecting it |
| QUIZ-06 | Quiz consistency        | PASS   | Same answers produced identical results                 |
| QUIZ-07 | Multiple quizzes        | PASS   | Evaluation correctly used most recent quiz              |

---

# 4. Detailed Notes

## QUIZ-04 — Evaluate correct format

The system successfully evaluated a properly formatted quiz response.

Observed behavior:

- intent correctly classified as `quiz_answer`
- quiz evaluation route executed
- last quiz state retrieved successfully
- answer parsing completed correctly
- evaluation result generated without retrieval

Output contained:

- per-question evaluation table
- correct answer comparison
- final score calculation
- structured feedback

The system behaved as expected.

---

## QUIZ-05 — Evaluate invalid format

The system received an ambiguous natural-language answer:

moja odpowiedz to chyba b ale nie jestem pewien

Observed behavior:

- input was not recognized as a structured quiz answer
- system routed the request to normal chat logic
- assistant attempted to interpret the answer instead of rejecting it

Expected behavior:

The system should have returned a validation message requesting a correct answer format.

Example expected response:

Podaj odpowiedzi w formacie: 1b, 2c, 3a...

Impact:

Low functional risk, but inconsistent validation behavior.

Severity:

Low

Status:

Open issue

---

## QUIZ-06 — Quiz consistency

The same answer set was submitted twice to the same quiz.

Observed behavior:

- identical evaluation results returned
- identical answer key used
- no regeneration of quiz
- state remained stable

Result:

Deterministic evaluation behavior confirmed.

---

## QUIZ-07 — Multiple quizzes

Two quizzes were generated sequentially within the same conversation.

Observed behavior:

- second quiz contained a different set of questions
- evaluation referenced the second quiz
- previous quiz state was correctly replaced
- no state mixing occurred

Result:

Multi-quiz state management verified.

---

# 5. Issues Found

## BUG-QUIZ-001 — Invalid answer format not strictly validated

**Status:** Open  
**Severity:** Low

### Description

The system does not enforce strict answer formatting when a quiz is active.

Ambiguous input is interpreted conversationally rather than rejected with a validation message.

### Example

User input:

moja odpowiedz to chyba b ale nie jestem pewien

System response:

The assistant attempted to interpret the answer instead of requesting a valid format.

### Expected behavior

The system should enforce a structured answer format when a quiz is active.

Example validation message:

Nie rozpoznano poprawnego formatu odpowiedzi.
Podaj odpowiedzi w formacie: 1b, 2c, 3a...

### Risk

Low

This issue affects UX consistency rather than system stability.

---

## Observation — Answer key consistency

Some generated quizzes contained answer keys that appear inconsistent with documentation semantics.

Examples observed:

- unexpected correct answer mappings
- alternative parameters marked as incorrect

This behavior suggests potential inconsistencies in quiz generation logic or answer key extraction.

Severity:

Low

Status:

Review recommended

---

# 6. Summary

The quiz evaluation subsystem passed the majority of tested scenarios.

---

## Result

Total executed tests:

4

Passed:

3

Failed:

1

Warnings:

0

---

## Conclusion

The quiz evaluation module is considered:

**STABLE WITH MINOR VALIDATION LIMITATIONS**

The system demonstrated:

- reliable answer parsing
- deterministic evaluation behavior
- stable session state management
- correct handling of multiple quizzes
- predictable evaluation output

The only identified issue relates to strict validation of invalid answer formats.

---

# 7. Recommendation

Proceed to the next validation phase focused on:

UI / UX stability testing.

Next testing scope:

- loading states
- streaming stability
- auto-scroll behavior
- layout consistency
- sidebar interaction
- error handling scenarios
- responsiveness validation

---

**Next planned report:**

TEST_REPORT_RUN_13 — UI / UX Validation
