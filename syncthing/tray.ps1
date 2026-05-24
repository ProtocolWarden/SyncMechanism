# Thin shim — delegates to tray.py (requires: pip install -r syncthing/requirements.txt)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
python (Join-Path $ScriptDir 'tray.py') @args
