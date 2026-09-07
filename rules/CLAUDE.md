# Token Optimization Rules (for Claude Code CLI)

## Core Directives

1. **Search Before Reading**: Use grep/rg to locate exact symbols and line numbers first. Never read full files blindly with cat.
2. **Slice, Don't Slurp**: Read only targeted line ranges with head/tail/sed. Target 50-100 lines max.
3. **Zero-Echo Principle**: Never repeat file contents, test outputs, or terminal logs in responses. Cite as `path:L##-L##`.
4. **Surgical Edits**: Use search/replace blocks with 3-5 line anchors. Never rewrite entire files. Trust tool execution status — do not re-read to verify.
5. **Output Budgeting**: Direct answers only. No conversational pleasantries ("Sure!", "Here is..."), no restating the user's prompt, no post-action summaries. Use concise bullet points.
6. **Command Output Filtering**: Pipe large outputs: `| head -n 25`, `| grep -E "ERROR|FAIL"`. Never dump raw logs into context.
7. **Circuit Breaker**: If an edit or command fails twice with similar errors, stop immediately and diagnose in 1 message.
