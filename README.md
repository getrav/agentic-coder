# Agentic Coder with HealthMonitor & GitHub Webhook Integration

This project implements a multi-agent coding system with workspace isolation, health monitoring, and GitHub webhook integration.

## Features

- **SupervisorAgent**: A coordinator that manages multiple agents in a workflow
- **LangGraph-style Execution**: Graph-based workflow execution with nodes and edges
- **Agent Registration**: Dynamic agent registration and execution
- **Workflow Management**: Conditional routing between agents based on execution results
- **HealthMonitor Daemon**: Background async monitoring service for system health and recovery
- **Workspace Isolation**: Git worktree-based isolation for agent workspaces
- **GitHub Webhook Integration**: Handles GitHub webhook events (issues.opened, issue_comment)

## Files

- `supervisor_agent.py`: Basic supervisor agent implementation
- `langgraph_supervisor.py`: Enhanced LangGraph-style supervisor with workflow graphs
- `src/agentic_coder/health_monitor.py`: HealthMonitor daemon implementation
- `health_monitor_cli.py`: Command-line interface for HealthMonitor
- `src/agentic_coder/workspace/agent_workspace.py`: Agent workspace management
- `github_webhook.py`: GitHub webhook handler and Flask server
- `webhook_cli.py`: Command-line interface for webhook management
- `requirements.txt`: Python dependencies (for when LangGraph libraries are available)

## Usage

### Basic Supervisor
```python
from supervisor_agent import SupervisorAgent

supervisor = SupervisorAgent()
supervisor.register_agent("analyzer", analysis_agent)
supervisor.register_agent("processor", processing_agent)
results = supervisor.run_workflow(initial_input)
```

### LangGraph-style Supervisor
```python
from langgraph_supervisor import LangGraphSupervisorAgent

supervisor = LangGraphSupervisorAgent()
supervisor.register_agent("input_processing", input_processing_agent)
supervisor.register_agent("analysis", analysis_agent)
# ... register more agents
supervisor.create_workflow()
result = supervisor.run_workflow(initial_input)
```

## Workflow Components

### Agents
- **Input Processing**: Validates and normalizes input data
- **Analysis**: Analyzes data and extracts insights
- **Decision**: Makes workflow decisions
- **Execution**: Executes main tasks
- **Validation**: Validates results
- **Output**: Generates final output

### Graph Structure
- **Nodes**: Represent individual agents/steps
- **Edges**: Define workflow transitions with conditions
- **State Management**: Maintains workflow state across executions

## Example Output

The supervisor coordinates agents through a structured workflow:
```
🚀 Starting LangGraph-style Supervised Workflow...
🔄 Input Processing: Processing input data...
🔍 Analysis: Analyzing data...
🤔 Decision: Making workflow decisions...
⚡ Execution: Running main task...
✅ Validation: Validating results...
📤 Output: Generating final output...
```

## Key Concepts

1. **Agent Coordination**: Supervisor decides which agent executes next
2. **Conditional Routing**: Workflow paths based on agent results
3. **State Persistence**: Maintains context across agent executions
4. **Error Handling**: Graceful handling of agent failures
5. **Modular Design**: Easy to add new agents and workflow patterns

## HealthMonitor Daemon

The HealthMonitor provides background async monitoring for system health and recovery:

### Starting the HealthMonitor
```bash
# Start with default settings
python3 health_monitor_cli.py start

# Start with specific agents and workspaces
python3 health_monitor_cli.py start --agents agent1 agent2 --workspaces ws1 ws2

# Check status
python3 health_monitor_cli.py status

# List monitors
python3 health_monitor_cli.py list
```

### Features
- **System Monitoring**: CPU, memory, disk usage, filesystem health
- **Agent Monitoring**: Track agent workspace health and resource usage
- **Workspace Monitoring**: Monitor workspace integrity and database connectivity
- **Health Metrics**: Collect and store metrics with configurable thresholds
- **Alert System**: Generate alerts when metrics exceed thresholds
- **Persistent Storage**: SQLite database for metrics and alerts

For detailed documentation, see [HEALTHMONITOR.md](HEALTHMONITOR.md).

## GitHub Webhook Integration

The project includes GitHub webhook integration that handles:

- **issues.opened**: Processes when new issues are created
- **issue_comment**: Processes when comments are created, edited, or deleted on issues

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Start the webhook server:
```bash
python webhook_cli.py start
```

### Testing

Generate sample events:
```bash
python webhook_cli.py generate-samples
```

Test webhook events:
```bash
python webhook_cli.py test sample_events/issue_opened.json --event-type issues
python webhook_cli.py test sample_events/issue_comment_created.json --event-type issue_comment
```

### Configuration

- `GITHUB_WEBHOOK_SECRET`: GitHub webhook secret for signature verification
- `WEBHOOK_HOST`: Server host (default: 0.0.0.0)
- `WEBHOOK_PORT`: Server port (default: 5000)
- `WEBHOOK_DEBUG`: Enable debug mode (default: false)

## Future Enhancements

- Integration with actual LangGraph libraries
- AI-powered decision making
- Distributed agent execution
- Real-time monitoring and debugging
- Persistent workflow storage
- Auto-scaling based on health metrics
- Integration with external monitoring systems
- Additional GitHub event types
- Webhook event storage and replay
