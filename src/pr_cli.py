"""PR Creation CLI - Command-line interface for creating and linking PRs."""

import argparse
import sys
from typing import Optional

from .pr_creation_service import PRCreationService, create_pr_service_from_env, PRCreationResult


def print_pr_result(result: PRCreationResult):
    """Print PR creation result in a user-friendly format."""
    if result.success:
        print("✅ PR created successfully!")
        if result.pr_info:
            print(f"   PR URL: {result.pr_info.pr_url}")
            print(f"   PR Number: #{result.pr_info.pr_number}")
            print(f"   Title: {result.pr_info.title}")
            if result.pr_info.bead_id:
                print(f"   Linked Bead: {result.pr_info.bead_id}")
            if result.bead_updated:
                print("   Bead updated with PR information ✓")
    else:
        print("❌ PR creation failed!")
        if result.error_message:
            print(f"   Error: {result.error_message}")


def cmd_create_pr(args):
    """Handle create-pr command."""
    service = create_pr_service_from_env()
    if not service:
        print("❌ Missing required environment variables:")
        print("   GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO")
        return 1
    
    if args.bead:
        # Create PR for bead
        result = service.create_pr_for_bead(
            bead_id=args.bead,
            head_branch=args.head,
            base_branch=args.base,
            title=args.title,
            body=args.body
        )
    else:
        # Create PR without bead
        result = service.create_pr_without_bead(
            title=args.title,
            head_branch=args.head,
            base_branch=args.base,
            body=args.body
        )
    
    print_pr_result(result)
    return 0 if result.success else 1


def cmd_link_pr(args):
    """Handle link-pr command."""
    service = create_pr_service_from_env()
    if not service:
        print("❌ Missing required environment variables:")
        print("   GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO")
        return 1
    
    result = service.link_pr_to_bead(
        pr_number=args.pr_number,
        bead_id=args.bead_id
    )
    
    print_pr_result(result)
    return 0 if result.success else 1


def cmd_list_bead_prs(args):
    """Handle list-bead-prs command."""
    service = create_pr_service_from_env()
    if not service:
        print("❌ Missing required environment variables:")
        print("   GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO")
        return 1
    
    prs = service.get_prs_for_bead(args.bead_id)
    
    if not prs:
        print(f"No PRs found for bead {args.bead_id}")
        return 0
    
    print(f"PRs linked to bead {args.bead_id}:")
    print("-" * 50)
    
    for pr in prs:
        status_icon = "✅" if pr.pr_url else "❌"
        print(f"{status_icon} #{pr.pr_number}: {pr.pr_title}")
        print(f"    URL: {pr.pr_url}")
        print(f"    Branch: {pr.head_branch} → {pr.base_branch}")
        print()


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Create and manage GitHub pull requests with bead tracking"
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # create-pr command
    create_pr_parser = subparsers.add_parser('create-pr', help='Create a new pull request')
    create_pr_parser.add_argument('--head', required=True, help='Head branch name')
    create_pr_parser.add_argument('--base', default='main', help='Base branch (default: main)')
    create_pr_parser.add_argument('--title', required=True, help='PR title')
    create_pr_parser.add_argument('--body', help='PR body/description')
    create_pr_parser.add_argument('--bead', help='Bead ID to link (optional)')
    
    # link-pr command
    link_pr_parser = subparsers.add_parser('link-pr', help='Link existing PR to bead')
    link_pr_parser.add_argument('pr_number', type=int, help='PR number')
    link_pr_parser.add_argument('bead_id', help='Bead ID to link')
    
    # list-bead-prs command
    list_prs_parser = subparsers.add_parser('list-bead-prs', help='List PRs for a bead')
    list_prs_parser.add_argument('bead_id', help='Bead ID')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        if args.command == 'create-pr':
            return cmd_create_pr(args)
        elif args.command == 'link-pr':
            return cmd_link_pr(args)
        elif args.command == 'list-bead-prs':
            return cmd_list_bead_prs(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
    
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())