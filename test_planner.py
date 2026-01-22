#!/usr/bin/env python3
"""
Simple test for the Planner Agent.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from agents.planner import PlannerAgent

def test_planner_agent():
    """Test basic functionality of the Planner Agent."""
    print("Testing Planner Agent...")
    
    # Create planner instance
    planner = PlannerAgent()
    
    # Test technical spec generation
    requirements = {
        'title': 'Test API Service',
        'description': 'A simple test API service for demonstration',
        'requirements': [
            'implement REST API endpoints',
            'add database integration',
            'include basic authentication'
        ],
        'complexity': 'low',
        'tech_stack': ['Python', 'Flask'],
        'type': 'api',
        'priority': 'medium',
        'team_size': 1
    }
    
    # Generate spec
    spec = planner.generate_technical_spec(requirements)
    
    # Verify spec was created
    assert spec.title == 'Test API Service'
    assert len(spec.requirements) == 3
    assert spec.priority == 'medium'
    
    print("✓ Technical spec generation works")
    
    # Test plan update - use minimal changes for low impact
    changes = {
        'documentation': {'format': 'markdown'}
    }
    
    update = planner.update_plan('TEST-001', changes, 'Added documentation format')
    assert update.plan_id == 'TEST-001'
    assert 'Low' in update.impact
    
    print("✓ Plan update works")
    
    # Test project analysis
    project_data = {
        'features': [
            {'name': 'user management', 'critical': True},
            {'name': 'data export', 'integrations': ['storage']}
        ],
        'timelines': {'duration': 4},
        'resources': ['developer', 'designer']
    }
    
    analysis = planner.analyze_project_scope(project_data)
    assert 'feature_count' in analysis
    assert 'complexity_score' in analysis
    assert analysis['feature_count'] == 2
    
    print("✓ Project analysis works")
    
    # Test export functionality
    json_spec = planner.export_spec(spec, 'json')
    assert 'Test API Service' in json_spec
    
    markdown_spec = planner.export_spec(spec, 'markdown')
    assert '# Test API Service' in markdown_spec
    
    print("✓ Export functionality works")
    
    print("\nAll tests passed! Planner Agent is working correctly.")

if __name__ == '__main__':
    test_planner_agent()
