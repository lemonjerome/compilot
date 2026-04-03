# Test Skill Guide

## Purpose

Write plain Node.js unit tests that verify the JavaScript logic in `script.js`.
The goal is real test coverage — not trivially passing assertions.

---

## Rules

### File naming
- Always name the test file `tests.js`.
- Place it at the workspace root (same level as `script.js`).

### Test format
- Use Node.js built-in `assert` module only. No Mocha, Jest, or test frameworks.
- Each test is a direct `assert.*` call at the top level of the file.
- End with `console.log('All tests passed');` so the runner can confirm success.

### What to test
- **Pure logic functions**: formatters, validators, calculators, state transitions.
- **Data helpers**: anything that transforms or reduces plain data.
- **Edge cases**: empty input, zero values, boundary conditions.

### What NOT to test
- DOM manipulation (`document`, `querySelector`, etc.) — Node.js has no DOM.
- `localStorage`, `window`, `fetch`, `setTimeout` — browser APIs only.
- Event listeners — these require a running browser context.

---

## Extracting logic from script.js

If the functions you want to test are not exported, copy the relevant function bodies
into the test file directly. Keep them in sync with `script.js`.

```js
// Inline the pure function from script.js
function formatTime(seconds) {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}
```

---

## Test file template

```js
'use strict';
const assert = require('assert');

// --- Copy pure functions here if not exported ---

function add(a, b) { return a + b; }  // example

// --- Tests ---

// Test 1: basic addition
assert.strictEqual(add(1, 2), 3, 'add(1, 2) should equal 3');

// Test 2: edge case
assert.strictEqual(add(0, 0), 0, 'add(0, 0) should equal 0');

console.log('All tests passed');
```

---

## Fixing failures

When `run_unit_tests` returns a non-zero exit code:

1. Read the `stderr` output — Node.js prints the failing assertion and line number.
2. Identify whether the **test expectation** is wrong or the **application logic** is wrong.
3. Fix the right thing:
   - If the test expected the wrong value → update the assertion in `tests.js`.
   - If the logic returned the wrong value → fix the function in `script.js` AND `tests.js` (keep the copy in sync).
4. Rewrite the corrected file with `create_file`, then call `run_unit_tests` again.

Do NOT set expected values to match whatever the buggy function returns — fix the logic.

---

## Using search_files

Before writing tests, you may use `search_files` to confirm file locations:

```json
{ "pattern": "*.js" }
```

Or to find a specific function name in the workspace:

```json
{ "pattern": "*.js", "content_query": "function formatTime" }
```
