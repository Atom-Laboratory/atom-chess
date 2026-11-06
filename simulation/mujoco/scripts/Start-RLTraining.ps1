param(
    [ValidateSet('lift','grasp')][string]$Stage = 'lift',
    [ValidateRange(1,100000000)][int]$Steps = 20000,
    [ValidateSet('auto','cpu','cuda')][string]$Device = 'auto',
    [double]$Speed = 2,
    [switch]$Headless,
    [string]$Resume,
    [string]$WarmStart,
    [string]$Output
)
$ErrorActionPreference = 'Stop'
if ($Resume -and $WarmStart) { throw 'Choose Resume or WarmStart.' }
$atomModule = Split-Path $PSScriptRoot -Parent
$atomRoot = Split-Path (Split-Path $atomModule -Parent) -Parent
$atomPython = Join-Path $atomModule '.venv/Scripts/python.exe'
$atomBundle = Join-Path $atomModule 'runs/playground-fingertip-only-v1'
if (-not (Test-Path -LiteralPath $atomPython)) { throw 'Create the MuJoCo venv and install the rl extra; see visual-grasp-rl-guide.md.' }
if (-not (Test-Path -LiteralPath $atomBundle)) { throw 'Build the fingertip-only Playground bundle first; see visual-grasp-rl-guide.md.' }
if ([double]::IsNaN($Speed) -or [double]::IsInfinity($Speed) -or $Speed -le 0) { throw 'Speed must be finite and positive.' }
if (-not $Output) { $Output = Join-Path $atomModule ('runs/visual-'+$Stage+'-'+[guid]::NewGuid().ToString('N')) }
$atomArgs = @('-u', '-B', (Join-Path $atomModule 'examples/train_visual_grasp.py'), '--bundle', $atomBundle,
    '--output', $Output, '--steps', $Steps, '--stage', $Stage, '--device', $Device, '--speed', $Speed,
    '--eval-episodes', 5)
if (-not $Headless) { $atomArgs += '--watch' }
if ($Resume) { $atomArgs += @('--resume',$Resume) }
if ($WarmStart) { $atomArgs += @('--warm-start',$WarmStart) }
Write-Host "Training output: $Output"
Write-Host 'Lift starts with a scripted reset grip. Grasp starts above the piece. Both use RGB policy inputs and oracle rewards.'
Push-Location $atomRoot
try {
    & $atomPython @atomArgs
    if ($LASTEXITCODE -ne 0) { throw "RL process exited with code $LASTEXITCODE. Inspect the output and latest checkpoint." }
} finally { Pop-Location }
