#Requires -Version 5.1
<#
.SYNOPSIS
  Install Ollama on Windows (winget) and pull models used by vendor-lookup-rag.
.EXAMPLE
  Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
  cd <repo-root>
  .\scripts\install-ollama-windows.ps1
#>

$ErrorActionPreference = "Stop"

function Test-OllamaInPath {
    return [bool](Get-Command ollama -ErrorAction SilentlyContinue)
}

if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Error "winget not found. Install App Installer / Windows Package Manager, or install Ollama manually from https://ollama.com/download/windows"
    exit 1
}

Write-Host "Installing Ollama via winget..."
winget install -e --id Ollama.Ollama --accept-package-agreements --accept-source-agreements

if (-not (Test-OllamaInPath)) {
    $ollamaExe = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
    if (Test-Path $ollamaExe) {
        Write-Host "Adding Ollama to PATH for this session: $ollamaExe"
        $dir = Split-Path $ollamaExe
        $env:Path = "$dir;$env:Path"
    }
}

if (-not (Test-OllamaInPath)) {
    Write-Host ""
    Write-Warning "ollama not in PATH yet. Close and reopen PowerShell (or restart the machine), then run:"
    Write-Host "  ollama pull nomic-embed-text"
    Write-Host "  ollama pull gemma4:e4b"
    exit 0
}

Write-Host ""
Write-Host "Pulling embedding model (nomic-embed-text)..."
& ollama pull nomic-embed-text

Write-Host ""
Write-Host "Pulling chat model (gemma4:e4b) — this may take a while..."
& ollama pull gemma4:e4b

Write-Host ""
Write-Host "Done. Ollama should be available at http://localhost:11434"
Write-Host "Optional: ollama list"
