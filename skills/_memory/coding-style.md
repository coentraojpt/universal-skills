---
usf: false
summary: Prefer clarity over cleverness; explicit names; small functions; no dead code; comments only for non-obvious WHY.
---

# Coding Style

Guidelines referenced by skills via `[[coding-style]]`.

## General
- Clarity beats cleverness. If two equivalent solutions exist, pick the more readable one.
- Names describe intent, not implementation. `retryCount`, not `rc`.
- Small functions (≤30 lines); one reason to change each.
- Delete dead code — don't comment it out.

## Comments
- Default: no comment.
- Write a comment only when the WHY is non-obvious (hidden constraint, workaround, surprising behavior).
- Never restate the code.

## Errors
- Validate at boundaries (user input, external APIs).
- Trust internal invariants — don't defensive-check every call.
- Fail fast with a clear message; don't silently swallow.

## Testing
- One behavior per test.
- Test names describe what, not how: `returns_empty_list_when_no_matches`.
- Avoid mocks at boundaries that matter (real DB in integration tests).
