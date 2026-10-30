$ErrorActionPreference = "Stop"

$root = (Get-Location).Path
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements.txt
}

Write-Host "Starting cmms-mcp on http://127.0.0.1:8765 ..."
$env:MCP_TRANSPORT = "streamable-http"
$mcp = Start-Process -FilePath $python `
    -ArgumentList "-m", "mcp_server.cmms_server" `
    -WorkingDirectory $root -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 2

Write-Host "Starting FastAPI on http://127.0.0.1:8000 ..."
$api = Start-Process -FilePath $python `
    -ArgumentList "-m", "uvicorn", "fieldops.main:app", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $root -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 3

Write-Host "Starting Streamlit on http://127.0.0.1:8501 ..."
try {
    & $python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
}
finally {
    Write-Host "Stopping API and MCP..."
    if ($api -and -not $api.HasExited) { Stop-Process -Id $api.Id -Force }
    if ($mcp -and -not $mcp.HasExited) { Stop-Process -Id $mcp.Id -Force }
}
