import json
from pathlib import Path

config_path = Path.home() / ".claude.json"
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

notebooklm_key = r'C:\Users\awang\git\notebooklm-mcp'
if notebooklm_key in config['projects']:
    if 'mcpServers' in config['projects'][notebooklm_key]:
        if 'notebooklm' in config['projects'][notebooklm_key]['mcpServers']:
            print(json.dumps(config['projects'][notebooklm_key]['mcpServers']['notebooklm'], indent=2))
        else:
            print("No notebooklm MCP server configured")
    else:
        print("No MCP servers configured")
else:
    print("Project not found")
