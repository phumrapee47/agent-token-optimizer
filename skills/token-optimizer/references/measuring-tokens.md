# Measuring Token Usage

## How Antigravity Tokens Work

Every conversation turn consumes tokens:
- **Input tokens**: System prompt + context + skill content + tool results
- **Output tokens**: Agent response + tool calls + thinking

## Measurement Sources

### 1. Conversation Transcripts (Primary)
Antigravity stores full transcripts at:
```
%APPDATA%\.gemini\antigravity\brain\<conversation-id>\.system_generated\logs\
├── transcript.jsonl        ← truncated version (smaller)
└── transcript_full.jsonl   ← complete version
```

Each line is a JSON step with:
- `content` — the text payload (its byte size ≈ token proxy)
- `tool_calls` — array of tool invocations
- `type` — `USER_INPUT`, `PLANNER_RESPONSE`, `TOOL_RESULT`, etc.

### 2. Token Estimation Formula
Since Antigravity doesn't expose raw token counts, we estimate:
```
estimated_tokens ≈ total_bytes / 4  (English)
estimated_tokens ≈ total_bytes / 6  (Code-heavy)
estimated_tokens ≈ total_bytes / 8  (Thai/CJK)
```

## Benchmark Methodology

### A/B Testing Protocol
1. **Baseline run**: Complete a task WITHOUT `token-optimizer` skill active
2. **Optimized run**: Complete the SAME task WITH `token-optimizer` skill active
3. **Compare**:
   - Total estimated tokens (input + output)
   - Number of tool calls
   - Number of conversation turns
   - Task completion success (binary: pass/fail)

### Test Cases
Use consistent, repeatable tasks:

| Test Case | Description | Expected Token Savings |
|-----------|-------------|----------------------|
| `file-edit` | Edit a single function in a known file | 30-50% |
| `multi-file-search` | Find all usages of a symbol across codebase | 40-60% |
| `explain-code` | Explain what a function does | 20-40% |
| `debug-error` | Fix a stack trace error | 25-45% |
| `refactor` | Rename a class across multiple files | 35-55% |

### Quality Checks
Token savings are worthless if quality drops. Verify:
- [ ] Correct code changes (diff matches expected)
- [ ] No missing edge cases
- [ ] Build/tests still pass
- [ ] User would accept the output
