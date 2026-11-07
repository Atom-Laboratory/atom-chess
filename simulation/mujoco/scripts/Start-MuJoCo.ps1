param(
    [ValidateSet('view', 'demo', 'playground')][string]$Mode = 'view',
    [switch]$DiagnosticUnchecked,
    [string]$Bundle
)
$ErrorActionPreference = 'Stop'
if ($DiagnosticUnchecked -and $Mode -ne 'playground') {
    throw '-DiagnosticUnchecked requires -Mode playground.'
}
$atomModule = Split-Path $PSScriptRoot -Parent
$atomSimulation = Split-Path $atomModule -Parent
$atomPython = Join-Path $atomModule '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $atomPython)) {
    throw 'Crie .venv e instale o pacote seguindo simulation/mujoco/README.md.'
}
$atomBundle = Join-Path $atomModule 'assets\bundles\interactive-chess-v6'
$atomBuildOptions = @()
if ($Mode -eq 'playground') {
    $atomBundle = Join-Path $atomModule 'assets\bundles\playground-fingertip-only-v1'
    $atomBuildOptions = @('--parameters', (Join-Path $atomModule 'playground\configs\playground-reachable-board.json'))
}
if ($Mode -eq 'view') {
    $atomBundle = Join-Path $atomModule 'assets\bundles\interactive-wrist-v1'
    $atomBuildOptions = @('--wrist')
}
if ($Bundle) {
    $atomBundle = (Resolve-Path -LiteralPath $Bundle).Path
}
if (-not (Test-Path -LiteralPath $atomBundle)) {
    & $atomPython -m atom_mujoco.cli build --urdf (Join-Path $atomSimulation 'src\urdf\atom.urdf.xacro') --output $atomBundle --interactive @atomBuildOptions
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao compilar o modelo.' }
}
if ($Mode -eq 'view') {
    & $atomPython -m atom_mujoco.cli view --bundle $atomBundle
} elseif ($Mode -eq 'playground') {
    $atomPlaygroundOptions = @()
    if ($DiagnosticUnchecked) { $atomPlaygroundOptions += '--diagnostic-unchecked' }
    & $atomPython (Join-Path $atomModule 'playground\run.py') --bundle $atomBundle @atomPlaygroundOptions
} else {
    $atomResult = Join-Path $atomModule ('examples\evaluate_joint_baseline\runs\demo-' + [guid]::NewGuid().ToString('N') + '.json')
    & $atomPython -m atom_mujoco.cli demo --bundle $atomBundle --output $atomResult
    Write-Host "Resultado: $atomResult"
}
if ($LASTEXITCODE -ne 0) { throw 'Falha na execução do MuJoCo.' }
