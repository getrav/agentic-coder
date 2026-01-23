#!/usr/bin/env python3
"""
GitHub Webhook CLI

Command-line interface for managing and testing GitHub webhook integration.
"""

import os
import sys
import json
import argparse
from github_webhook import GitHubWebhookHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_webhook_event(event_file: str, event_type: str):
    """Test webhook with a sample event payload."""
    try:
        with open(event_file, 'r') as f:
            payload = json.load(f)
        
        handler = GitHubWebhookHandler()
        result = handler.handle_webhook(event_type, payload)
        
        print(f"✅ Event test successful: {event_type}")
        print(f"Result: {json.dumps(result, indent=2)}")
        return True
        
    except FileNotFoundError:
        print(f"❌ Event file not found: {event_file}")
        return False
    except Exception as e:
        print(f"❌ Error testing event: {e}")
        return False

def generate_sample_events():
    """Generate sample webhook event files for testing."""
    
    # Sample issue opened event
    issue_opened_event = {
        "action": "opened",
        "issue": {
            "id": 123456789,
            "number": 42,
            "title": "Test Issue",
            "body": "This is a test issue",
            "state": "open",
            "user": {
                "login": "testuser"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "html_url": "https://github.com/test/repo/issues/42"
        },
        "repository": {
            "full_name": "test/repo"
        }
    }
    
    # Sample issue comment created event
    issue_comment_event = {
        "action": "created",
        "issue": {
            "id": 123456789,
            "number": 42,
            "title": "Test Issue",
            "html_url": "https://github.com/test/repo/issues/42"
        },
        "comment": {
            "id": 987654321,
            "body": "This is a test comment",
            "user": {
                "login": "testuser"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z",
            "html_url": "https://github.com/test/repo/issues/42#issuecomment-123"
        },
        "repository": {
            "full_name": "test/repo"
        }
    }
    
    # Write sample files
    os.makedirs('sample_events', exist_ok=True)
    
    with open('sample_events/issue_opened.json', 'w') as f:
        json.dump(issue_opened_event, f, indent=2)
    
    with open('sample_events/issue_comment_created.json', 'w') as f:
        json.dump(issue_comment_event, f, indent=2)
    
    print("✅ Sample event files generated:")
    print("   - sample_events/issue_opened.json")
    print("   - sample_events/issue_comment_created.json")

def start_webhook_server():
    """Start the webhook server."""
    try:
        from github_webhook import run_webhook_server
        
        # Configuration from environment variables
        host = os.environ.get('WEBHOOK_HOST', '0.0.0.0')
        port = int(os.environ.get('WEBHOOK_PORT', 5000))
        debug = os.environ.get('WEBHOOK_DEBUG', 'false').lower() == 'true'
        
        print(f"🚀 Starting GitHub webhook server...")
        print(f"📡 URL: http://{host}:{port}/webhook/github")
        print(f"🔐 Secret: {'Configured' if os.environ.get('GITHUB_WEBHOOK_SECRET') else 'Not configured'}")
        print(f"🎯 Events: issues.opened, issue_comment")
        print()
        
        run_webhook_server(host=host, port=port, debug=debug)
        
    except ImportError as e:
        print(f"❌ Failed to import webhook server: {e}")
        return False

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description='GitHub Webhook CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test webhook with sample event')
    test_parser.add_argument('event_file', help='Path to event JSON file')
    test_parser.add_argument('--event-type', choices=['issues', 'issue_comment'], 
                           required=True, help='Event type')
    
    # Generate samples command
    generate_parser = subparsers.add_parser('generate-samples', 
                                          help='Generate sample event files')
    
    # Start server command
    start_parser = subparsers.add_parser('start', help='Start webhook server')
    
    args = parser.parse_args()
    
    if args.command == 'test':
        success = test_webhook_event(args.event_file, args.event_type)
        sys.exit(0 if success else 1)
    
    elif args.command == 'generate-samples':
        generate_sample_events()
    
    elif args.command == 'start':
        start_webhook_server()
    
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == '__main__':
    main()