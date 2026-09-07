<#
.SYNOPSIS
    Benchmark token usage across Antigravity conversation transcripts.

.DESCRIPTION
    Analyzes conversation transcript JSONL files to estimate token consumption.
    Compares baseline vs optimized runs and generates a summary report.

.PARAMETER BaselineId
    Conversation ID of the baseline run (without token-optimizer skill).

.PARAMETER OptimizedId
    Conversation ID of the optimized run (with token-optimizer skill).

.PARAMETER BrainDir
    Path to the Antigravity brain directory. Defaults to ~/.gemini/antigravity/brain.

.EXAMPLE
    .\benchmark.ps1 -BaselineId "abc-123" -OptimizedId "def-456"
    .\benchmark.ps1 -BaselineId "abc-123"  # Single run analysis
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$BaselineId,

    [Parameter(Mandatory=$false)]
    [string]$OptimizedId,

    [Parameter(Mandatory=$false)]
    [string]$BrainDir = (Join-Path $env:USERPROFILE ".gemini\antigravity\brain")
)

# --- Helper Functions ---

function Get-TranscriptPath {
    param([string]$ConversationId)
    $path = Join-Path $BrainDir "$ConversationId\.system_generated\logs\transcript_full.jsonl"
    if (-not (Test-Path $path)) {
        $path = Join-Path $BrainDir "$ConversationId\.system_generated\logs\transcript.jsonl"
    }
    return $path
}

function Measure-Transcript {
    param([string]$TranscriptPath)

    if (-not (Test-Path $TranscriptPath)) {
        Write-Error "Transcript not found: $TranscriptPath"
        return $null
    }

    $lines = Get-Content $TranscriptPath -Encoding UTF8

    $stats = @{
        TotalSteps        = 0
        UserInputs        = 0
        ModelResponses    = 0
        ToolCalls         = 0
        ToolResults       = 0
        InputBytes        = 0   # bytes from user + tool results (input tokens)
        OutputBytes       = 0   # bytes from model responses + tool calls (output tokens)
        TotalBytes        = 0
        ThinkingBytes     = 0
        StepBreakdown     = @()
    }

    foreach ($line in $lines) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }

        try {
            $step = $line | ConvertFrom-Json
        } catch {
            continue
        }

        $stats.TotalSteps++

        $contentBytes = 0
        if ($step.content) {
            $contentBytes = [System.Text.Encoding]::UTF8.GetByteCount($step.content)
        }

        $thinkingBytes = 0
        if ($step.thinking) {
            $thinkingBytes = [System.Text.Encoding]::UTF8.GetByteCount($step.thinking)
        }

        $toolCallBytes = 0
        $toolCallCount = 0
        if ($step.tool_calls) {
            $toolCallJson = ($step.tool_calls | ConvertTo-Json -Depth 10 -Compress)
            $toolCallBytes = [System.Text.Encoding]::UTF8.GetByteCount($toolCallJson)
            $toolCallCount = @($step.tool_calls).Count
        }

        $stepType = if ($step.type) { $step.type } else { "UNKNOWN" }

        switch -Wildcard ($stepType) {
            "USER_INPUT" {
                $stats.UserInputs++
                $stats.InputBytes += $contentBytes
            }
            "PLANNER_RESPONSE" {
                $stats.ModelResponses++
                $stats.OutputBytes += $contentBytes + $toolCallBytes
                $stats.ThinkingBytes += $thinkingBytes
                $stats.ToolCalls += $toolCallCount
            }
            "TOOL_RESULT" {
                $stats.ToolResults++
                $stats.InputBytes += $contentBytes  # tool results are input tokens
            }
            default {
                $stats.InputBytes += $contentBytes
            }
        }

        $stats.TotalBytes += ($contentBytes + $toolCallBytes + $thinkingBytes)

        $stats.StepBreakdown += @{
            Index   = $step.step_index
            Type    = $stepType
            Bytes   = ($contentBytes + $toolCallBytes)
        }
    }

    return $stats
}

function Format-Bytes {
    param([int64]$Bytes)
    if ($Bytes -ge 1MB) { return "{0:N1} MB" -f ($Bytes / 1MB) }
    if ($Bytes -ge 1KB) { return "{0:N1} KB" -f ($Bytes / 1KB) }
    return "$Bytes B"
}

