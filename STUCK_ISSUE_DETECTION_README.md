# Stuck Issue Detection Implementation

This implementation adds comprehensive stuck issue detection capabilities to the supervisor agent system, enabling automatic detection and recovery from stuck/hanging workflows and agents.

## Features

### 🔍 Detection Capabilities
- **Timeout Detection**: Identifies agents running longer than threshold
- **No Progress Detection**: Detects agents that are not making progress
- **Blocked Workflow Detection**: Identifies workflows that appear stuck
- **Infinite Loop Detection**: Detects potential infinite loop conditions
- **Deadlock Detection**: Identifies potential deadlock scenarios

### 🚨 Issue Types
1. **Timeout** (High Severity): Agent exceeded execution time threshold
2. **No Progress** (Medium Severity): Agent not making progress
3. **Blocked** (Critical Severity): Workflow appears blocked
4. **Infinite Loop** (High Severity): Agent in potential infinite loop
5. **Deadlock** (Critical Severity): Workflow in potential deadlock

### ⚡ Recovery Mechanisms
- **Timeout Recovery**: Graceful agent termination and restart
- **Blocked Recovery**: Workflow reset and state cleanup
- **No Progress Recovery**: Agent restart from checkpoint
- **Infinite Loop Recovery**: Loop interruption and condition fix
- **Deadlock Recovery**: Resource release and deadlock resolution

## Files Added

### Core Components
- **`stuck_issue_detector.py`**: Main detection system with comprehensive monitoring
- **`supervisor_agent_with_stuck_detection.py`**: Enhanced supervisor with stuck detection
- **`langgraph_supervisor_with_stuck_detection.py`**: LangGraph integration

### Key Classes

#### StuckIssueDetector
- Monitors agent execution times
- Tracks workflow progress
- Detects various stuck conditions
- Provides real-time issue reporting

#### StuckIssueRecovery
- Handles automatic recovery from detected issues
- Configurable recovery strategies
- Graceful error handling and logging

#### SupervisorAgentWithStuckDetection
- Enhanced version of original supervisor
- Seamless integration with existing code
- Backward compatible

#### LangGraphSupervisorWithStuckDetection
- LangGraph-style supervisor with stuck detection
- Maintains all LangGraph functionality
- Adds monitoring and recovery capabilities

## Usage Examples

### Basic Supervisor with Stuck Detection

```python
from supervisor_agent_with_stuck_detection import SupervisorAgentWithStuckDetection

# Create supervisor with stuck detection
supervisor = SupervisorAgentWithStuckDetection(
    enable_stuck_detection=True,
    timeout_threshold=300,  # 5 minutes
    progress_check_interval=60  # Check every minute
)

# Register agents
supervisor.register_agent("analyzer", analysis_agent)
supervisor.register_agent("processor", processing_agent)
supervisor.register_agent("validator", validation_agent)

# Run workflow
result = supervisor.run_workflow(initial_input, max_steps=10)

# Check for stuck issues
issues = supervisor.get_stuck_issues()
if issues and issues.get("total_issues", 0) > 0:
    print(f"Detected {issues['total_issues']} stuck issues")
```

### LangGraph Supervisor with Stuck Detection

```python
from langgraph_supervisor_with_stuck_detection import LangGraphSupervisorWithStuckDetection

# Create LangGraph supervisor with stuck detection
supervisor = LangGraphSupervisorWithStuckDetection(
    enable_stuck_detection=True,
    timeout_threshold=300,
    progress_check_interval=60
)

# Register agents
supervisor.register_agent("input_processing", input_processing_agent)
supervisor.register_agent("analysis", analysis_agent)
supervisor.register_agent("decision", decision_agent)
supervisor.register_agent("execution", execution_agent)
supervisor.register_agent("validation", validation_agent)
supervisor.register_agent("output", output_agent)

# Create and run workflow
supervisor.create_workflow()
result = supervisor.run_workflow(initial_input)

# Check for stuck issues
if "stuck_issues" in result:
    issues = result["stuck_issues"]
    print(f"Active issues: {issues['active_count']}")
```

### Standalone Detection

```python
from stuck_issue_detector import StuckIssueDetector

# Create detector
detector = StuckIssueDetector(
    timeout_threshold=120,  # 2 minutes
    progress_check_interval=30  # Check every 30 seconds
)

# Start monitoring
detector.start_monitoring()

# Track agent activities
detector.agent_started("my_agent", "workflow_123")
detector.agent_progress("my_agent", "workflow_123")
detector.agent_completed("my_agent", "workflow_123")

# Track workflow activities  
detector.workflow_started("workflow_123", {"data": "test"})
detector.workflow_progress("workflow_123", "node_1", 1)
detector.workflow_completed("workflow_123")

# Get detected issues
issues = detector.get_issue_summary()
print(f"Total issues: {issues['total_issues']}")

# Stop monitoring
detector.stop_monitoring()
```

### Custom Recovery Strategies

