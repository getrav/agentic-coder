#!/usr/bin/env python3
"""
Planner Agent - Technical specification generation and plan updates.

This agent is responsible for:
1. Generating technical specifications from requirements
2. Updating and maintaining project plans
3. Providing planning and estimation capabilities
"""

import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class TechnicalSpec:
    """Represents a technical specification."""
    title: str
    description: str
    requirements: List[str]
    approach: str
    dependencies: List[str]
    estimated_effort: str
    priority: str
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()


@dataclass
class PlanUpdate:
    """Represents a plan update."""
    plan_id: str
    changes: Dict[str, Any]
    reason: str
    impact: str
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


class PlannerAgent:
    """Main Planner Agent class."""
    
    def __init__(self):
        self.specs = []
        self.plan_updates = []
        self.current_context = {}
    
    def generate_technical_spec(self, requirements: Dict[str, Any]) -> TechnicalSpec:
        """
        Generate a technical specification from given requirements.
        
        Args:
            requirements: Dictionary containing project requirements
            
        Returns:
            TechnicalSpec object
        """
        logger.info(f"Generating technical spec for: {requirements.get('title', 'Unknown')}")
        
        # Extract key information from requirements
        title = requirements.get('title', 'Untitled Specification')
        description = requirements.get('description', 'No description provided')
        raw_requirements = requirements.get('requirements', [])
        
        # Process requirements into structured format
        processed_requirements = self._process_requirements(raw_requirements)
        
        # Determine approach based on requirements
        approach = self._determine_approach(requirements)
        
        # Identify dependencies
        dependencies = self._identify_dependencies(requirements)
        
        # Estimate effort
        effort = self._estimate_effort(requirements)
        
        # Determine priority
        priority = requirements.get('priority', 'medium')
        
        spec = TechnicalSpec(
            title=title,
            description=description,
            requirements=processed_requirements,
            approach=approach,
            dependencies=dependencies,
            estimated_effort=effort,
            priority=priority
        )
        
        self.specs.append(spec)
        logger.info(f"Generated technical spec: {title}")
        
        return spec
    
    def update_plan(self, plan_id: str, changes: Dict[str, Any], reason: str) -> PlanUpdate:
        """
        Update a project plan with specified changes.
        
        Args:
            plan_id: ID of the plan to update
            changes: Dictionary of changes to apply
            reason: Reason for the update
            
        Returns:
            PlanUpdate object
        """
        logger.info(f"Updating plan {plan_id}: {reason}")
        
        # Assess impact of changes
        impact = self._assess_impact(changes)
        
        update = PlanUpdate(
            plan_id=plan_id,
            changes=changes,
            reason=reason,
            impact=impact
        )
        
        self.plan_updates.append(update)
        logger.info(f"Plan {plan_id} updated successfully")
        
        return update
    
    def analyze_project_scope(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze project scope and provide planning insights.
        
        Args:
            project_data: Project data to analyze
            
        Returns:
            Analysis results
        """
        logger.info("Analyzing project scope")
        
        # Extract key metrics
        features = project_data.get('features', [])
        timelines = project_data.get('timelines', {})
        resources = project_data.get('resources', [])
        
        # Perform analysis
        analysis = {
            'feature_count': len(features),
            'complexity_score': self._calculate_complexity(features),
            'resource_adequacy': self._assess_resources(resources, features),
            'timeline_feasibility': self._assess_timeline(timelines, features),
            'recommendations': self._generate_recommendations(project_data)
        }
        
        return analysis
    
    def _process_requirements(self, raw_requirements: List[str]) -> List[str]:
        """Process raw requirements into structured format."""
        processed = []
        
        for req in raw_requirements:
            # Clean up requirement text
            req = req.strip()
            if req and len(req) > 10:  # Minimum meaningful length
                # Ensure requirement is properly formatted
                if not req[0].isupper():
                    req = req.capitalize()
                if not req.endswith('.'):
                    req += '.'
                processed.append(req)
        
        return processed
    
    def _determine_approach(self, requirements: Dict[str, Any]) -> str:
        """Determine implementation approach based on requirements."""
        complexity = requirements.get('complexity', 'medium')
        tech_stack = requirements.get('tech_stack', [])
        
        if complexity == 'high':
            approach = ("Modular, phased implementation with extensive testing "
                       "and documentation. Focus on scalability and maintainability.")
        elif complexity == 'medium':
            approach = ("Structured implementation with clear separation of concerns. "
                       "Balance between speed and quality.")
        else:
            approach = ("Streamlined implementation focusing on core functionality. "
                       "Iterative development with rapid feedback.")
        
        if tech_stack:
            approach += f" Using tech stack: {', '.join(tech_stack)}."
        
        return approach
    
    def _identify_dependencies(self, requirements: Dict[str, Any]) -> List[str]:
        """Identify project dependencies."""
        dependencies = []
        
        # Extract dependencies from requirements
        if 'dependencies' in requirements:
            dependencies.extend(requirements['dependencies'])
        
        # Add common dependencies based on project type
        project_type = requirements.get('type', 'general')
        common_deps = {
            'web': ['web server', 'database', 'frontend framework'],
            'api': ['authentication', 'rate limiting', 'documentation'],
            'ml': ['data preprocessing', 'model training', 'evaluation framework'],
            'general': ['configuration management', 'logging', 'error handling']
        }
        
        if project_type in common_deps:
            dependencies.extend(common_deps[project_type])
        
        return list(set(dependencies))  # Remove duplicates
    
    def _estimate_effort(self, requirements: Dict[str, Any]) -> str:
        """Estimate implementation effort."""
        complexity = requirements.get('complexity', 'medium')
        feature_count = len(requirements.get('features', []))
        
        # Base effort estimation
        effort_matrix = {
            'low': {1: '1-2 days', 2: '2-3 days', 3: '3-5 days'},
            'medium': {1: '3-5 days', 2: '5-8 days', 3: '1-2 weeks'},
            'high': {1: '1-2 weeks', 2: '2-3 weeks', 3: '3-4 weeks'}
        }
        
        # Determine effort range
        effort_level = min(feature_count, 3)  # Cap at 3 for estimation
        base_effort = effort_matrix.get(complexity, {}).get(effort_level, '1-2 weeks')
        
        # Adjust for team size
        team_size = requirements.get('team_size', 1)
        if team_size > 1:
            base_effort = f"{base_effort} (with {team_size} developers)"
        
        return base_effort
    
    def _assess_impact(self, changes: Dict[str, Any]) -> str:
        """Assess the impact of plan changes."""
        impact_score = 0
        
        # Score based on change types
        if 'timeline' in changes:
            impact_score += 3
        if 'resources' in changes:
            impact_score += 2
        if 'scope' in changes:
            impact_score += 4
        if 'dependencies' in changes:
            impact_score += 2
        
        # Determine impact level
        if impact_score >= 7:
            return "High - Significant changes requiring stakeholder approval"
        elif impact_score >= 4:
            return "Medium - Moderate changes affecting project timeline"
        else:
            return "Low - Minor changes with minimal impact"
    
    def _calculate_complexity(self, features: List[Dict[str, Any]]) -> float:
        """Calculate project complexity score."""
        if not features:
            return 0.0
        
        complexity_score = 0.0
        
        for feature in features:
            # Base complexity per feature
            feature_complexity = 1.0
            
            # Adjust for feature attributes
            if feature.get('integrations'):
                feature_complexity += len(feature['integrations']) * 0.5
            
            if feature.get('external_dependencies'):
                feature_complexity += len(feature['external_dependencies']) * 0.3
            
            if feature.get('critical', False):
                feature_complexity += 0.5
            
            complexity_score += feature_complexity
        
        # Normalize to 0-10 scale
        return min(complexity_score, 10.0)
    
    def _assess_resources(self, resources: List[str], features: List[Dict[str, Any]]) -> str:
        """Assess if resources are adequate for the project."""
        resource_count = len(resources)
        feature_count = len(features)
        
        if resource_count == 0:
            return "Insufficient - No resources allocated"
        
        ratio = feature_count / resource_count
        
        if ratio > 5:
            return "Insufficient - Too many features per resource"
        elif ratio > 3:
            return "Marginal - Resources stretched thin"
        elif ratio > 1:
            return "Adequate - Reasonable resource allocation"
        else:
            return "Good - Well-resourced project"
    
    def _assess_timeline(self, timelines: Dict[str, Any], features: List[Dict[str, Any]]) -> str:
        """Assess timeline feasibility."""
        if not timelines:
            return "No timeline specified"
        
        duration = timelines.get('duration', 0)
        if duration == 0:
            return "No duration specified"
        
        # Simple heuristic: 1 week per feature as baseline
        estimated_weeks = len(features)
        available_weeks = duration
        
        if available_weeks >= estimated_weeks * 1.5:
            return "Feasible - Comfortable timeline"
        elif available_weeks >= estimated_weeks:
            return "Feasible - Tight but achievable"
        else:
            return "Risky - Timeline may be insufficient"
    
    def _generate_recommendations(self, project_data: Dict[str, Any]) -> List[str]:
        """Generate planning recommendations."""
        recommendations = []
        
        # Analyze project structure
        features = project_data.get('features', [])
        if len(features) > 10:
            recommendations.append("Consider breaking into phases or sprints")
        
        # Check for missing elements
        if 'testing' not in project_data:
            recommendations.append("Add testing strategy and resource allocation")
        
        if 'documentation' not in project_data:
            recommendations.append("Include documentation planning")
        
        # Resource recommendations
        resources = project_data.get('resources', [])
        if len(resources) < 2:
            recommendations.append("Consider additional resources for redundancy")
        
        # Default recommendations
        if not recommendations:
            recommendations.append("Project appears well-structured")
        
        return recommendations
    
    def export_spec(self, spec: TechnicalSpec, format: str = 'json') -> str:
        """Export technical specification to specified format."""
        if format.lower() == 'json':
            return json.dumps(asdict(spec), indent=2)
        elif format.lower() == 'markdown':
            return self._spec_to_markdown(spec)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _spec_to_markdown(self, spec: TechnicalSpec) -> str:
        """Convert specification to Markdown format."""
        md = f"# {spec.title}\n\n"
        md += f"**Description:** {spec.description}\n\n"
        md += f"**Priority:** {spec.priority}\n"
        md += f"**Estimated Effort:** {spec.estimated_effort}\n"
        md += f"**Created:** {spec.created_at}\n\n"
        
        md += "## Requirements\n\n"
        for req in spec.requirements:
            md += f"- {req}\n"
        
        md += "\n## Approach\n\n"
        md += f"{spec.approach}\n\n"
        
        md += "## Dependencies\n\n"
        for dep in spec.dependencies:
            md += f"- {dep}\n"
        
        return md
    
    def get_spec_history(self) -> List[TechnicalSpec]:
        """Get history of all generated specifications."""
        return self.specs
    
    def get_plan_update_history(self) -> List[PlanUpdate]:
        """Get history of all plan updates."""
        return self.plan_updates


def main():
    """Main function for testing the Planner Agent."""
    planner = PlannerAgent()
    
    # Example usage
    requirements = {
        'title': 'User Authentication System',
        'description': 'Implement secure user authentication with multiple providers',
        'requirements': [
            'users must be able to register with email and password',
            'support social login (Google, GitHub)',
            'implement password reset functionality',
            'add two-factor authentication',
            'ensure GDPR compliance'
        ],
        'complexity': 'medium',
        'tech_stack': ['Python', 'PostgreSQL', 'React'],
        'type': 'web',
        'priority': 'high',
        'team_size': 2
    }
    
    # Generate technical spec
    spec = planner.generate_technical_spec(requirements)
    print("Generated Technical Specification:")
    print(planner.export_spec(spec, 'markdown'))
    
    # Example plan update
    changes = {
        'timeline': {'duration': 6, 'unit': 'weeks'},
        'resources': ['backend developer', 'frontend developer', 'QA engineer']
    }
    update = planner.update_plan('AUTH-001', changes, 'Added QA resource and extended timeline')
    print(f"\nPlan Update: {update.plan_id}")
    print(f"Impact: {update.impact}")


if __name__ == '__main__':
    main()
