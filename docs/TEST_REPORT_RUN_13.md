# Agent AI — Test Report Run 13

Project: Agent AI Chatbot  
Module: UI / UX  
Test Scope: General UI  
Test Type: Manual End-to-End Testing  
Environment: Local Development  
Date: 2026-04-06  
Tester: Paweł Staniewski

---

# 1. Objective

The purpose of this test run was to validate the stability and usability of the application's general user interface.

The tested scenarios focused on:

- initial UI rendering
- loading state visibility
- error message clarity
- transition behavior between authentication states

The goal was to confirm that the application provides predictable and user-friendly feedback during standard authentication workflows.

---

# 2. Environment

## Backend

- Django REST Framework
- FastAPI (streaming endpoint)
- Haystack v2 Agent architecture

## Frontend

- React
- AuthSwitcherLayout component
- AppLoading component
- CSS responsive layout system

## Database

- PostgreSQL
- pgvector extension

## Authentication

- JWT-based authentication
- Login form validation
- Session initialization flow

---

# 3. Test Cases Executed

| Test ID | Test Case      | Result         | Notes                                               |
| ------- | -------------- | -------------- | --------------------------------------------------- |
| UI-01   | Initial load   | PASS           | Login screen renders correctly                      |
| UI-02   | Loading states | PASS           | Dedicated loading screen displayed                  |
| UI-03   | Error messages | PASS (warning) | Loading screen briefly appears before error message |

---

# 4. Detailed Notes

## UI-01 — Initial load

The application was opened from a clean browser session.

Observed behavior:

- login screen rendered correctly
- layout was visually stable
- no visual glitches detected
- no layout shifting observed
- responsive background and glow elements rendered correctly

Result:

PASS

---

## UI-02 — Loading states

Valid login credentials were submitted.

Observed behavior:

- application transitioned immediately to a dedicated loading screen
- loading spinner was clearly visible
- loading message displayed:

Loading workspace...

- transition to main workspace occurred without delay

Result:

PASS

---

## UI-03 — Error messages

Invalid login credentials were submitted.

Observed behavior:

- loading screen briefly appeared
- application returned to login screen
- error message displayed:

Invalid email or password.

The message was clear and understandable.

However, the temporary loading screen before showing the error created a slightly misleading user experience.

Result:

PASS (warning)

---

# 5. Issues Found

## UX-UI-001 — Loading screen shown before authentication failure

Status: Open  
Severity: Low  
Priority: Low

Description:

When invalid login credentials are submitted, the application briefly displays the loading screen before returning to the login screen with an error message.

This behavior may suggest to users that authentication succeeded before failing.

Current Flow:

Click login  
→ Loading screen  
→ Return to login  
→ Error message displayed

Recommended Flow:

Click login  
→ Loading indicator on login screen  
→ If authentication fails:  
 show error message without full loading transition  
→ If authentication succeeds:  
 show loading screen

Risk:

Low

This issue affects user experience clarity rather than system functionality.

---

# 6. Summary

The general UI behavior of the authentication flow is stable and predictable.

All tested scenarios completed successfully.

No functional failures were detected.

One minor UX inconsistency was identified regarding loading transitions during failed authentication attempts.

---

## Result

Total executed tests:

3

Passed:

3

Failed:

0

Warnings:

1

---

## Conclusion

The General UI module is considered:

STABLE WITH MINOR UX IMPROVEMENT OPPORTUNITY

The system demonstrated:

- stable initial rendering
- clear loading feedback
- user-friendly error messaging
- predictable authentication behavior

---

# 7. Recommendation

Proceed to the next validation phase focused on:

Chat UI behavior.

Next testing scope:

- auto-scroll behavior
- streaming stability
- message rendering
- layout integrity for long responses

---

Next planned report:

TEST_REPORT_RUN_14 — Chat UI Validation
