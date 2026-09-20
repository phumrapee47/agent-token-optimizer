# Measured results on Claude Code

Model `claude-sonnet-5`, headless `claude -p` runs, real token usage from the JSON output, automatic grading. Every number is a delta versus *no rules* **in the same batch**. See [README.md](README.md) to reproduce.

## Tasks (7, sample Python "shop" project)
1. locate a function and its thresholds  2. fix a planted bug without touching tests  3. explain `place_order` on payment failure  4. add tax rules plus tests (hidden test checks it)  5. review a file for bugs  6. run a noisy test suite (~450 log lines, 8 failures) and list failures  7. fix a build that prints 240 warnings before one real error

## This repository's rules

| Ruleset | Output tokens | Total tokens | Quality (0-1) | Notes |
| :--- | :--- | :--- | :--- | :--- |
| `rules/CLAUDE.md` (before fix) | -10% | -5.6% | 0.947 | |
| `rules/CLAUDE.md` (now) | -13% | -5.3% | 0.917 | code-review task scored 0.53 |
| `SKILL.md` (before fix) | -9% | +4.2% | 0.962 | log-heavy tasks +28% total |
| `SKILL.md` (now) | -13% | -2.1% | 0.966 | |

3 reps per task per variant (n=21 per row for 7 tasks).

## Other public rulesets (same method, 5 quiet tasks, 3 reps, n=15)

| Ruleset | Claimed | Output | Total | Quality |
| :--- | :--- | :--- | :--- | :--- |
| Author's earlier personal 7 rules | - | -22% | -8.1% | 0.95 |
| caveman native-core | - | -13% | -5.7% | 0.95 |
| rescue-tokens | 70-90% | -12% | +3.4% | 0.93 |
| caveman (full) | ~65% | -9% | -1.4% | 0.89 |
| caveman (ultra) | ~65% | -7% | +2.3% | 0.93 |
| antigravity 2.0 | 60-80% | +3% | +2.0% | 0.94 |
| ultimate protocol | ~93% | +18% | -5.1% | 0.94 |

Rulesets were applied as always-on system-prompt text, without their proxies, hooks or installers.

## Findings
- Output tokens drop 10-20%. Total tokens drop only 2-8%: the fixed context re-sent every turn dominates, and the rules do not change the number of turns.
- Run-to-run noise is about 8-10% on total tokens (the same variant differed by 8% between batches). Treat smaller differences as noise.
- Capped output can hurt open-ended review tasks (fewer findings listed). Quality drops here are from 3 reps and a keyword grader, so treat them as a signal, not proof.
- Adding five extra rules (batch tool calls, no narration between calls, verify once, exact scope, no directory dumps) on top of a 7-rule baseline did not reduce turns or total tokens (16 runs).
- An output-filtering `PreToolUse` hook compressed tool output by ~50-60% when it fired, but a permission-safe version fired in only a few runs (models append `| tail`, `; echo`, ...), and the naive version can bypass `deny` rules. It is not included here.

## Limitations
Small sample project, one model, 3 reps, keyword-based quality grader, single machine. The earlier single-task Gemini benchmark in the main README used estimated tokens and a hypothetical baseline, and is not comparable.
