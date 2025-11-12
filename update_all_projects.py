import json
from pathlib import Path

# Read config
config_path = Path.home() / ".claude.json"
with open(config_path, 'r', encoding='utf-8') as f:
    config = json.load(f)

# Track updates
updated_projects = []
skipped_projects = []

# Update all projects that have notebooklm MCP server
for project_path, project_config in config.get("projects", {}).items():
    if "mcpServers" in project_config and "notebooklm" in project_config["mcpServers"]:
        # Update to HTTP mode
        old_config = project_config["mcpServers"]["notebooklm"].copy()
        project_config["mcpServers"]["notebooklm"] = {
            "type": "http",
            "url": "http://127.0.0.1:8765/mcp/"
        }
        updated_projects.append({
            "path": project_path,
            "old_type": old_config.get("type", "unknown")
        })
    else:
        # Check if project exists but doesn't have notebooklm
        if project_path in config.get("projects", {}):
            skipped_projects.append(project_path)

# Write back
with open(config_path, 'w', encoding='utf-8') as f:
    json.dump(config, f, indent=2)

# Report results
print("=" * 60)
print("MCP Config Update Complete")
print("=" * 60)

if updated_projects:
    print(f"\n[UPDATED] {len(updated_projects)} project(s):")
    for proj in updated_projects:
        # Shorten path for display
        short_path = proj["path"].split("\\")[-1] if "\\" in proj["path"] else proj["path"]
        print(f"  - {short_path}")
        print(f"    Was: {proj['old_type']} -> Now: HTTP")
else:
    print("\n[INFO] No projects with notebooklm MCP server found")

if skipped_projects:
    print(f"\n[SKIPPED] {len(skipped_projects)} project(s) without notebooklm:")
    for proj in skipped_projects[:5]:  # Show first 5
        short_path = proj.split("\\")[-1] if "\\" in proj else proj
        print(f"  - {short_path}")
    if len(skipped_projects) > 5:
        print(f"  ... and {len(skipped_projects) - 5} more")

print("\n" + "=" * 60)
print("All projects now use: http://127.0.0.1:8765/mcp/")
print("Restart Claude Code in each directory to apply changes")
print("=" * 60)
