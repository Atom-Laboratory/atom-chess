param(
    [string]$Model = 'qwen3:4b',
    [switch]$Pull
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$data = Join-Path $repo '.atom-knowledge'
$executable = Join-Path $data 'ollama-runtime/ollama.exe'
if (!(Test-Path -LiteralPath $executable)) {
    throw 'Portable Ollama is missing. Follow the README local LLM installation commands first.'
}
if ($Model -match ':cloud$') { throw 'This launcher supports local models only.' }
$env:OLLAMA_HOST = '127.0.0.1:11434'
$env:OLLAMA_MODELS = Join-Path $data 'ollama-models'
$env:OLLAMA_NO_CLOUD = '1'
$running = $false
try { $null = Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 2; $running = $true } catch {}
if (!$running) {
    $stamp = [guid]::NewGuid().ToString('N')
    Start-Process -FilePath $executable -ArgumentList 'serve' -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $data "ollama-$stamp.log") `
        -RedirectStandardError (Join-Path $data "ollama-$stamp-error.log") | Out-Null
    for ($attempt = 0; $attempt -lt 120; $attempt++) {
        try { $null = Invoke-RestMethod 'http://127.0.0.1:11434/api/version' -TimeoutSec 2; $running = $true; break } catch { Start-Sleep -Milliseconds 500 }
    }
    if (!$running) { throw 'Ollama did not become ready; inspect .atom-knowledge/ollama-*-error.log.' }
} else {
    Write-Host 'Using the existing local Ollama server; its model directory and settings are unchanged.'
}
if ($Pull) {
    & $executable pull $Model
    if ($LASTEXITCODE -ne 0) { throw 'Model download failed.' }
}
Write-Host "Ollama is available at http://127.0.0.1:11434. Use --generator ollama --llm-model $Model."
