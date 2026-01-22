# SupervisorAgent with LangGraph

This project implements a basic SupervisorAgent using LangGraph-style workflow patterns.

## Features

- **SupervisorAgent**: A coordinator that manages multiple agents in a workflow
- **LangGraph-style Execution**: Graph-based workflow execution with nodes and edges
- **Agent Registration**: Dynamic agent registration and execution
- **Workflow Management**: Conditional routing between agents based on execution results

## Files

- `supervisor_agent.py`: Basic supervisor agent implementation
- `langgraph_supervisor.py`: Enhanced LangGraph-style supervisor with workflow graphs
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

## Future Enhancements

- Integration with actual LangGraph libraries
- AI-powered decision making
- Distributed agent execution
- Real-time monitoring and debugging
- Persistent workflow storage