function Estimate-Tokens {
    param([int64]$Bytes, [double]$BytesPerToken = 4.0)
    return [math]::Round($Bytes / $BytesPerToken)
}

function Show-Stats {
    param([hashtable]$Stats, [string]$Label)

    $estInputTokens  = Estimate-Tokens $Stats.InputBytes
    $estOutputTokens = Estimate-Tokens $Stats.OutputBytes
    $estTotalTokens  = Estimate-Tokens $Stats.TotalBytes

    Write-Host ""
    Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host "  $Label" -ForegroundColor Cyan
    Write-Host "═══════════════════════════════════════════" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Steps & Turns" -ForegroundColor Yellow
    Write-Host "    Total Steps:      $($Stats.TotalSteps)"
    Write-Host "    User Inputs:      $($Stats.UserInputs)"
    Write-Host "    Model Responses:  $($Stats.ModelResponses)"
    Write-Host "    Tool Calls:       $($Stats.ToolCalls)"
    Write-Host "    Tool Results:     $($Stats.ToolResults)"
    Write-Host ""
    Write-Host "  Byte Usage" -ForegroundColor Yellow
    Write-Host "    Input Bytes:      $(Format-Bytes $Stats.InputBytes)"
    Write-Host "    Output Bytes:     $(Format-Bytes $Stats.OutputBytes)"
    Write-Host "    Thinking Bytes:   $(Format-Bytes $Stats.ThinkingBytes)"
    Write-Host "    Total Bytes:      $(Format-Bytes $Stats.TotalBytes)"
    Write-Host ""
    Write-Host "  Estimated Tokens (~4 bytes/token)" -ForegroundColor Yellow
    Write-Host "    Input Tokens:     ~$($estInputTokens.ToString('N0'))"
    Write-Host "    Output Tokens:    ~$($estOutputTokens.ToString('N0'))"
    Write-Host "    Total Tokens:     ~$($estTotalTokens.ToString('N0'))"
    Write-Host ""
}

function Show-Comparison {
    param([hashtable]$Baseline, [hashtable]$Optimized)

    $byteSaved = $Baseline.TotalBytes - $Optimized.TotalBytes
    $bytePercent = if ($Baseline.TotalBytes -gt 0) {
        [math]::Round(($byteSaved / $Baseline.TotalBytes) * 100, 1)
    } else { 0 }

    $toolSaved = $Baseline.ToolCalls - $Optimized.ToolCalls
    $toolPercent = if ($Baseline.ToolCalls -gt 0) {
        [math]::Round(($toolSaved / $Baseline.ToolCalls) * 100, 1)
    } else { 0 }

    $stepSaved = $Baseline.TotalSteps - $Optimized.TotalSteps
    $stepPercent = if ($Baseline.TotalSteps -gt 0) {
        [math]::Round(($stepSaved / $Baseline.TotalSteps) * 100, 1)
    } else { 0 }

    $tokenSaved = (Estimate-Tokens $Baseline.TotalBytes) - (Estimate-Tokens $Optimized.TotalBytes)

    Write-Host ""
    Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  COMPARISON RESULTS" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""

    $sign = if ($byteSaved -ge 0) { "[-]" } else { "[+]" }
    $color = if ($byteSaved -ge 0) { "Green" } else { "Red" }

    Write-Host "  Metric               Baseline    Optimized   Savings" -ForegroundColor Yellow
    Write-Host "  -----------------------------------------------------"
    Write-Host ("  Total Bytes          {0,-12}{1,-12}{2} {3}%" -f `
        (Format-Bytes $Baseline.TotalBytes), `
        (Format-Bytes $Optimized.TotalBytes), `
        $sign, [math]::Abs($bytePercent)) -ForegroundColor $color

    Write-Host ("  Est. Tokens          {0,-12}{1,-12}{2} {3}" -f `
        (Estimate-Tokens $Baseline.TotalBytes).ToString('N0'), `
        (Estimate-Tokens $Optimized.TotalBytes).ToString('N0'), `
        $sign, $tokenSaved.ToString('N0')) -ForegroundColor $color

    $sign2 = if ($toolSaved -ge 0) { "[-]" } else { "[+]" }
    $color2 = if ($toolSaved -ge 0) { "Green" } else { "Red" }
    Write-Host ("  Tool Calls           {0,-12}{1,-12}{2} {3}%" -f `
        $Baseline.ToolCalls, $Optimized.ToolCalls, $sign2, [math]::Abs($toolPercent)) -ForegroundColor $color2

    $sign3 = if ($stepSaved -ge 0) { "[-]" } else { "[+]" }
    $color3 = if ($stepSaved -ge 0) { "Green" } else { "Red" }
    Write-Host ("  Total Steps          {0,-12}{1,-12}{2} {3}%" -f `
        $Baseline.TotalSteps, $Optimized.TotalSteps, $sign3, [math]::Abs($stepPercent)) -ForegroundColor $color3

    Write-Host ""

    # Verdict
    if ($bytePercent -ge 20) {
        Write-Host "  [PASS] Significant token reduction ($bytePercent%)" -ForegroundColor Green
    } elseif ($bytePercent -ge 5) {
        Write-Host "  [WARN] Marginal token reduction ($bytePercent%)" -ForegroundColor Yellow
    } elseif ($bytePercent -ge 0) {
        Write-Host "  [FAIL] Little to no reduction ($bytePercent%)" -ForegroundColor Red
    } else {
        Write-Host "  [FAIL] REGRESSION: Optimized used MORE tokens ($bytePercent%)" -ForegroundColor Red
    }
    Write-Host ""
}

