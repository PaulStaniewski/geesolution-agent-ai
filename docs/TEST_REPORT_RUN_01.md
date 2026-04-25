# Agent AI — Test Report Run 01

**Project:** Agent AI Chatbot  
**Module:** Authentication  
**Test Scope:** Registration Flow  
**Test Type:** Manual End-to-End Testing  
**Environment:** Local Development  
**Date:** 2026-03-30  
**Tester:** Paweł Staniewski

---

## 1. Objective

The purpose of this test run was to validate the registration flow of the authentication module in the Agent AI application.

The tested flow included:

- new user registration
- duplicate email handling
- password validation
- password confirmation validation
- automatic login after successful registration

---

## 2. Environment

### Backend

- Django REST Framework
- SimpleJWT
- Custom user model with email-based authentication

### Frontend

- React
- AuthContext
- Animated login/register auth layout

### Database

- PostgreSQL

### Authentication Model

- email as primary identifier
- password-based login
- JWT access + refresh tokens

---

## 3. Test Cases Executed

| Test ID     | Test Case                     | Result | Notes                                                                                                               |
| ----------- | ----------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------- |
| AUTH-REG-01 | Register new user             | PASS   | New account created successfully                                                                                    |
| AUTH-REG-02 | Register existing email       | PASS   | Frontend displayed: "Email already in use."                                                                         |
| AUTH-REG-03 | Invalid email format          | PASS   | Frontend form validation blocked invalid email input                                                                |
| AUTH-REG-04 | Empty fields                  | PASS   | Required field validation triggered correctly                                                                       |
| AUTH-REG-05 | Password mismatch             | PASS   | Frontend displayed: "Passwords do not match."                                                                       |
| AUTH-REG-06 | Weak password                 | PASS   | Frontend displayed backend validation message: "This password is too short. It must contain at least 8 characters." |
| AUTH-REG-07 | Auto-login after registration | PASS   | User was redirected to the main application immediately after successful registration                               |

---

## 4. Detailed Notes

### AUTH-REG-01 — Register new user

The system created a new account successfully and completed the registration flow without errors.

### AUTH-REG-02 — Register existing email

The system correctly rejected registration when the email address was already in use.  
The frontend displayed a clear message:

> Email already in use.

### AUTH-REG-03 — Invalid email format

The frontend correctly blocked invalid email input using form validation.

### AUTH-REG-04 — Empty fields

The registration form correctly prevented submission when required fields were empty.

### AUTH-REG-05 — Password mismatch

The frontend correctly handled local password confirmation mismatch.  
Displayed message:

> Passwords do not match.

### AUTH-REG-06 — Weak password

The backend password validation worked correctly and returned a validation error for a short password.  
Displayed message:

> This password is too short. It must contain at least 8 characters.

### AUTH-REG-07 — Auto-login after registration

After successful registration, the user was automatically logged in and redirected to the main application view.  
This behavior is consistent with modern SaaS UX patterns.

---

## 5. Issues Found

### BUG-001 — Auth validation messages persisted when switching between login and register panels

**Status:** Fixed during testing  
**Severity:** Low

**Description:**  
Validation messages such as password mismatch or backend error messages remained visible after switching between authentication panels.

**Resolution:**  
Error state reset logic was added during panel switching.

---

## 6. Summary

The registration module passed all tested scenarios.

### Result

- Total executed tests: **7**
- Passed: **7**
- Failed: **0**

### Conclusion

The registration flow is considered stable and production-ready for the current project stage.

Validated successfully:

- user creation
- duplicate email protection
- password validation
- confirm password validation
- auto-login after successful registration
- frontend and backend error messaging

---

## 7. Recommendation

Proceed to the next authentication test run focused on:

- login flow
- invalid credentials
- logout
- token persistence after page refresh
- refresh token behavior
