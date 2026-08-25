#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonBin = if ($env:PYTHON_BIN) { $env:PYTHON_BIN } else { "python" }
$VenvDir = if ($env:VENV_DIR) { $env:VENV_DIR } else { Join-Path $RootDir ".venv" }

& $PythonBin -m venv $VenvDir
& (Join-Path $VenvDir "Scripts\python.exe") -m pip install --upgrade pip
& (Join-Path $VenvDir "Scripts\python.exe") -m pip install -e $RootDir

& (Join-Path $VenvDir "Scripts\precice-ai.exe") bootstrap @args
