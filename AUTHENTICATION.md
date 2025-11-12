# Authentication Setup

The NotebookLM MCP server uses **persistent Chrome profile** authentication for reliable, long-lasting sessions.

## How It Works

The server maintains a dedicated Chrome profile that preserves your Google login session across runs. Once you log in manually, the session persists indefinitely.

## Setup

### 1. Configure MCP Server

Create a config file (e.g., `notebooklm-config.json`):

```json
{
  "headless": false,
  "default_notebook_id": "your-notebook-id-here",
  "auth": {
    "use_persistent_session": true,
    "profile_dir": "C:\\path\\to\\chrome_profile_notebooklm"
  }
}
```

**Settings:**
- `headless: false` - Opens a visible browser window (recommended for first login)
- `profile_dir` - Where to store the Chrome profile (session data)
- `use_persistent_session: true` - Enables profile-based authentication

### 2. Update Claude Code Config

Edit `~/.claude.json` (or `.claude/claude_desktop_config.json` on Windows):

```json
{
  "notebooklm": {
    "type": "stdio",
    "command": "uv",
    "args": [
      "--directory",
      "C:\\path\\to\\notebooklm-mcp",
      "run",
      "notebooklm-mcp",
      "--config",
      "C:\\path\\to\\notebooklm-config.json",
      "server"
    ]
  }
}
```

### 3. First Run - Manual Login

On first use:
1. The server launches a Chrome window
2. You'll be redirected to Google sign-in
3. Log in to your Google account
4. Close the browser or let it stay open

Your session is now saved in the profile directory!

### 4. Subsequent Runs

All future runs will:
- Use the saved profile
- Skip the login step
- Work automatically

## Headless Mode (Optional)

Once you've logged in at least once with `headless: false`, you can switch to headless mode:

```json
{
  "headless": true,
  "auth": {
    "use_persistent_session": true,
    "profile_dir": "C:\\path\\to\\chrome_profile_notebooklm"
  }
}
```

The saved session will work in headless mode.

## Troubleshooting

### "Authentication required" on first run
- **Normal!** Log in manually in the browser window
- Session will be saved for next time

### Session expired
- Run the server with `headless: false`
- Log in again manually
- Profile will be updated

### Multiple Google accounts
- The profile saves the account you log in with
- To switch accounts: delete the profile directory and log in with the new account

## Profile Management

**Location:** The profile directory specified in `profile_dir` contains:
- Cookies
- Login session
- Browser preferences

**Backup:** You can copy the profile directory to save your session

**Clean start:** Delete the profile directory to start fresh

## Security Notes

1. **Keep profile private**: The profile contains your authentication tokens
2. **Don't commit to git**: Add profile directory to `.gitignore`
3. **Single machine**: Profiles are machine-specific, don't share between computers

## Example Configs

### Development (visible browser):
```json
{
  "headless": false,
  "default_notebook_id": "abc123",
  "auth": {
    "use_persistent_session": true,
    "profile_dir": "./chrome_profile_dev"
  }
}
```

### Production (headless):
```json
{
  "headless": true,
  "default_notebook_id": "abc123",
  "auth": {
    "use_persistent_session": true,
    "profile_dir": "/opt/notebooklm/profile"
  }
}
```
