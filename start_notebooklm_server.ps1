# Start NotebookLM MCP Server in HTTP mode for multi-client support
# Location: C:\Users\awang\git\trade
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host " NotebookLM MCP Server - HTTP Mode" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$repoDir = "C:\Users\awang\git\notebooklm-mcp"
$config = "C:\Users\awang\git\trade\notebooklm-config-gui.json"
$port = 8765
$serverHost = "127.0.0.1"

Write-Host "Repository  : " -NoNewline -ForegroundColor Yellow
Write-Host $repoDir -ForegroundColor White
Write-Host "Config File : " -NoNewline -ForegroundColor Yellow
Write-Host $config -ForegroundColor White
Write-Host "Server URL  : " -NoNewline -ForegroundColor Yellow
Write-Host "http://${serverHost}:${port}/mcp/" -ForegroundColor Green
Write-Host ""
Write-Host "This server can handle multiple Claude Code clients simultaneously." -ForegroundColor Gray
Write-Host "Configure Claude Desktop to connect via HTTP transport." -ForegroundColor Gray
Write-Host ""
Write-Host "Press Ctrl+C to stop the server." -ForegroundColor DarkGray
Write-Host ""

# Change to repo directory
Set-Location $repoDir

try {
    uv run notebooklm-mcp --config $config server --transport http --host $serverHost --port $port
}
catch {
    Write-Host ""
    Write-Host "Server stopped: $_" -ForegroundColor Red
    exit 1
}
