$ErrorActionPreference = "Stop"

$python = "python"
if (Test-Path ".venv\Scripts\python.exe") {
    $python = ".venv\Scripts\python.exe"
} else {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
    $python = ".venv\Scripts\python.exe"
}

Write-Host "Installing dependencies..."
& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt

Write-Host "Starting 设备售后运维助手 at http://127.0.0.1:8501"
& $python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
