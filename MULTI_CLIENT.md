# Multi-Client Setup Guide

This guide explains how to run ONE NotebookLM MCP server that multiple Claude Code instances can connect to.

## Why Multi-Client Mode?

- **Single browser instance**: Only one Chrome profile needed, shared by all clients
- **Better performance**: Browser stays warm between requests
- **Resource efficient**: No duplicate Chrome processes
- **Simplified auth**: Login once, use everywhere

## Setup Steps

### 1. Start the MCP Server in HTTP Mode

The server needs to run independently in HTTP mode:

```bash
cd C:\Users\awang\git\notebooklm-mcp
uv run notebooklm-mcp --config C:\Users\awang\git\trade\notebooklm-config-gui.json server --transport http --host 127.0.0.1 --port 8765
```

Or use the startup script (see below).

### 2. Configure Claude Code Clients

Update each Claude Code instance's MCP config to connect to the HTTP server:

**Location**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "notebooklm": {
      "type": "http",
      "url": "http://127.0.0.1:8765/mcp/v1/"
    }
  }
}
```

### 3. Start Multiple Claude Code Instances

Now you can start multiple Claude Code instances in different directories. They'll all connect to the same MCP server.

## Startup Script

For convenience, use this PowerShell script to start the server:

**File**: `start_notebooklm_server.ps1`

```powershell
# Start NotebookLM MCP Server in HTTP mode
$ErrorActionPreference = "Stop"

Write-Host "Starting NotebookLM MCP Server..." -ForegroundColor Cyan

$config = "C:\Users\awang\git\trade\notebooklm-config-gui.json"
$port = 8765
$host = "127.0.0.1"

Write-Host "Config: $config" -ForegroundColor Yellow
Write-Host "Server: http://${host}:${port}/mcp/" -ForegroundColor Green

Set-Location "C:\Users\awang\git\notebooklm-mcp"
uv run notebooklm-mcp --config $config server --transport http --host $host --port $port
```

Run it:
```powershell
powershell -ExecutionPolicy Bypass -File start_notebooklm_server.ps1
```

## Server Config Recommendations

For multi-client use, configure the server with:

```json
{
  "headless": false,
  "default_notebook_id": "your-notebook-id",
  "timeout": 60,
  "auth": {
    "use_persistent_session": true,
    "profile_dir": "C:\\Users\\awang\\git\\trade\\chrome_profile_notebooklm"
  }
}
```

**Key settings**:
- `headless: false` for first run (to complete login)
- After login succeeds, you can switch to `headless: true`
- Single `profile_dir` shared by all clients

## Troubleshooting

### Server won't start

**Error**: "Chrome failed to start"

**Solution**: Check if Chrome profile is locked by another process:
```powershell
Get-Process chrome | Stop-Process -Force
```

### Clients can't connect

**Error**: "Connection refused"

**Solution**: Verify server is running:
```powershell
curl http://127.0.0.1:8765/mcp/health
```

### Authentication required

**Error**: "Authentication required"

**Solution**:
1. Stop the server
2. Set `headless: false` in config
3. Restart server and complete manual login
4. Once authenticated, switch to `headless: true`

## Transport Options

The server supports three transport modes:

### STDIO (Default)
- **Use case**: Single Claude Code instance
- **Config**: `--transport stdio`
- **Connection**: Direct process communication

### HTTP
- **Use case**: Multiple clients, REST API access
- **Config**: `--transport http --port 8765`
- **Connection**: HTTP at `http://127.0.0.1:8765/mcp/`

### SSE (Server-Sent Events)
- **Use case**: Streaming responses, real-time updates
- **Config**: `--transport sse --port 8765`
- **Connection**: SSE at `http://127.0.0.1:8765/`

## Example: Running Everything

**Terminal 1** (Server):
```bash
cd C:\Users\awang\git\notebooklm-mcp
uv run notebooklm-mcp --config config.json server --transport http --port 8765
```

**Terminal 2** (Claude Code Instance 1):
```bash
cd C:\Users\awang\git\project1
code .
# Use notebooklm MCP tools
```

**Terminal 3** (Claude Code Instance 2):
```bash
cd C:\Users\awang\git\project2
code .
# Use notebooklm MCP tools
```

Both instances share the same NotebookLM session!
