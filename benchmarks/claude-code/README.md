# Claude Code benchmark harness

Reproduces the numbers in [RESULTS.md](RESULTS.md). Requires the `claude` CLI (logged in) and Python 3.

```bash
python setup.py          # builds ./base (sample project with a planted bug) and ./variants/*.txt
python setup_noisy.py    # builds ./base_noisy (adds a noisy test suite and a noisy build script)

# variants/<name>.txt is appended to the system prompt; an empty file is the "no rules" baseline.
# Put your own ruleset in variants/ (e.g. copy rules/CLAUDE.md to variants/mine.txt).
TK_BASE=base_noisy python run_exp.py 3 A_baseline,mine results.jsonl
#                                   ^reps  ^variants (comma separated)  ^output
# Optional: TK_TASKS=T2_bugfix,T3_explain limits the task set.
```

Each run happens in a fresh copy of the project, with CLAUDE.md, skills and MCP servers disabled so only the variant differs (`CLAUDE_CODE_DISABLE_CLAUDE_MDS=1`, `--strict-mcp-config`, `--disable-slash-commands`). Runs whose result says "session limit" or has no output tokens are recorded as errors, not data.

Windows: run directories are created under `%TEMP%\tkexp` because long paths (>260 chars) break process launch.
