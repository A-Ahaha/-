param(
  [switch]$NoVenv,
  [switch]$Reinstall,
  [switch]$SkipDbInit
)

$ErrorActionPreference = "Stop"

function Write-Step($msg) {
  Write-Host ""
  Write-Host "==> $msg"
}

function Load-DotEnv($path) {
  if (!(Test-Path $path)) { return }
  Get-Content $path | ForEach-Object {
    $line = $_.Trim()
    if ($line.Length -eq 0) { return }
    if ($line.StartsWith("#")) { return }
    $idx = $line.IndexOf("=")
    if ($idx -le 0) { return }
    $k = $line.Substring(0, $idx).Trim()
    $v = $line.Substring($idx + 1).Trim()
    if ($k.Length -eq 0) { return }
    [System.Environment]::SetEnvironmentVariable($k, $v)
  }
}

function Ensure-MySqlDatabase($pythonExe) {
  Write-Step "Ensuring MySQL database exists (from DATABASE_URL)"
  $py = @'
import os
from urllib.parse import urlparse, parse_qs

database_url = os.getenv("DATABASE_URL", "").strip()
if not database_url:
    print("[skip] DATABASE_URL is empty")
    raise SystemExit(0)

u = urlparse(database_url)
scheme = (u.scheme or "").lower()
if not scheme.startswith("mysql"):
    print(f"[skip] Non-MySQL DATABASE_URL scheme: {scheme}")
    raise SystemExit(0)

db_name = (u.path or "").lstrip("/")
if not db_name:
    print("[skip] No database name in DATABASE_URL")
    raise SystemExit(0)

host = u.hostname or "127.0.0.1"
port = u.port or 3306
user = u.username or "root"
password = u.password or ""
query = parse_qs(u.query or "")
charset = (query.get("charset") or ["utf8mb4"])[0]

import pymysql

conn = pymysql.connect(
    host=host,
    port=port,
    user=user,
    password=password,
    charset=charset,
    autocommit=True,
)
try:
    with conn.cursor() as cur:
        cur.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` DEFAULT CHARACTER SET {charset}")
    print(f"[ok] Database ensured: {db_name}")
finally:
    conn.close()
'@
  & $pythonExe -c $py
}

Set-Location -Path $PSScriptRoot

Write-Step "Loading environment variables"
if (Test-Path ".env") {
  Load-DotEnv ".env"
} else {
  Load-DotEnv ".env.example"
}

if (-not $NoVenv) {
  if (!(Test-Path ".venv")) {
    Write-Step "Creating virtual environment (.venv)"
    python -m venv .venv
  }

  $venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
  if (!(Test-Path $venvPython)) {
    throw "Virtual env python not found: $venvPython"
  }
} else {
  $venvPython = "python"
}

Write-Step "Installing dependencies"
if ($Reinstall) {
  & $venvPython -m pip install --upgrade pip
  & $venvPython -m pip install -r requirements.txt --upgrade
} else {
  & $venvPython -m pip install -r requirements.txt
}

if (-not $SkipDbInit) {
  Ensure-MySqlDatabase $venvPython
} else {
  Write-Step "Skipping database initialization (-SkipDbInit)"
}

Write-Step "Starting Flask backend"
Write-Host "Tip: set USE_MOCK_ABSA=1 for faster dev"
& $venvPython app.py

