"""Example usage of BeadsClient."""

import asyncio
from beadsclient import BeadsClient


async def async_example():
    """Example of async usage."""
    client = BeadsClient()
    
    print("=== Async Example ===")
    
    # Show a bead
    result = await client.show("AC-pf4")
    if result.success:
        print("Bead details:")
        print(result.stdout)
    else:
        print(f"Error: {result.stderr}")
    
    # List ready beads
    result = await client.ready()
    if result.success:
        print("\nReady beads:")
        print(result.stdout)


def sync_example():
    """Example of sync usage."""
    client = BeadsClient()
    
    print("\n=== Sync Example ===")
    
    # Show a bead
    result = client.show_sync("AC-pf4")
    if result.success:
        print("Bead details:")
        print(result.stdout)
    else:
        print(f"Error: {result.stderr}")
    
    # List beads
    result = client.list_beads_sync()
    if result.success:
        print("\nBeads list:")
        print(result.stdout)


if __name__ == "__main__":
    print("BeadsClient Example")
    print("==================")
    
    # Run async example
    asyncio.run(async_example())
    
    # Run sync example
    sync_example()