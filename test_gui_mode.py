#!/usr/bin/env python3
"""Test script for GUI mode with persistent profile"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from notebooklm_mcp.server import NotebookLMFastMCP
from notebooklm_mcp.config import load_config


async def test_gui_mode():
    print("=" * 60)
    print("Testing Persistent Profile Authentication (GUI Mode)")
    print("=" * 60)

    config_path = "C:/Users/awang/git/trade/notebooklm-config-gui.json"

    print("\n1. Loading config from:", config_path)
    config = load_config(config_path)
    print(f"   Headless: {config.headless}")
    print(f"   Profile Dir: {config.auth.profile_dir}")
    print(f"   Use Persistent Session: {config.auth.use_persistent_session}")

    print("\n2. Creating server...")
    server = NotebookLMFastMCP(config)

    print("\n3. Initializing browser...")
    print("   A Chrome window will open.")
    print("   If you see a login page, please log in to Google.")
    print("   Your session will be saved to the profile directory.\n")

    await server._ensure_client()
    print("\n   Browser initialized!")

    print("\n4. Attempting authentication...")
    auth_success = await server.client.authenticate()

    if auth_success:
        print("\n" + "=" * 60)
        print("SUCCESS! Authentication working!")
        print("=" * 60)
        print("Your session is saved. Future runs will skip login.")
    else:
        print("\n" + "=" * 60)
        print("Authentication needed - please log in manually")
        print("=" * 60)
        print("The browser window will stay open.")
        print("Please log in, then your session will be saved.")
        print("\nPress Ctrl+C when done logging in.")

        # Keep browser open for manual login
        try:
            await asyncio.sleep(300)  # Wait 5 minutes
        except KeyboardInterrupt:
            print("\n\nSession should now be saved!")

    # Clean up
    if server.client:
        await server.client.close()
        print("\nBrowser closed.")

    return auth_success


if __name__ == "__main__":
    try:
        success = asyncio.run(test_gui_mode())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest completed.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