```python
from stuck_issue_detector import StuckIssueDetector, StuckIssueRecovery, StuckIssueType

# Create detector and recovery
detector = StuckIssueDetector()
recovery = StuckIssueRecovery(detector)

# Define custom recovery strategy
def custom_timeout_recovery(issue):
    print(f"Custom recovery for timeout: {issue.agent_name}")
    # Implement custom recovery logic
    return True

# Register custom strategy
recovery.register_recovery_strategy(StuckIssueType.TIMEOUT, custom_timeout_recovery)

# Register recovery callback
detector.register_issue_callback(recovery.handle_issue)
```

## Configuration Options

### StuckIssueDetector Parameters
- **`timeout_threshold`**: Maximum execution time before timeout (seconds)
- **`progress_check_interval`**: How often to check for issues (seconds)
- **`max_iterations_without_progress`**: Max iterations before workflow considered blocked

### Severity Levels
- **LOW**: Minor issues, logging only
- **MEDIUM**: Moderate issues, may need attention
- **HIGH**: Serious issues, immediate action needed
- **CRITICAL**: Critical issues, system functionality impaired

## Monitoring and Reporting

### Issue Structure
Each detected issue includes:
- **issue_id**: Unique identifier
- **issue_type**: Type of stuck issue
- **severity**: Severity level
- **agent_name**: Name of affected agent
- **workflow_id**: ID of affected workflow
- **description**: Detailed description
- **detected_at**: Detection timestamp
- **metadata**: Additional diagnostic information

### Summary Reports
```python
summary = detector.get_issue_summary()

# Total issues
total_issues = summary['total_issues']

# Issues by type
by_type = summary['by_type']
# Example: {'timeout': 2, 'no_progress': 1}

# Issues by severity
by_severity = summary['by_severity']
# Example: {'high': 2, 'medium': 1}

# Issues by agent
by_agent = summary['by_agent']
# Example: {'analyzer': 1, 'processor': 2}
```

## Integration with Existing Code

### Backward Compatibility
The enhanced supervisor classes are fully backward compatible. Existing code will continue to work without modification:

```python
# This still works exactly the same
from supervisor_agent import SupervisorAgent

supervisor = SupervisorAgent()
supervisor.register_agent("analyzer", analysis_agent)
results = supervisor.run_workflow(input_data)
```

### Migration to Enhanced Version
To enable stuck detection, simply change the import and add configuration:

```python
# Before
from supervisor_agent import SupervisorAgent
supervisor = SupervisorAgent()

# After  
from supervisor_agent_with_stuck_detection import SupervisorAgentWithStuckDetection
supervisor = SupervisorAgentWithStuckDetection(enable_stuck_detection=True)
```

## Performance Considerations

### Monitoring Overhead
- Background monitoring runs in separate thread
- Minimal impact on agent performance
- Configurable check intervals to balance detection vs. performance

### Memory Usage
- Active issue history is automatically cleaned
- Old issues (1+ hours) are removed from memory
- Configurable retention period if needed

### Scalability
- Designed to handle multiple concurrent workflows
- Thread-safe operations
- Efficient data structures for tracking

## Testing and Validation

### Running Tests
```bash
# Test the stuck detection system
python3 stuck_issue_detector.py

# Test the enhanced supervisor
python3 supervisor_agent_with_stuck_detection.py

# Test the LangGraph integration
python3 langgraph_supervisor_with_stuck_detection.py
```

### Demo Scenarios
The test files include demonstrations of:
- Normal agent execution (no issues)
- Timeout scenarios (agents running too long)
- No progress scenarios (agents not making progress)
- Blocked workflow scenarios (workflows stuck)

## Logging and Debugging

### Log Levels
- **INFO**: Normal operation and agent lifecycle events
- **WARNING**: Detected stuck issues and recovery actions
- **ERROR**: System errors and recovery failures

### Debug Information
Detailed information is logged for each detected issue:
- Agent name and workflow ID
- Timestamp and duration
- Threshold values exceeded
- Recovery actions taken

## Future Enhancements

### Planned Features
- **Machine Learning**: AI-based issue prediction
- **Distributed Monitoring**: Multi-process support
- **Persistent Storage**: Historical issue tracking
- **Web Dashboard**: Real-time monitoring interface
- **Alert Integration**: Email/Slack notifications

### Extensibility
The system is designed to be easily extended:
- Add new issue types
- Implement custom recovery strategies
- Integrate with external monitoring systems
- Support different agent frameworks

## Summary

This stuck issue detection implementation provides:

✅ **Comprehensive monitoring** of agent workflows
✅ **Automatic detection** of various stuck conditions  
✅ **Configurable recovery** mechanisms
✅ **Backward compatibility** with existing code
✅ **Real-time reporting** and logging
✅ **Easy integration** and configuration
✅ **Production-ready** with proper error handling

The system enhances the reliability and robustness of the supervisor agent framework by automatically detecting and recovering from stuck conditions, minimizing manual intervention and improving overall system stability.