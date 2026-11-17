param([string]$Python = "python")
$ErrorActionPreference = "Stop"
$testRoot = $PSScriptRoot
$env:PIP_CACHE_DIR = Join-Path $testRoot ".cache\pip"
$env:PYTHONDONTWRITEBYTECODE = "1"
$env:PYTHONPYCACHEPREFIX = Join-Path $testRoot ".cache\pycache"
$taskTemp = Join-Path $testRoot ".tmp"
New-Item -ItemType Directory -Path $taskTemp -Force | Out-Null
$env:TEMP = $taskTemp
$env:TMP = $taskTemp
& $Python -c "import sys; assert sys.version_info >= (3, 10), 'Python 3.10+ required'"
if ($LASTEXITCODE -ne 0) { throw "Select a working Python 3.10+ installation with -Python" }
& $Python -m venv (Join-Path $testRoot ".venv")
if ($LASTEXITCODE -ne 0) { throw "Could not create the test-only virtual environment" }
$testPython = Join-Path $testRoot ".venv\Scripts\python.exe"
& $testPython -m pip install --disable-pip-version-check --no-cache-dir -r (Join-Path $testRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Could not install test dependencies" }
Write-Output "Ready: use $testPython to run run.py or tests\verify.py"
