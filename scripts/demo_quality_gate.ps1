$ErrorActionPreference = "Stop"

Write-Host "=========================================================="
Write-Host " ForgeLLM CI/CD Quality Gate Demonstration"
Write-Host "=========================================================="
Write-Host "This script demonstrates the automated Quality Gate evaluating"
Write-Host "Experiment EXP-000010 against configurable thresholds."
Write-Host ""

Write-Host "----------------------------------------------------------"
Write-Host " SCENARIO 1: PASSING THE QUALITY GATE"
Write-Host "----------------------------------------------------------"
Write-Host "Configuration: --max-rouge-degradation 0.05"
Write-Host "We tolerate a slight regression up to -0.05 ROUGE-L."
Write-Host "Since the delta is ~0.0, this should PASS as 'EQUIVALENT'."
Write-Host ""

try {
    # We call it via the venv executable directly to ensure it runs correctly
    & .\venv\Scripts\forge.exe evaluate EXP-000010 --max-rouge-degradation 0.05
    $PassExit = $LASTEXITCODE
} catch {
    $PassExit = 1
}

if ($PassExit -eq 0) {
    Write-Host "`n✅ SUCCESS: The pipeline correctly PASSED the Quality Gate." -ForegroundColor Green
} else {
    Write-Host "`n❌ ERROR: The pipeline unexpectedly FAILED the Quality Gate." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "----------------------------------------------------------"
Write-Host " SCENARIO 2: FAILING THE QUALITY GATE"
Write-Host "----------------------------------------------------------"
Write-Host "Configuration: --min-rouge-improvement 0.50"
Write-Host "We strictly demand a massive +0.50 improvement in ROUGE-L."
Write-Host "Since the model hasn't improved that much, this MUST FAIL."
Write-Host ""

try {
    & .\venv\Scripts\forge.exe evaluate EXP-000010 --min-rouge-improvement 0.50
    $FailExit = $LASTEXITCODE
} catch {
    $FailExit = 1
}

if ($FailExit -eq 1) {
    Write-Host "`n✅ SUCCESS: The pipeline correctly FAILED and blocked the degradation." -ForegroundColor Green
} else {
    Write-Host "`n❌ ERROR: The pipeline unexpectedly PASSED a failing model (Exit Code: $FailExit)." -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=========================================================="
Write-Host " Demonstration Complete."
Write-Host "=========================================================="
