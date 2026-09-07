# ⚡ Agent Token Optimizer

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Token Reduction](https://img.shields.io/badge/Token_Reduction-64.6%25-brightgreen.svg)](#benchmark-results)
[![Output Reduction](https://img.shields.io/badge/Output_Cut-86.7%25-blue.svg)](#benchmark-results)
[![Platform](https://img.shields.io/badge/Supports-Claude_Code_|_Antigravity_|_Cursor_|_Aider-blueviolet.svg)](#quick-installation)

> **A battle-tested, research-backed token optimization ruleset and benchmark harness for AI Coding Assistants.**  
> Slashes LLM token consumption by **~65%** and output tokens by **~87%** with **zero loss in code quality**.

---

## 🛑 The Problem

Autonomous AI coding agents (Claude Code, Antigravity, Cursor, Aider) suffer from chronic context bloat:
1. **Blind Whole-File Reads**: Slurping 500+ line files into context just to locate a single method.
2. **Conversational Chatter & Echoing**: Re-quoting code, repeating user prompts, and outputting pleasantries.
3. **Doom Loops**: Retrying broken tool commands blindly, burning tens of thousands of tokens per minute.
4. **Fast Rate Limits**: Hitting tier quotas (e.g. Claude Pro 5-hour limits) after only 10–15 messages.

---

## 📊 Benchmark Results

Evaluated across identical tasks, models (`Google Flash`), and files using our PowerShell transcript analyzer:

| Metric | Baseline (Verbose) | Optimized | Ultra (Optimal) | Extreme |
| :--- | :--- | :--- | :--- | :--- |
| **Total Bytes** | 44.8 KB | 18.9 KB | **15.9 KB** | 19.1 KB |
| **Est. Tokens** | ~11,477 | ~4,832 | **~4,063** | ~4,885 |
| **Output Bytes** | 19.5 KB | 2.9 KB | **2.6 KB** | 3.8 KB |
| **Thinking Bytes** | 11.0 KB | 937 B | **2.4 KB** | 3.2 KB |
| **Input Bytes** | 14.3 KB | 15.0 KB | **10.9 KB** | 12.0 KB |
| **Tool Calls** | 2 | 4 | **5** | 11 |
| **Total Token Savings** | Baseline | **-57.9%** | **-64.6%** 🚀 | -57.4% |

```
Token Footprint Comparison:

Baseline   ████████████████████████████████████████  ~11,477 tokens
Optimized  ████████████████▋                          ~4,832 tokens (-57.9%)
Ultra      ██████████████                             ~4,063 tokens (-64.6%)  <-- SWEET SPOT
Extreme    ████████████████▉                          ~4,885 tokens (-57.4%)
```

> **Why Ultra won over Extreme**: Over-constraining the agent caused fragmented tool calls (11 calls vs 5), which increased input metadata overhead. **Ultra represents the empirical sweet spot.**

See full evaluation in [benchmarks/benchmark_results.md](benchmarks/benchmark_results.md).

---

## 🎯 The 7 Core Directives

Our ruleset is formulated as an enforceable contract:

1. **Search Before Reading**: Use `grep` / regex to find symbols and line numbers first. Never `cat` or view entire files blindly.
2. **Slice, Don't Slurp**: When reading files, enforce `StartLine` and `EndLine` slices (~50–100 lines max).
3. **Zero-Echo Principle**: Never repeat inspected file contents or command logs. Cite as `path:L##-L##`.
4. **Surgical Edits**: Use targeted search/replace blocks with 3–5 line anchors. Never rewrite entire files. Trust tool execution status; do not re-read files immediately to verify edits.
5. **Output Budgeting**: Direct answers only. No conversational pleasantries ("Sure!", "Here is..."), no restating prompts, no post-action summaries. Use concise bullet points or tables.
6. **Command Output Filtering**: Pipe shell and test outputs through `head -n 25`, `tail -n 25`, or `grep -E "ERROR|FAIL"`.
7. **Doom Loop Circuit Breaker**: If an edit or command fails twice with similar error traces, abort immediately and emit a 1-turn diagnosis. Never loop blindly.

---

## 🚀 Quick Installation

### For Claude Code CLI (`claude`)

**Option 1: Global (Applies to all projects automatically)**
```powershell
# Windows
Copy-Item rules\CLAUDE.md "$env:USERPROFILE\.claude\CLAUDE.md" -Force
```
```bash
# macOS / Linux
cp rules/CLAUDE.md ~/.claude/CLAUDE.md
```

**Option 2: Per-Project**
Drop `rules/CLAUDE.md` directly into the root directory of your repository.

---

### For Google Antigravity / Gemini

**Option 1: Global Rule**
```powershell
Copy-Item rules\GEMINI.md "$env:USERPROFILE\.gemini\config\GEMINI.md" -Force
```

**Option 2: As a Modular Skill**
Copy the `skills/token-optimizer` directory to:
- Global: `~/.gemini/config/skills/token-optimizer/`
- Workspace: `.agents/skills/token-optimizer/`

---

## 🔬 Benchmark Tool

We include a PowerShell transcript analyzer that inspects JSONL conversation logs and computes byte / token usage:

```powershell
# Analyze a single session
.\benchmarks\benchmark.ps1 -BaselineId "<conversation-id>"

# A/B compare two sessions
.\benchmarks\benchmark.ps1 -BaselineId "<baseline-id>" -OptimizedId "<optimized-id>"

# List recent sessions
.\benchmarks\benchmark.ps1
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
