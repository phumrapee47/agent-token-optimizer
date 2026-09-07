# Empirical Benchmark Results

This benchmark evaluates token reduction techniques on the exact same task, code repository, and language model (`Google Flash`).

## 1. Experimental Setup

* **Target Task**: Read `benchmark.ps1` (313 lines, PowerShell) and explain the architecture and functional purpose of all 7 internal functions.
* **Control Group (Baseline)**: Standard verbose AI coding agent behavior (full-file reads, long conversational recaps, comprehensive step-by-step prose).
* **Treatment Groups**:
  * **Optimized**: Targeted reading (`grep_search` before read, line-sliced `view_file`), surgical output, no preambles/recaps.
  * **Ultra**: Extreme concise bullet points, grep-only context gathering (no full reads), 10-line response cap.
  * **Extreme**: Aggressive grep batching, sub-7-word function summaries, strict char limit.

---

## 2. 4-Way Comparative Metrics

| Metric | Baseline (Verbose) | Optimized | Ultra (Optimal) | Extreme |
| :--- | :--- | :--- | :--- | :--- |
| **Total Bytes** | 44.8 KB | 18.9 KB | **15.9 KB** | 19.1 KB |
| **Est. Tokens** | ~11,477 | ~4,832 | **~4,063** | ~4,885 |
| **Output Bytes** | 19.5 KB | 2.9 KB | **2.6 KB** | 3.8 KB |
| **Thinking Bytes** | 11.0 KB | 937 B | **2.4 KB** | 3.2 KB |
| **Input Bytes** | 14.3 KB | 15.0 KB | **10.9 KB** | 12.0 KB |
| **Tool Calls** | 2 | 4 | **5** | 11 |
| **Token Reduction** | Baseline (0%) | **-57.9%** | **-64.6%** | **-57.4%** |

```
Total Token Footprint:

Baseline    [========================================] ~11,477 tokens
Optimized   [=================                       ] ~4,832 tokens (-57.9%)
Ultra       [==============                          ] ~4,063 tokens (-64.6%)  <-- Optimal Sweet Spot
Extreme     [=================                       ] ~4,885 tokens (-57.4%)
```

---

## 3. Key Findings

1. **Output & Thinking Token Collapse**:
   * Output payload decreased by **86.7%** (from 19.5 KB down to 2.6 KB) by removing conversational filler, polite preambles, and code echoing.
   * Internal reasoning / thinking overhead fell by **78.2%** because concise instruction formats minimize reasoning branch exploration.
2. **The "Extreme" Over-optimization Penalty**:
   * Attempting to over-constrain the agent (`Extreme` mode) caused it to generate **11 individual tool calls** (small fragmented greps) rather than 5 balanced calls.
   * The tool-call metadata overhead increased total input bytes, making `Extreme` (-57.4%) perform worse than `Ultra` (-64.6%).
3. **Quality & Completeness**:
   * All 7 functions (`Get-TranscriptPath`, `Measure-Transcript`, `Format-Bytes`, `Estimate-Tokens`, `Show-Stats`, `Show-Comparison`, `Show-RecentConversations`) were accurately documented in all 3 optimization variants. Zero architectural omissions occurred.
