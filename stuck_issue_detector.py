#!/usr/bin/env python3
"""
Stuck Issue Detection System

A comprehensive system for detecting and handling stuck/hanging issues
in supervisor agent workflows.

Features:
- Agent execution timeout detection
- Workflow progress monitoring
- Blocked task identification
- Automatic recovery mechanisms
- Alerting and reporting
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StuckIssueType(Enum):
    TIMEOUT = "timeout"
    BLOCKED = "blocked"
    INFINITE_LOOP = "infinite_loop"
    NO_PROGRESS = "no_progress"
    DEADLOCK = "deadlock"


class IssueSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class StuckIssue:
    """Represents a detected stuck issue"""
    issue_id: str
    issue_type: StuckIssueType
    severity: IssueSeverity
    agent_name: str
    workflow_id: str
    description: str
    detected_at: datetime
    metadata: Dict[str, Any]
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class StuckIssueDetector:
    """Detects stuck issues in agent workflows"""
    
    def __init__(self, 
                 timeout_threshold: int = 300,  # 5 minutes
                 progress_check_interval: int = 60,  # 1 minute
                 max_iterations_without_progress: int = 10):
        self.timeout_threshold = timeout_threshold
        self.progress_check_interval = progress_check_interval
        self.max_iterations_without_progress = max_iterations_without_progress
        
        # Tracking data
        self.agent_start_times: Dict[str, datetime] = {}
        self.agent_last_progress: Dict[str, datetime] = {}
        self.agent_iteration_counts: Dict[str, int] = {}
        self.workflow_tracking: Dict[str, Dict[str, Any]] = {}
        
        # Detected issues
        self.detected_issues: List[StuckIssue] = []
        
        # Monitoring thread
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_active = False
        
        # Callbacks for handling issues
        self.issue_callbacks: List[Callable] = []
        
    def register_issue_callback(self, callback: Callable):
        """Register a callback to be called when an issue is detected"""
        self.issue_callbacks.append(callback)
        
    def start_monitoring(self):
        """Start the background monitoring thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
            self.monitoring_thread.daemon = True
            self.monitoring_thread.start()
            logger.info("Stuck issue monitoring started")
    
    def stop_monitoring(self):
        """Stop the background monitoring thread"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join()
        logger.info("Stuck issue monitoring stopped")
    
    def agent_started(self, agent_name: str, workflow_id: str):
        """Called when an agent starts execution"""
        now = datetime.now()
        self.agent_start_times[agent_name] = now
        self.agent_last_progress[agent_name] = now
        self.agent_iteration_counts[agent_name] = 0
        
        logger.info(f"Agent {agent_name} started in workflow {workflow_id}")
    
    def agent_progress(self, agent_name: str, workflow_id: str):
        """Called when an agent makes progress"""
        now = datetime.now()
        self.agent_last_progress[agent_name] = now
        if agent_name in self.agent_iteration_counts:
            self.agent_iteration_counts[agent_name] += 1
        else:
            self.agent_iteration_counts[agent_name] = 1
            
        logger.debug(f"Agent {agent_name} made progress in workflow {workflow_id}")
    
    def agent_completed(self, agent_name: str, workflow_id: str):
        """Called when an agent completes execution"""
        # Clean up tracking data
        self.agent_start_times.pop(agent_name, None)
        self.agent_last_progress.pop(agent_name, None)
        self.agent_iteration_counts.pop(agent_name, None)
        
        logger.info(f"Agent {agent_name} completed in workflow {workflow_id}")
    
    def workflow_started(self, workflow_id: str, initial_state: Dict[str, Any]):
        """Called when a workflow starts"""
        self.workflow_tracking[workflow_id] = {
            'started_at': datetime.now(),
            'last_progress': datetime.now(),
            'completed_nodes': [],
            'total_iterations': 0,
            'state': initial_state.copy()
        }
        
        logger.info(f"Workflow {workflow_id} started")
    
    def workflow_progress(self, workflow_id: str, completed_node: str, iteration: int):
        """Called when a workflow makes progress"""
        if workflow_id in self.workflow_tracking:
            self.workflow_tracking[workflow_id]['last_progress'] = datetime.now()
            self.workflow_tracking[workflow_id]['completed_nodes'].append(completed_node)
            self.workflow_tracking[workflow_id]['total_iterations'] = iteration
            
            logger.debug(f"Workflow {workflow_id} progress: node {completed_node} completed")
    
    def workflow_completed(self, workflow_id: str):
        """Called when a workflow completes"""
        # Clean up tracking data
        self.workflow_tracking.pop(workflow_id, None)
        
        logger.info(f"Workflow {workflow_id} completed")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                self._check_for_timeout_issues()
                self._check_for_no_progress_issues()
                self._check_for_blocked_issues()
                time.sleep(self.progress_check_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
    
    def _check_for_timeout_issues(self):
        """Check for agents that have been running too long"""
        now = datetime.now()
        
        for agent_name, start_time in self.agent_start_times.items():
            elapsed = (now - start_time).total_seconds()
            
            if elapsed > self.timeout_threshold:
                issue = StuckIssue(
                    issue_id=f"timeout_{agent_name}_{int(now.timestamp())}",
                    issue_type=StuckIssueType.TIMEOUT,
                    severity=IssueSeverity.HIGH,
                    agent_name=agent_name,
                    workflow_id="unknown",  # Could be enhanced to track workflow per agent
                    description=f"Agent {agent_name} has been running for {elapsed:.1f} seconds (threshold: {self.timeout_threshold}s)",
                    detected_at=now,
                    metadata={
                        'elapsed_time': elapsed,
                        'threshold': self.timeout_threshold
                    }
                )
                
                self._report_issue(issue)
    
    def _check_for_no_progress_issues(self):
        """Check for agents that are not making progress"""
        now = datetime.now()
        
        for agent_name, last_progress in self.agent_last_progress.items():
            if agent_name not in self.agent_iteration_counts:
                continue
                
            elapsed = (now - last_progress).total_seconds()
            iteration_count = self.agent_iteration_counts[agent_name]
            
            # Check if no progress for too long but agent is still registered (running)
            if (elapsed > self.timeout_threshold and 
                agent_name in self.agent_start_times):
                
                issue = StuckIssue(
                    issue_id=f"no_progress_{agent_name}_{int(now.timestamp())}",
                    issue_type=StuckIssueType.NO_PROGRESS,
                    severity=IssueSeverity.MEDIUM,
                    agent_name=agent_name,
                    workflow_id="unknown",
                    description=f"Agent {agent_name} has not made progress for {elapsed:.1f} seconds (iterations: {iteration_count})",
                    detected_at=now,
                    metadata={
                        'elapsed_since_progress': elapsed,
                        'iteration_count': iteration_count,
                        'threshold': self.timeout_threshold
                    }
                )
                
                self._report_issue(issue)
    
    def _check_for_blocked_issues(self):
        """Check for workflows that appear blocked"""
        now = datetime.now()
        
        for workflow_id, progress_data in self.workflow_tracking.items():
            last_progress = progress_data['last_progress']
            total_iterations = progress_data['total_iterations']
            
            elapsed = (now - last_progress).total_seconds()
            
            # Check if workflow has been stuck for too many iterations
            if (elapsed > self.timeout_threshold and 
                total_iterations > self.max_iterations_without_progress):
                
                issue = StuckIssue(
                    issue_id=f"blocked_workflow_{workflow_id}_{int(now.timestamp())}",
                    issue_type=StuckIssueType.BLOCKED,
                    severity=IssueSeverity.CRITICAL,
                    agent_name="workflow_supervisor",
                    workflow_id=workflow_id,
                    description=f"Workflow {workflow_id} appears blocked after {total_iterations} iterations, no progress for {elapsed:.1f}s",
                    detected_at=now,
                    metadata={
                        'elapsed_since_progress': elapsed,
                        'total_iterations': total_iterations,
                        'completed_nodes': len(progress_data['completed_nodes']),
                        'threshold_iterations': self.max_iterations_without_progress
                    }
                )
                
                self._report_issue(issue)
    
    def _report_issue(self, issue: StuckIssue):
        """Report a detected issue"""
        # Check if we already reported this issue recently
        recent_issues = [i for i in self.detected_issues 
                        if (i.agent_name == issue.agent_name and 
                            i.issue_type == issue.issue_type and
                            (datetime.now() - i.detected_at).total_seconds() < 60)]
        
        if not recent_issues:
            self.detected_issues.append(issue)
            logger.warning(f"Stuck issue detected: {issue.description}")
            
            # Call registered callbacks
            for callback in self.issue_callbacks:
                try:
                    callback(issue)
                except Exception as e:
                    logger.error(f"Error in issue callback: {e}")
    
    def get_active_issues(self) -> List[StuckIssue]:
        """Get all currently active issues"""
        # Remove issues older than 1 hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        active_issues = [issue for issue in self.detected_issues 
                        if issue.detected_at > one_hour_ago]
        
        return active_issues
    
    def get_issue_summary(self) -> Dict[str, Any]:
        """Get a summary of detected issues"""
        active_issues = self.get_active_issues()
        
        summary = {
            'total_issues': len(active_issues),
            'by_type': {},
            'by_severity': {},
            'by_agent': {},
            'issues': [self._issue_to_dict(issue) for issue in active_issues]
        }
        
        for issue in active_issues:
            # Count by type
            issue_type = issue.issue_type.value
            summary['by_type'][issue_type] = summary['by_type'].get(issue_type, 0) + 1
            
            # Count by severity
            severity = issue.severity.value
            summary['by_severity'][severity] = summary['by_severity'].get(severity, 0) + 1
            
            # Count by agent
            agent = issue.agent_name
            summary['by_agent'][agent] = summary['by_agent'].get(agent, 0) + 1
        
        return summary
    
    def _issue_to_dict(self, issue: StuckIssue) -> Dict[str, Any]:
        """Convert issue to dictionary for serialization"""
        return {
            'issue_id': issue.issue_id,
            'issue_type': issue.issue_type.value,
            'severity': issue.severity.value,
            'agent_name': issue.agent_name,
            'workflow_id': issue.workflow_id,
            'description': issue.description,
            'detected_at': issue.detected_at.isoformat(),
            'metadata': issue.metadata
        }


class StuckIssueRecovery:
    """Handles recovery from stuck issues"""
    
    def __init__(self, detector: StuckIssueDetector):
        self.detector = detector
        self.recovery_strategies = {
            StuckIssueType.TIMEOUT: self._handle_timeout,
            StuckIssueType.BLOCKED: self._handle_blocked,
            StuckIssueType.NO_PROGRESS: self._handle_no_progress,
            StuckIssueType.INFINITE_LOOP: self._handle_infinite_loop,
            StuckIssueType.DEADLOCK: self._handle_deadlock
        }
    
    def register_recovery_strategy(self, issue_type: StuckIssueType, strategy: Callable):
        """Register a custom recovery strategy"""
        self.recovery_strategies[issue_type] = strategy
    
    def handle_issue(self, issue: StuckIssue) -> bool:
        """Handle a detected issue"""
        strategy = self.recovery_strategies.get(issue.issue_type)
        
        if strategy:
            try:
                success = strategy(issue)
                logger.info(f"Recovery strategy executed for issue {issue.issue_id}: {'success' if success else 'failed'}")
                return success
            except Exception as e:
                logger.error(f"Error in recovery strategy for issue {issue.issue_id}: {e}")
                return False
        else:
            logger.warning(f"No recovery strategy for issue type: {issue.issue_type}")
            return False
    
    def _handle_timeout(self, issue: StuckIssue) -> bool:
        """Default timeout recovery strategy"""
        logger.warning(f"Timeout recovery: Terminating agent {issue.agent_name}")
        
        # In a real implementation, this would:
        # 1. Kill the stuck agent process
        # 2. Restart the agent with clean state
        # 3. Possibly retry the last operation
        
        return True  # Simulate successful recovery
    
    def _handle_blocked(self, issue: StuckIssue) -> bool:
        """Default blocked workflow recovery strategy"""
        logger.warning(f"Blocked workflow recovery: Resetting workflow {issue.workflow_id}")
        
        # In a real implementation, this would:
        # 1. Identify the blocking condition
        # 2. Clear the block (kill stuck agents, release resources)
        # 3. Restart the workflow from last known good state
        
        return True  # Simulate successful recovery
    
    def _handle_no_progress(self, issue: StuckIssue) -> bool:
        """Default no-progress recovery strategy"""
        logger.warning(f"No progress recovery: Restarting agent {issue.agent_name}")
        
        # In a real implementation, this would:
        # 1. Check agent health
        # 2. Restart if unhealthy
        # 3. Resume from last checkpoint
        
        return True  # Simulate successful recovery
    
    def _handle_infinite_loop(self, issue: StuckIssue) -> bool:
        """Default infinite loop recovery strategy"""
        logger.warning(f"Infinite loop recovery: Breaking agent {issue.agent_name}")
        
        # In a real implementation, this would:
        # 1. Force interrupt the agent
        # 2. Analyze the loop condition
        # 3. Fix the condition or skip the problematic operation
        
        return True  # Simulate successful recovery
    
    def _handle_deadlock(self, issue: StuckIssue) -> bool:
        """Default deadlock recovery strategy"""
        logger.warning(f"Deadlock recovery: Breaking deadlock in workflow {issue.workflow_id}")
        
        # In a real implementation, this would:
        # 1. Identify deadlocked resources/agents
        # 2. Force release one of the deadlocked resources
        # 3. Resume normal execution
        
        return True  # Simulate successful recovery


# Example usage and demonstration
def demo_stuck_issue_detection():
    """Demonstrate stuck issue detection functionality"""
    print("🔍 Stuck Issue Detection Demo")
    print("=" * 40)
    
    # Create detector with short timeouts for demo
    detector = StuckIssueDetector(
        timeout_threshold=5,  # 5 seconds for demo
        progress_check_interval=1,  # Check every 1 second
        max_iterations_without_progress=3
    )
    
    # Create recovery handler
    recovery = StuckIssueRecovery(detector)
    
    # Register a simple callback to log issues
    def log_issue(issue: StuckIssue):
        print(f"🚨 ISSUE DETECTED: {issue.description}")
    
    detector.register_issue_callback(log_issue)
    # Also register the recovery handler
    detector.register_issue_callback(recovery.handle_issue)
    
    # Start monitoring
    detector.start_monitoring()
    
    # Simulate some agent activities
    print("\n📊 Simulating agent activities...")
    
    # Agent 1: Normal operation
    detector.agent_started("agent1", "workflow1")
    time.sleep(1)
    detector.agent_progress("agent1", "workflow1")
    time.sleep(1)
    detector.agent_completed("agent1", "workflow1")
    print("✅ Agent1: Normal operation completed")
    
    # Agent 2: Timeout scenario
    detector.agent_started("agent2", "workflow2")
    print("⏳ Agent2: Will timeout (running too long)...")
    time.sleep(8)  # Longer than 5 second timeout
    
    # Agent 3: No progress scenario
    detector.agent_started("agent3", "workflow3")
    detector.agent_progress("agent3", "workflow3")  # One progress update
    print("⏸️ Agent3: Will have no progress...")
    time.sleep(8)  # No progress for too long
    
    # Workflow: Blocked scenario
    detector.workflow_started("blocked_workflow", {"initial": "state"})
    for i in range(5):  # More than max_iterations_without_progress (3)
        detector.workflow_progress("blocked_workflow", f"node_{i}", i + 1)
        time.sleep(0.5)
    print("🔄 Workflow: Will appear blocked...")
    time.sleep(6)  # No progress for too long
    
    # Show issue summary
    print("\n📋 Issue Summary:")
    summary = detector.get_issue_summary()
    print(f"Total issues detected: {summary['total_issues']}")
    
    if summary['issues']:
        print("\nDetected issues:")
        for issue in summary['issues']:
            print(f"  - {issue['issue_type']} ({issue['severity']}): {issue['description']}")
    
    # Stop monitoring
    detector.stop_monitoring()
    
    print("\n✅ Demo completed!")


if __name__ == "__main__":
    demo_stuck_issue_detection()