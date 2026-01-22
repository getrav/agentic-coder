#!/usr/bin/env python3
"""CLI tool for the ReviewerAgent."""

import sys
import argparse
import subprocess
from pathlib import Path

# Add src to path
sys.path.insert(0, 'src')

from reviewer_agent import ReviewerAgent


def get_git_diff():
    """Get git diff for current changes."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError:
        try:
            # Try unstaged changes if no staged changes
            result = subprocess.run(
                ['git', 'diff'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            print("❌ No changes found to review")
            sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ReviewerAgent - Analyze code changes and provide feedback"
    )
    
    parser.add_argument(
        '--diff-file', '-f',
        help='Read diff from file instead of git'
    )
    
    parser.add_argument(
        '--output-format', '-o',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    # Get diff content
    if args.diff_file:
        with open(args.diff_file, 'r') as f:
            diff_text = f.read()
    else:
        diff_text = get_git_diff()
        if not diff_text.strip():
            print("❌ No changes found to review")
            sys.exit(1)
    
    if args.verbose:
        print(f"📋 Analyzing diff ({len(diff_text)} characters)...")
    
    # Initialize agent and analyze
    agent = ReviewerAgent()
    result = agent.analyze_diff(diff_text)
    
    # Output results
    if args.output_format == 'json':
        import json
        from dataclasses import asdict
        
        # Convert to serializable format
        output = asdict(result)
        output['decision'] = result.decision.value
        
        # Convert feedback objects to dicts
        output['feedback'] = [asdict(f) for f in result.feedback]
        
        print(json.dumps(output, indent=2))
    else:
        print(agent.format_review_result(result))
        
        # Add exit code based on decision
        if result.decision.value == 'reject':
            print("\n❌ Changes rejected")
            sys.exit(1)
        elif result.decision.value == 'request_changes':
            print("\n⚠️  Changes requested")
            sys.exit(2)
        else:
            print("\n✅ Changes approved")
            sys.exit(0)


if __name__ == "__main__":
    main()