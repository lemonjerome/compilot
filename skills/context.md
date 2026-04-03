# Context Efficiency Skill

## Purpose

Guide the agent to use the context window efficiently so it does not exhaust capacity before writing output files.

---

## Exploration Rules

- Start with `list_directory` to orient. Only call `read_file` on files you actually need.
- Use `search_files` with a `content_query` to locate specific patterns before reading whole files.
- Do NOT re-read a file whose content is already visible earlier in this conversation — the content is already in context.
- Each tool call consumes context space that you will need for file content. Minimize unnecessary reads.

---

## Writing Files

- Call `create_file` exactly ONCE per stage with the COMPLETE file content.
- Never call `create_file` with partial content — there is no append tool.
- If you realize the file needs changes after writing, call `create_file` again with the full corrected content.
- Every coding stage writes exactly ONE primary file: html_code → index.html, js_code → script.js, css_code → styles.css.

---

## Reasoning

- Think in plain text. Do not output JSON envelopes, XML wrappers, or `type=reason` prefixes.
- Keep reasoning concise. Long reasoning blocks consume context that you will need for file content.
- When you have finished writing a file, your stage is done — produce a short confirmation in plain text (no tool calls).

---

## Tool Efficiency

- Prefer `search_files(pattern="*.js", content_query="function")` over reading every JS file manually.
- If a file path is already known from `list_directory`, skip the search and read it directly.
- Tool outputs from earlier turns are already in context — you do not need to call the same tool again.
