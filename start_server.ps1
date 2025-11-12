# Start NotebookLM MCP Server in HTTP mode for multi-client support
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " NotebookLM MCP Server - HTTP Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$config = "C:\Users\awang\git\trade\notebooklm-config-gui.json"
$port = 8765
$host = "127.0.0.1"

Write-Host "Config File : " -NoNewline -ForegroundColor Yellow
Write-Host $config -ForegroundColor White
Write-Host "Server URL  : " -NoNewline -ForegroundColor Yellow
Write-Host "http://${host}:${port}/mcp/" -ForegroundColor Green
Write-Host ""
Write-Host "This server can handle multiple Claude Code clients." -ForegroundColor Gray
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor Gray
Write-Host ""

Set-Location "C:\Users\awang\git\notebooklm-mcp"

try {
    uv run notebooklm-mcp --config $config server --transport http --host $host --port $port
}
catch {
    Write-Host ""
    Write-Host "Server stopped: $_" -ForegroundColor Red
    exit 1
}
