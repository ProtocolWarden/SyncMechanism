# Thin shim — delegates to install.py (requires: pip install typer[all])
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $ScriptDir 'install.py') @args
