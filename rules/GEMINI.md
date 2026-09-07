# Token Optimization Directives (for Antigravity / Gemini)

Follow these strict efficiency rules across all responses and actions:

1. **Search Before Reading**: Use `grep_search` to locate exact symbols and line numbers first. Never view entire files blindly.
2. **Slice, Don't Slurp**: When reading files (`view_file`), always specify `StartLine` and `EndLine` (target ~50-100 lines). If search results provide enough context, do not call `view_file`.
3. **Zero-Echo Principle**: Never repeat file contents, test outputs, or terminal logs in responses. Cite as `path:L##-L##`.
4. **Surgical Edits**: Use `replace_file_content` with minimal 3-5 line anchors. Never rewrite entire files. Trust tool execution status; do not re-read files to verify edits unless a build or test fails.
5. **Output Budgeting**: Direct answers only. No conversational pleasantries ("Sure!", "Here is..."), no restating the user's prompt, and no post-action summaries. Use concise bullet points or tables.
6. **Command Output Filtering**: Filter noisy CLI outputs using `head -n 25`, `tail -n 25`, or `grep -E "ERROR|FAIL"`.
7. **Circuit Breaker**: If an edit or command fails twice with similar errors, stop immediately and emit a 1-turn diagnosis. Never loop blindly.
