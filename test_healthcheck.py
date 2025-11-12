#!/usr/bin/env python3
"""Test script to run healthcheck locally"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from notebooklm_mcp.server import NotebookLMFastMCP
from notebooklm_mcp.config import load_config


async def test_healthcheck():
    print("Loading config...")
    config = load_config("C:/Users/awang/git/trade/notebooklm-config.json")

    print("Creating server...")
    server = NotebookLMFastMCP(config)

    print("\nCalling healthcheck (this will initialize the browser)...")
    print("This may take ~30 seconds on first run...\n")

    # Call _ensure_client and then check healthcheck
    # The healthcheck tool is registered but we need to call it via the internal method
    try:
        await server._ensure_client()
        print("\nBrowser initialized successfully!")

        # Try to authenticate
        print("Attempting authentication...")
        auth_success = await server.client.authenticate()

        # Log the current URL for debugging
        if server.client.driver:
            current_url = server.client.driver.current_url
            print(f"\nCurrent URL after auth attempt: {current_url}")

        if auth_success:
            print("Authentication successful!")
        else:
            print("Authentication failed - manual login may be required")

        # Check authentication status
        auth_status = getattr(server.client, "_is_authenticated", False)

        result = {
            "status": "healthy" if auth_status else "needs_auth",
            "message": "Browser initialized and authentication attempted",
            "authenticated": auth_status,
            "notebook_id": config.default_notebook_id,
            "mode": "headless" if config.headless else "gui",
        }
    except Exception as e:
        result = {
            "status": "error",
            "message": str(e),
            "authenticated": False,
        }
        import traceback
        print(f"\nError during initialization: {e}")
        traceback.print_exc()

    print("=" * 60)
    print("HEALTHCHECK RESULT:")
    print("=" * 60)
    for key, value in result.items():
        print(f"  {key}: {value}")
    print("=" * 60)

    # Clean up
    if server.client:
        await server.client.close()
        print("\nBrowser closed.")

    return result


if __name__ == "__main__":
    try:
        result = asyncio.run(test_healthcheck())

        if result["status"] == "healthy":
            print("\nSUCCESS: Server is healthy!")
            sys.exit(0)
        else:
            print(f"\nFAILED: Server status is '{result['status']}'")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
