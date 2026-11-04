$ErrorActionPreference = "Stop" #出错就停

$root = (Get-Location).Path  #确定项目根目录和 Python 路径
$python = Join-Path $root ".venv\Scripts\python.exe"

if (-not (Test-Path $python)) {    #虚拟环境不存在就创建
    Write-Host "Creating virtual environment..."
    python -m venv .venv
    & $python -m pip install --upgrade pip
    & $python -m pip install -r requirements.txt
}

Write-Host "Starting history-mcp on http://127.0.0.1:8765 ..." #启动 history-mcp
$env:MCP_TRANSPORT = "streamable-http" #设置MCP传输方式
$mcp = Start-Process -FilePath $python ` #启动MCP Server
    -ArgumentList "-m", "mcp_server.history_server" `
    -WorkingDirectory $root -PassThru -WindowStyle Hidden

Start-Sleep -Seconds 2

Write-Host "Starting Streamlit on http://127.0.0.1:8501 ..." #启动 Streamlit
try {
    & $python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501
}
finally { #退出时关闭 MCP
    Write-Host "Stopping MCP..."
    if ($mcp -and -not $mcp.HasExited) { Stop-Process -Id $mcp.Id -Force }
}
