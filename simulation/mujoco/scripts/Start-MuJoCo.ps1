param([ValidateSet('view', 'demo')][string]$Mode = 'view')
$ErrorActionPreference = 'Stop'
$atomModule = Split-Path $PSScriptRoot -Parent
$atomSimulation = Split-Path $atomModule -Parent
$atomPython = Join-Path $atomModule '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $atomPython)) {
    throw 'Crie .venv e instale o pacote seguindo simulation/mujoco/README.md.'
}
$atomBundle = Join-Path $atomModule 'runs\interactive-chess-v4'
if (-not (Test-Path -LiteralPath $atomBundle)) {
    & $atomPython -m atom_mujoco.cli build --urdf (Join-Path $atomSimulation 'src\urdf\atom.urdf.xacro') --output $atomBundle --interactive
    if ($LASTEXITCODE -ne 0) { throw 'Falha ao compilar o modelo.' }
}
if ($Mode -eq 'view') {
    & $atomPython -m atom_mujoco.cli view --bundle $atomBundle
} else {
    $atomResult = Join-Path $atomModule ('runs\demo-' + [guid]::NewGuid().ToString('N') + '.json')
    & $atomPython -m atom_mujoco.cli demo --bundle $atomBundle --output $atomResult
    Write-Host "Resultado: $atomResult"
}
if ($LASTEXITCODE -ne 0) { throw 'Falha na execução do MuJoCo.' }
