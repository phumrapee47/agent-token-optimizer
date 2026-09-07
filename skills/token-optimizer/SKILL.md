---
name: token-optimizer
description: >-
  Use this skill to optimize token consumption while maintaining output quality.
  Activate when the agent should minimize token usage for cost efficiency,
  such as during large refactors, research tasks, or repetitive workflows.
---

# Token Optimizer

## Core Rules (Always Apply)

### 1. Search → Slice → Act (Never Read Blind)
- `grep_search` to find symbols/line numbers FIRST
- `view_file` with `StartLine`/`EndLine` (max 100 lines). NEVER read full files
- If grep output shows enough context, skip `view_file` entirely

### 2. Zero-Echo Principle
- NEVER re-quote file contents, tool outputs, or test results
- Cite as `path:L##-L##` instead of quoting
- No preambles ("Sure!", "Here's what I did", "Let me explain")
- No post-action recaps or summaries

### 3. Surgical Edits Only
- `replace_file_content` with 3-5 line anchors. NEVER full-file rewrites
- Trust tool success status. Do NOT re-read files to verify edits
- Batch independent tool calls in ONE turn

### 4. Output Budgeting
- Max 3 sentences explanation unless user asks for detail
- Bullet points over paragraphs. Tables over lists
- One-line-per-item format: `FuncName (L##): description`

### 5. Input Filtering
- Pipe large commands: `| head -n 25`, `| grep -E "ERROR|FAIL"`
- Use `Includes` globs on grep to skip node_modules, build dirs, minified files
- For JSON/CSV >20KB: use `jq`/`grep` CLI, don't read into context

### 6. Context Hygiene
- Delegate broad searches to subagents; receive only summaries
- Keep max 2-3 files in active focus
- Once file edit verified, drop it from consideration
- No re-reading files you already inspected this turn

### 7. Doom Loop Breaker
- If same error appears twice after fix attempts: STOP, diagnose in 1 turn
- Never retry blindly — emit structured diagnosis instead

## When NOT to Optimize
- User asks for detailed explanation
- Debugging complex multi-file issues (context matters)
- First interaction on new codebase

## Verification
See [benchmark script](./scripts/benchmark.ps1) and [measurement guide](./references/measuring-tokens.md).
