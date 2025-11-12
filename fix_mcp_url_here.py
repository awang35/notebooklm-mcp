import json
from pathlib import Path

# Read config
config_path = Path.home() / ".claude.json"
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Update URL for notebooklm-mcp directory
notebooklm_key = r'C:\Users\awang\git\notebooklm-mcp'

# Check if notebooklm MCP server exists for this directory
if notebooklm_key in config["projects"]:
    if "mcpServers" not in config["projects"][notebooklm_key]:
        config["projects"][notebooklm_key]["mcpServers"] = {}

    # Add or update notebooklm MCP server config
    config["projects"][notebooklm_key]["mcpServers"]["notebooklm"] = {
        "type": "http",
        "url": "http://127.0.0.1:8765/mcp/"
    }

    print(f"[OK] Updated notebooklm-mcp directory config")
else:
    print(f"[ERROR] notebooklm-mcp directory not found in config")

# Write back
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2)

print("\nConfig updated for notebooklm-mcp directory:")
print("  URL: http://127.0.0.1:8765/mcp/")
print("\nRestart Claude Code to apply changes.")
