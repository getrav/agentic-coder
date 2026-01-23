#!/usr/bin/env python3
"""
HealthMonitor CLI

Command-line interface for starting and managing the HealthMonitor daemon.
"""

import asyncio
import argparse
import sys
import signal
import json
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agentic_coder.health_monitor import HealthMonitor


async def start_daemon(args):
    """Start the HealthMonitor daemon."""
    monitor = HealthMonitor(
        db_path=args.db_path,
        check_interval=args.interval,
        alert_cooldown=args.alert_cooldown,
        log_level=args.log_level
    )
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        monitor.logger.info(f"Received signal {signum}, stopping...")
        monitor.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Add initial monitors if specified
        if args.agents:
            for agent_id in args.agents:
                monitor.add_agent_monitor(agent_id)
        
        if args.workspaces:
            for workspace_id in args.workspaces:
                monitor.add_workspace_monitor(workspace_id)
        
        # Start monitoring
        print(f"Starting HealthMonitor daemon...")
        print(f"Database: {args.db_path}")
        print(f"Check interval: {args.interval}s")
        print(f"Alert cooldown: {args.alert_cooldown}s")
        print(f"Log level: {args.log_level}")
        
        if args.agents:
            print(f"Monitoring agents: {', '.join(args.agents)}")
        
        if args.workspaces:
            print(f"Monitoring workspaces: {', '.join(args.workspaces)}")
        
        print("Press Ctrl+C to stop...")
        
        await monitor.start()
        
    except KeyboardInterrupt:
        monitor.logger.info("Received KeyboardInterrupt, stopping...")
    except Exception as e:
        monitor.logger.error(f"HealthMonitor failed: {e}")
        sys.exit(1)


def show_status(args):
    """Show current health status."""
    try:
        monitor = HealthMonitor(db_path=args.db_path)
        summary = monitor.get_health_summary()
        
        print("HealthMonitor Status")
        print("=" * 30)
        print(f"Database: {args.db_path}")
        print(f"Timestamp: {summary['timestamp']}")
        print(f"Running: {summary['running']}")
        print(f"Monitored Agents: {summary['monitored_agents']}")
        print(f"Monitored Workspaces: {summary['monitored_workspaces']}")
        print(f"Recent Metrics: {summary['recent_metrics_count']}")
        print(f"Active Alerts: {summary['active_alerts_count']}")
        
        if summary['metrics_by_status']:
            print("\nMetrics by Status:")
            for status, count in summary['metrics_by_status'].items():
                print(f"  {status}: {count}")
        
        if summary['active_alerts']:
            print("\nActive Alerts:")
            for alert in summary['active_alerts']:
                print(f"  [{alert['severity'].upper()}] {alert['resource_type']}:{alert['resource_id']}")
                print(f"    {alert['message']}")
        
    except Exception as e:
        print(f"Error getting status: {e}")
        sys.exit(1)


def list_monitors(args):
    """List current monitors."""
    try:
        monitor = HealthMonitor(db_path=args.db_path)
        
        print("Current Monitors")
        print("=" * 20)
        
        if monitor.monitored_agents:
            print("Agents:")
            for agent_id in monitor.monitored_agents:
                print(f"  - {agent_id}")
        else:
            print("Agents: None")
        
        if monitor.monitored_workspaces:
            print("\nWorkspaces:")
            for workspace_id in monitor.monitored_workspaces:
                print(f"  - {workspace_id}")
        else:
            print("\nWorkspaces: None")
            
    except Exception as e:
        print(f"Error listing monitors: {e}")
        sys.exit(1)


def add_monitor(args):
    """Add a monitor."""
    try:
        monitor = HealthMonitor(db_path=args.db_path)
        
        if args.type == "agent":
            monitor.add_agent_monitor(args.id)
            print(f"Added agent monitor: {args.id}")
        elif args.type == "workspace":
            monitor.add_workspace_monitor(args.id)
            print(f"Added workspace monitor: {args.id}")
        else:
            print(f"Unknown monitor type: {args.type}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error adding monitor: {e}")
        sys.exit(1)


def remove_monitor(args):
    """Remove a monitor."""
    try:
        monitor = HealthMonitor(db_path=args.db_path)
        
        if args.type == "agent":
            monitor.remove_agent_monitor(args.id)
            print(f"Removed agent monitor: {args.id}")
        elif args.type == "workspace":
            monitor.remove_workspace_monitor(args.id)
            print(f"Removed workspace monitor: {args.id}")
        else:
            print(f"Unknown monitor type: {args.type}")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error removing monitor: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="HealthMonitor Daemon - Background async monitoring service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start                                    # Start with default settings
  %(prog)s start --agents agent1 agent2            # Start monitoring specific agents
  %(prog)s start --workspaces ws1 ws2 --interval 60  # Start with 60s interval
  %(prog)s status                                  # Show current status
  %(prog)s add agent test_agent                    # Add agent monitor
  %(prog)s remove workspace test_workspace         # Remove workspace monitor
  %(prog)s list                                    # List current monitors
        """
    )
    
    parser.add_argument(
        "--db-path",
        default="health_monitor.db",
        help="Database file path (default: health_monitor.db)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Start command
    start_parser = subparsers.add_parser("start", help="Start the HealthMonitor daemon")
    start_parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="Check interval in seconds (default: 30)"
    )
    start_parser.add_argument(
        "--alert-cooldown",
        type=int,
        default=300,
        help="Alert cooldown period in seconds (default: 300)"
    )
    start_parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    start_parser.add_argument(
        "--agents",
        nargs="+",
        help="Agent IDs to monitor"
    )
    start_parser.add_argument(
        "--workspaces",
        nargs="+",
        help="Workspace IDs to monitor"
    )
    start_parser.set_defaults(func=start_daemon)
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show current health status")
    status_parser.set_defaults(func=show_status)
    
    # List command
    list_parser = subparsers.add_parser("list", help="List current monitors")
    list_parser.set_defaults(func=list_monitors)
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a monitor")
    add_parser.add_argument("type", choices=["agent", "workspace"], help="Monitor type")
    add_parser.add_argument("id", help="Monitor ID")
    add_parser.set_defaults(func=add_monitor)
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a monitor")
    remove_parser.add_argument("type", choices=["agent", "workspace"], help="Monitor type")
    remove_parser.add_argument("id", help="Monitor ID")
    remove_parser.set_defaults(func=remove_monitor)
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Run command
    if args.command == "start":
        asyncio.run(args.func(args))
    else:
        args.func(args)


if __name__ == "__main__":
    main()