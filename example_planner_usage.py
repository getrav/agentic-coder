#!/usr/bin/env python3
"""
Example usage of the Planner Agent.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from agents.planner import PlannerAgent

def main():
    """Demonstrate Planner Agent capabilities."""
    print("=== Planner Agent Example ===\n")
    
    planner = PlannerAgent()
    
    # Example 1: Generate technical specification
    print("1. Generating Technical Specification")
    print("-" * 40)
    
    requirements = {
        'title': 'E-commerce Payment System',
        'description': 'Implement secure payment processing for e-commerce platform',
        'requirements': [
            'support credit card payments',
            'integrate with PayPal and Stripe',
            'implement fraud detection',
            'add subscription management',
            'ensure PCI compliance',
            'provide payment analytics dashboard'
        ],
        'complexity': 'high',
        'tech_stack': ['Python', 'Django', 'PostgreSQL', 'Redis'],
        'type': 'web',
        'priority': 'high',
        'team_size': 4
    }
    
    spec = planner.generate_technical_spec(requirements)
    print(planner.export_spec(spec, 'markdown'))
    print("\n" + "="*50 + "\n")
    
    # Example 2: Plan update
    print("2. Updating Project Plan")
    print("-" * 25)
    
    changes = {
        'timeline': {'duration': 12, 'unit': 'weeks'},
        'resources': ['backend lead', 'frontend dev', 'QA engineer', 'devops'],
        'budget': {'amount': 150000, 'currency': 'USD'}
    }
    
    update = planner.update_plan('ECOM-PAY-001', changes, 'Expanded team and budget for enhanced security requirements')
    print(f"Plan ID: {update.plan_id}")
    print(f"Impact: {update.impact}")
    print(f"Reason: {update.reason}")
    print("\n" + "="*50 + "\n")
    
    # Example 3: Project analysis
    print("3. Project Scope Analysis")
    print("-" * 25)
    
    project_data = {
        'features': [
            {'name': 'payment processing', 'critical': True, 'integrations': ['stripe', 'paypal']},
            {'name': 'user management', 'critical': True, 'external_dependencies': ['auth-service']},
            {'name': 'reporting dashboard', 'integrations': ['analytics-api']},
            {'name': 'admin panel', 'external_dependencies': ['admin-service']},
            {'name': 'notification system'}
        ],
        'timelines': {'duration': 16, 'milestones': ['alpha', 'beta', 'launch']},
        'resources': ['backend developer', 'frontend developer', 'QA engineer', 'project manager'],
        'testing': 'unit and integration tests',
        'documentation': 'technical and user documentation'
    }
    
    analysis = planner.analyze_project_scope(project_data)
    
    print(f"Feature Count: {analysis['feature_count']}")
    print(f"Complexity Score: {analysis['complexity_score']:.1f}/10")
    print(f"Resource Adequacy: {analysis['resource_adequacy']}")
    print(f"Timeline Feasibility: {analysis['timeline_feasibility']}")
    print("\nRecommendations:")
    for rec in analysis['recommendations']:
        print(f"  - {rec}")
    
    print("\n" + "="*50 + "\n")
    
    # Example 4: Export capabilities
    print("4. Export Capabilities")
    print("-" * 20)
    
    print("JSON Export (first 200 chars):")
    json_export = planner.export_spec(spec, 'json')
    print(json_export[:200] + "...")
    
    print("\nMarkdown Export (first 300 chars):")
    md_export = planner.export_spec(spec, 'markdown')
    print(md_export[:300] + "...")
    
    print("\n=== Example Complete ===")

if __name__ == '__main__':
    main()
