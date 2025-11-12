#!/usr/bin/env python3
"""Test script without persistent profile to isolate the crash issue"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from notebooklm_mcp.server import NotebookLMFastMCP
from notebooklm_mcp.config import load_config


async def test_no_profile():
    print("=" * 60)
    print("Testing Chrome Launch WITHOUT Persistent Profile")
    print("=" * 60)

    config_path = "C:/Users/awang/git/trade/notebooklm-config-test-no-profile.json"

    print("\n1. Loading config from:", config_path)
    config = load_config(config_path)
    print(f"   Headless: {config.headless}")
    print(f"   Use Persistent Session: {config.auth.use_persistent_session}")

    print("\n2. Creating server...")
    server = NotebookLMFastMCP(config)

    print("\n3. Initializing browser WITHOUT profile...")
    print("   A Chrome window should open.")

    try:
        await server._ensure_client()
        print("\n   Browser initialized successfully!")
        print("\n4. Chrome launched! This confirms the issue is with the profile directory.")

        # Keep browser open for a moment
        await asyncio.sleep(5)

    except Exception as e:
        print(f"\n   ERROR: Even without profile, Chrome failed to launch: {e}")
        return False
    finally:
        # Clean up
        if server.client:
            await server.client.close()
            print("\nBrowser closed.")

    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_no_profile())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTest completed.")
        sys.exit(0)
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
