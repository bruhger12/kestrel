$ErrorActionPreference = "Stop"

$engine = Join-Path $PSScriptRoot "..\bin\windows-x86_64\kestrel-0.1.0-avx2.exe"

if (-not (Test-Path -LiteralPath $engine)) {
    throw "Kestrel binary not found: $engine"
}

$output = ("uci`nquit`n" | & $engine) -join "`n"

if ($output -notmatch "id name Kestrel 0\.1\.0") {
    throw "Unexpected engine identity.`n$output"
}

if ($output -notmatch "id author Adam Kulju and Kestrel contributors") {
    throw "Missing Patricia/Kestrel author credit.`n$output"
}

if ($output -notmatch "(?m)^uciok$") {
    throw "Engine did not return uciok.`n$output"
}

Write-Host "UCI smoke test passed."
