#!/usr/bin/env python3
"""
Example: PR Creation and Linking

This script demonstrates how to use the PR creation and linking functionality
to create GitHub pull requests and link them to bead IDs.
"""

import os
import sys
sys.path.append('src')

from src.pr_creation_service import create_pr_service_from_env
from src.github_pr_client import create_github_config_from_env


def example_create_pr_for_bead():
    """Example: Create a PR for a specific bead."""
    print("🚀 Example: Create PR for Bead")
    print("=" * 40)
    
    # Create service from environment
    service = create_pr_service_from_env()
    if not service:
        print("❌ Missing environment variables")
        print("Required: GITHUB_TOKEN, GITHUB_OWNER, GITHUB_REPO")
        return
    
    # Example bead ID
    bead_id = "AC-yj5"
    head_branch = "polecat/quartz/AC-yj5@mkq73c2j"
    
    print(f"Creating PR for bead: {bead_id}")
    print(f"Head branch: {head_branch}")
    print()
    
    # Create PR
    result = service.create_pr_for_bead(
        bead_id=bead_id,
        head_branch=head_branch,
        title=f"Implement PR creation and linking ({bead_id})",
        body="This pull request implements GitHub PR creation and linking functionality with bead tracking."
    )
    
    if result.success and result.pr_info:
        print("✅ PR created successfully!")
        print(f"   PR URL: {result.pr_info.pr_url}")
        print(f"   PR Number: #{result.pr_info.pr_number}")
        print(f"   Linked Bead: {result.pr_info.bead_id}")
        if result.bead_updated:
            print("   Bead updated with PR information ✓")
    else:
        print("❌ PR creation failed!")
        if result.error_message:
            print(f"   Error: {result.error_message}")


def example_link_existing_pr():
    """Example: Link an existing PR to a bead."""
    print("\n🔗 Example: Link Existing PR to Bead")
    print("=" * 40)
    
    service = create_pr_service_from_env()
    if not service:
        print("❌ Missing environment variables")
        return
    
    # Example data
    pr_number = 123  # Replace with actual PR number
    bead_id = "AC-yj5"
    
    print(f"Linking PR #{pr_number} to bead {bead_id}")
    print()
    
    result = service.link_pr_to_bead(pr_number, bead_id)
    
    if result.success and result.pr_info:
        print("✅ PR linked successfully!")
        print(f"   PR URL: {result.pr_info.pr_url}")
        print(f"   Bead ID: {result.pr_info.bead_id}")
        if result.bead_updated:
            print("   Bead updated with PR information ✓")
    else:
        print("❌ PR linking failed!")
        if result.error_message:
            print(f"   Error: {result.error_message}")


def example_list_bead_prs():
    """Example: List PRs for a bead."""
    print("\n📋 Example: List PRs for Bead")
    print("=" * 40)
    
    service = create_pr_service_from_env()
    if not service:
        print("❌ Missing environment variables")
        return
    
    bead_id = "AC-yj5"
    print(f"Finding PRs for bead: {bead_id}")
    print()
    
    prs = service.get_prs_for_bead(bead_id)
    
    if prs:
        print(f"Found {len(prs)} PR(s) for bead {bead_id}:")
        print()
        for pr in prs:
            status_icon = "✅" if pr.pr_url else "❌"
            print(f"{status_icon} #{pr.pr_number}: {pr.title}")
            print(f"    URL: {pr.pr_url}")
            print(f"    Branch: {pr.head_branch} → {pr.base_branch}")
            print()
    else:
        print(f"No PRs found for bead {bead_id}")


def example_env_setup():
    """Example: Show required environment setup."""
    print("\n⚙️  Example: Environment Setup")
    print("=" * 40)
    
    print("Required environment variables:")
    print()
    print("export GITHUB_TOKEN='your_github_personal_access_token'")
    print("export GITHUB_OWNER='repository_owner'")
    print("export GITHUB_REPO='repository_name'")
    print("export GITHUB_API_URL='https://api.github.com'  # Optional")
    print()
    
    # Check current environment
    config = create_github_config_from_env()
    if config:
        print("✅ Environment variables are configured:")
        print(f"   Owner: {config.owner}")
        print(f"   Repo: {config.repo}")
        print(f"   API URL: {config.api_url}")
    else:
        print("❌ Environment variables are not configured")
        print("   Set the required variables and run this script again")


def main():
    """Run all examples."""
    print("PR Creation and Linking Examples")
    print("=" * 50)
    print()
    
    # Show environment setup
    example_env_setup()
    
    # Get config to see if we can run examples
    config = create_github_config_from_env()
    if config:
        # Run examples
        example_create_pr_for_bead()
        example_link_existing_pr()
        example_list_bead_prs()
    else:
        print("\n⚠️  Skipping live examples due to missing environment configuration")
        print("   Set the required environment variables to run live examples")


if __name__ == "__main__":
    main()