# ⚡ Agent Token Optimizer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Total Tokens](https://img.shields.io/badge/Total_Tokens-2--8%25_lower_(Claude_Code)-brightgreen.svg)](#-measured-on-claude-code)
[![Output Tokens](https://img.shields.io/badge/Output-10--20%25_lower_(Claude_Code)-blue.svg)](#-measured-on-claude-code)
[![Tested on](https://img.shields.io/badge/Tested_on-Claude_Code_(Sonnet_5)-blueviolet.svg)](#-measured-on-claude-code)

> **A battle-tested, research-backed token optimization ruleset and benchmark harness for AI Coding Assistants.**  
> Measured on Claude Code (Sonnet 5, 7 tasks, 3 reps): output tokens **~10-20% lower**, total tokens **~2-8% lower**. Quality was unchanged on most tasks, but open-ended code review lost items in some runs. See [measured results](#-measured-on-claude-code) and [benchmarks/claude-code/RESULTS.md](benchmarks/claude-code/RESULTS.md).

**Platform status:** Claude Code is measured (see below). Antigravity / Gemini rules are included (`rules/GEMINI.md`) but only have the single-task estimate further down. Cursor and Aider are untested: the rules are plain text and can be adapted, but there are no results for them.

---

## 🛑 The Problem

Autonomous AI coding agents (Claude Code, Antigravity, Cursor, Aider) suffer from chronic context bloat:
1. **Blind Whole-File Reads**: Slurping 500+ line files into context just to locate a single method.
2. **Conversational Chatter & Echoing**: Re-quoting code, repeating user prompts, and outputting pleasantries.
3. **Doom Loops**: Retrying broken tool commands blindly, burning tens of thousands of tokens per minute.
4. **Fast Rate Limits**: Hitting tier quotas (e.g. Claude Pro 5-hour limits) after only 10–15 messages.

---

## 🧪 Measured on Claude Code

Real usage numbers from `claude -p --output-format json` (model `claude-sonnet-5`), automatic grading, deltas vs. *no rules* in the same batch:

| Ruleset | Output tokens | Total tokens | Quality (0-1) |
| :--- | :--- | :--- | :--- |
| *No rules (baseline)* | 0% | 0% | 0.95-0.99 (varies by batch) |
| `rules/CLAUDE.md` | -13% | -5% | 0.92 |
| `skills/token-optimizer/SKILL.md` | -13% | -2% | 0.97 |

Notes: total tokens barely move because the fixed context (system prompt, tools) is re-sent every turn and dominates. Run-to-run noise is about 8-10%, so differences below that are not meaningful. Code-review style tasks can lose findings when output is capped. Method, limitations and comparisons with other public rulesets: [benchmarks/claude-code/RESULTS.md](benchmarks/claude-code/RESULTS.md).

---
## 🎯 The 7 Core Directives

Our ruleset is formulated as an enforceable contract:

1. **Search Before Reading**: Use `grep` / regex to find symbols and line numbers first. Never `cat` or view entire files blindly.
2. **Slice, Don't Slurp**: When reading files, enforce `StartLine` and `EndLine` slices (~50–100 lines max).
3. **Zero-Echo Principle**: Never repeat inspected file contents or command logs. Cite as `path:L##-L##`.
4. **Surgical Edits**: Use targeted search/replace blocks with 3–5 line anchors. Never rewrite entire files. Trust tool execution status; do not re-read files immediately to verify edits.
5. **Output Budgeting**: Max 3 sentences unless detail is requested. Direct answers only. No conversational pleasantries ("Sure!", "Here is..."), no restating prompts, no post-action summaries. Use concise bullet points or tables.
6. **Command Output Filtering**: Pipe shell and test outputs through `head -n 25`, `tail -n 25`, or `grep -E "ERROR|FAIL"`.
7. **Doom Loop Circuit Breaker**: If an edit or command fails twice with similar error traces, abort immediately and emit a 1-turn diagnosis. Never loop blindly.

> `skills/token-optimizer/SKILL.md` expresses the same ruleset slightly differently: directives 1-2 are merged into "Search → Slice → Act", and it adds a "Context Hygiene" directive (delegate broad searches to subagents, keep 2-3 files in focus).

---

## 🚀 Quick Installation

### For Claude Code CLI (`claude`)

> **Back up first.** If you already have a `~/.claude/CLAUDE.md`, the commands below *append* to it instead of overwriting it. Review the result for duplicate or conflicting rules.

**Option 1: Global (applies to all projects)**
```powershell
# Windows: append to your existing global CLAUDE.md (creates it if missing)
Add-Content -Path "$env:USERPROFILE\.claude\CLAUDE.md" -Value (Get-Content rules\CLAUDE.md -Raw)
```
```bash
# macOS / Linux
mkdir -p ~/.claude && cat rules/CLAUDE.md >> ~/.claude/CLAUDE.md
```

**Option 2: Per-project**
Copy `rules/CLAUDE.md` to the root of your repository (or append it to the `CLAUDE.md` already there).

**Option 3: As a skill**
Copy `skills/token-optimizer/` to `~/.claude/skills/token-optimizer/` (global) or `.claude/skills/token-optimizer/` (project). The skill uses the tool names in its "Tool names" note; the measured results above were run with the skill text applied as always-on instructions.

---

### For Google Antigravity / Gemini

**Option 1: Global Rule** (append, so an existing `GEMINI.md` is not lost)
```powershell
Add-Content -Path "$env:USERPROFILE\.gemini\config\GEMINI.md" -Value (Get-Content rules\GEMINI.md -Raw)
```

**Option 2: As a Modular Skill**
Copy the `skills/token-optimizer` directory to:
- Global: `~/.gemini/config/skills/token-optimizer/`
- Workspace: `.agents/skills/token-optimizer/`

---

## 🔬 Benchmark Tools

**Claude Code:** use the harness in [`benchmarks/claude-code/`](benchmarks/claude-code/README.md). It runs each ruleset through headless `claude -p` and reads real token usage.

**Antigravity / Gemini:** `benchmarks/benchmark.ps1` is a PowerShell transcript analyzer for **Antigravity** conversation logs (default `~/.gemini/antigravity/brain`). It does *not* read Claude Code sessions, and it estimates tokens from bytes.

```powershell
# Analyze a single Antigravity session
.enchmarksenchmark.ps1 -BaselineId "<conversation-id>"

# A/B compare two sessions
.enchmarksenchmark.ps1 -BaselineId "<baseline-id>" -OptimizedId "<optimized-id>"

# List recent sessions
.enchmarksenchmark.ps1
```

---

## 📚 Research Foundations

This ruleset synthesizes engineering practices and academic literature:
* **SWE-Pruner** (*arXiv:2601.16746*): Selective tool output pruning prevents syntax degradation while cutting tokens by 23–54%.
* **"Token Reduction Is Not Cost Reduction"** (*arXiv:2607.12161*): Prevents the "repair turn trap" where lossy code summarization causes doom loops.
* **Claude Code Microcompaction**: Offloading raw tool outputs to disk, retaining only compact pointers in conversation memory.
* **Aider Repository Mapping**: AST-derived symbol indexing over full-file context inclusion.
* **LLMLingua-2**: Hierarchical budget allocation across system, task, and context tokens.

---

## 📄 License

Distributed under the MIT License. See [LICENSE](LICENSE) for more details.

Developed with ❤️ by [Phumrapee](https://github.com/phumrapee47)
