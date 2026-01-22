"""Command-line interface for BeadsClient."""

import argparse
import asyncio
import sys
from beadsclient import BeadsClient


def create_parser():
    """Create command-line argument parser."""
    parser = argparse.ArgumentParser(
        description="BeadsClient - Python wrapper around bd CLI"
    )
    
    parser.add_argument(
        "--sync", action="store_true",
        help="Run commands synchronously"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Show command
    show_parser = subparsers.add_parser("show", help="Show bead details")
    show_parser.add_argument("bead_id", help="Bead ID to show")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List beads")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create new bead")
    create_parser.add_argument("--title", required=True, help="Bead title")
    create_parser.add_argument("--type", default="task", help="Bead type")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update bead")
    update_parser.add_argument("bead_id", help="Bead ID to update")
    update_parser.add_argument("--status", help="New status")
    
    # Close command
    close_parser = subparsers.add_parser("close", help="Close bead")
    close_parser.add_argument("bead_id", help="Bead ID to close")
    
    # Ready command
    ready_parser = subparsers.add_parser("ready", help="Show ready beads")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Sync beads")
    
    return parser


async def run_async_command(client, args):
    """Run command asynchronously."""
    if args.command == "show":
        result = await client.show(args.bead_id)
    elif args.command == "list":
        result = await client.list_beads()
    elif args.command == "create":
        result = await client.create(args.title, args.type)
    elif args.command == "update":
        result = await client.update(args.bead_id, args.status)
    elif args.command == "close":
        result = await client.close(args.bead_id)
    elif args.command == "ready":
        result = await client.ready()
    elif args.command == "sync":
        result = await client.sync()
    else:
        print(f"Unknown command: {args.command}")
        return 1
    
    if result.success:
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}", file=sys.stderr)
        return 0
    else:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return 1


def run_sync_command(client, args):
    """Run command synchronously."""
    if args.command == "show":
        result = client.show_sync(args.bead_id)
    elif args.command == "list":
        result = client.list_beads_sync()
    elif args.command == "create":
        result = client.create_sync(args.title, args.type)
    elif args.command == "update":
        result = client.update_sync(args.bead_id, args.status)
    elif args.command == "close":
        result = client.close_sync(args.bead_id)
    elif args.command == "ready":
        result = client.ready_sync()
    elif args.command == "sync":
        result = client.sync_sync()
    else:
        print(f"Unknown command: {args.command}")
        return 1
    
    if result.success:
        print(result.stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}", file=sys.stderr)
        return 0
    else:
        print(f"Error: {result.stderr}", file=sys.stderr)
        return 1


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    client = BeadsClient()
    
    if args.sync:
        return run_sync_command(client, args)
    else:
        return asyncio.run(run_async_command(client, args))


if __name__ == "__main__":
    sys.exit(main())