# --- List mode: show recent conversations ---

function Show-RecentConversations {
    param([int]$Count = 10)

    Write-Host ""
    Write-Host "Recent conversations:" -ForegroundColor Cyan
    Write-Host ""

    $conversations = Get-ChildItem $BrainDir -Directory |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First $Count

    foreach ($conv in $conversations) {
        $transcriptPath = Join-Path $conv.FullName ".system_generated\logs\transcript.jsonl"
        if (Test-Path $transcriptPath) {
            $firstLine = Get-Content $transcriptPath -First 1 -Encoding UTF8
            $preview = ""
            try {
                $step = $firstLine | ConvertFrom-Json
                if ($step.content) {
                    $preview = $step.content.Substring(0, [math]::Min(60, $step.content.Length))
                    if ($step.content.Length -gt 60) { $preview += "..." }
                }
            } catch {}

            $size = (Get-Item $transcriptPath).Length
            Write-Host "  $($conv.Name)" -ForegroundColor Yellow -NoNewline
            Write-Host "  $(Format-Bytes $size)  $($conv.LastWriteTime.ToString('yyyy-MM-dd HH:mm'))" -NoNewline
            if ($preview) {
                Write-Host "  $preview" -ForegroundColor DarkGray
            } else {
                Write-Host ""
            }
        }
    }
    Write-Host ""
}

# --- Main ---

if (-not $BaselineId -and -not $OptimizedId) {
    Write-Host ""
    Write-Host "Token Benchmark Tool" -ForegroundColor Cyan
    Write-Host "Usage:" -ForegroundColor Yellow
    Write-Host "  .\benchmark.ps1 -BaselineId <id>                    # Analyze single run"
    Write-Host "  .\benchmark.ps1 -BaselineId <id> -OptimizedId <id>  # Compare two runs"
    Write-Host ""

    Show-RecentConversations
    exit 0
}

if ($BaselineId) {
    $baselinePath = Get-TranscriptPath $BaselineId
    $baselineStats = Measure-Transcript $baselinePath
    if ($baselineStats) {
        Show-Stats $baselineStats "BASELINE: $BaselineId"
    }
}

if ($OptimizedId) {
    $optimizedPath = Get-TranscriptPath $OptimizedId
    $optimizedStats = Measure-Transcript $optimizedPath
    if ($optimizedStats) {
        Show-Stats $optimizedStats "OPTIMIZED: $OptimizedId"
    }
}

if ($baselineStats -and $optimizedStats) {
    Show-Comparison $baselineStats $optimizedStats
}
