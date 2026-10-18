param([string]$CairoDirectory, [switch]$WithNormalization)
$ErrorActionPreference = 'Stop'
$source = Join-Path $PSScriptRoot 'vector-png'
if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))) {
    $source = Join-Path $PSScriptRoot 'skills/vector-png'
}
$profileDirectory = [Environment]::GetFolderPath('UserProfile')
$destination = Join-Path $profileDirectory '.agents/skills/vector-png'
if (Test-Path -LiteralPath $destination) {
    throw "Existing skill was not overwritten: $destination"
}
if (-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))) {
    throw 'Keep this installer next to the supplied vector-png folder.'
}
New-Item -ItemType Directory -Force (Split-Path $destination) | Out-Null
Copy-Item -LiteralPath $source -Destination $destination -Recurse
& python -m venv (Join-Path $destination '.venv')
if ($LASTEXITCODE -ne 0) { throw 'Python virtual environment creation failed.' }
$pythonExecutable = Join-Path $destination '.venv/Scripts/python.exe'
& $pythonExecutable -m pip install -r (Join-Path $destination 'requirements.txt')
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
if ($WithNormalization) {
    & $pythonExecutable -m pip install -r (Join-Path $destination 'requirements-normalization.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Normalization dependency installation failed.' }
    & $pythonExecutable -m playwright install chromium
    if ($LASTEXITCODE -ne 0) { throw 'Chromium installation failed.' }
}
if (-not $CairoDirectory) {
    $candidates = @(
        $env:VECTOR_PNG_CAIRO_DIR,
        'C:/msys64/ucrt64/bin',
        (Join-Path $profileDirectory '.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/Library/bin')
    )
    foreach ($candidate in $candidates) {
        if ($candidate -and ((Test-Path -LiteralPath (Join-Path $candidate 'cairo.dll')) -or
                            (Test-Path -LiteralPath (Join-Path $candidate 'libcairo-2.dll')))) {
            $CairoDirectory = $candidate
            break
        }
    }
}
if ($CairoDirectory) {
    Set-Content -LiteralPath (Join-Path $destination 'cairo-path.txt') -Value $CairoDirectory -Encoding utf8
}
$checkDirectory = Join-Path ([IO.Path]::GetTempPath()) ('vector-png-check-' + [guid]::NewGuid().ToString('N'))
& $pythonExecutable (Join-Path $destination 'scripts/roundtrip_check.py') --output-dir $checkDirectory
if ($LASTEXITCODE -ne 0) { throw 'Skill copied, but validation failed. Check native Cairo setup.' }
if ($WithNormalization) {
    $normalizationDirectory = Join-Path $checkDirectory 'normalization'
    & $pythonExecutable (Join-Path $destination 'scripts/normalization_check.py') --output-dir $normalizationDirectory
    if ($LASTEXITCODE -ne 0) { throw 'Normalization rendering/roundtrip validation failed.' }
}
Write-Host "Installed and roundtrip verified: $destination"
Write-Host 'Open a new Codex chat/session and invoke $vector-png.'

