# HealthMonitor Daemon

A background async monitoring service for system health and recovery in the Agentic Coder system.

## Features

- **System Monitoring**: Monitors CPU, memory, disk usage, and filesystem health
- **Agent Monitoring**: Tracks agent workspace health and resource usage
- **Workspace Monitoring**: Monitors workspace integrity and database connectivity
- **Health Metrics**: Collects and stores health metrics with configurable thresholds
- **Alert System**: Generates alerts when metrics exceed warning/critical thresholds
- **Persistent Storage**: Uses SQLite for storing metrics and alerts
- **Async Operation**: Non-blocking monitoring loop with configurable intervals
- **CLI Interface**: Command-line tool for managing the daemon

## Quick Start

### Installation

The HealthMonitor is part of the Agentic Coder package. Ensure you have the required dependencies:

```bash
pip install -r requirements.txt
```

### Starting the Daemon

```bash
# Start with default settings
python3 health_monitor_cli.py start

# Start with specific agents and workspaces
python3 health_monitor_cli.py start --agents agent1 agent2 --workspaces ws1 ws2

# Start with custom interval and alert cooldown
python3 health_monitor_cli.py start --interval 60 --alert-cooldown 600

# Start with debug logging
python3 health_monitor_cli.py start --log-level DEBUG
```

### Checking Status

```bash
# Show current health status
python3 health_monitor_cli.py status
```

### Managing Monitors

```bash
# List current monitors
python3 health_monitor_cli.py list

# Add an agent monitor
python3 health_monitor_cli.py add agent test_agent

# Add a workspace monitor
python3 health_monitor_cli.py add workspace test_workspace

# Remove a monitor
python3 health_monitor_cli.py remove agent test_agent
```

## Architecture

### Core Components

1. **HealthMonitor**: Main daemon class that orchestrates monitoring
2. **HealthMetric**: Represents individual health metrics with thresholds
3. **HealthAlert**: Represents alert notifications
4. **Resource Types**: Different types of resources (AGENT, WORKSPACE, DATABASE, etc.)
5. **Health Status**: Health status levels (HEALTHY, DEGRADED, UNHEALTHY, CRITICAL)

### Monitoring Loop

1. **Collect Metrics**: Gather health metrics from all monitored resources
2. **Store Metrics**: Save metrics to SQLite database
3. **Analyze Metrics**: Check thresholds and generate alerts
4. **Store/Log Alerts**: Save alerts to database and log to console
5. **Wait**: Sleep for configured interval before next check

### Database Schema

The HealthMonitor uses SQLite with two main tables:

#### `health_metrics`
- `id`: Primary key
- `resource_type`: Type of resource (agent, workspace, etc.)
- `resource_id`: Unique identifier for the resource
- `metric_name`: Name of the metric
- `value`: Current metric value
- `threshold_warning`: Warning threshold
- `threshold_critical`: Critical threshold
- `timestamp`: When the metric was collected
- `unit`: Unit of measurement
- `status`: Health status (healthy, unhealthy, etc.)

#### `health_alerts`
- `id`: Primary key
- `resource_type`: Type of resource
- `resource_id`: Resource identifier
- `alert_type`: Type of alert
- `severity`: Alert severity
- `message`: Alert message
- `timestamp`: When the alert was generated
- `metadata`: Additional alert data (JSON)
- `resolved`: Whether the alert has been resolved
- `resolved_at`: When the alert was resolved

## Configuration

### Command Line Options

- `--db-path`: Database file path (default: health_monitor.db)
- `--interval`: Check interval in seconds (default: 30)
- `--alert-cooldown`: Alert cooldown period in seconds (default: 300)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

### Health Thresholds

Default thresholds are configured in the HealthMonitor class:

- **Memory Usage**: Warning at 80%, Critical at 95%
- **CPU Usage**: Warning at 80%, Critical at 95%
- **Disk Usage**: Warning at 85%, Critical at 95%
- **Workspace Size**: Warning at 1GB, Critical at 5GB

## API Reference

### HealthMonitor Class

```python
class HealthMonitor:
    def __init__(self, db_path: str, check_interval: int, alert_cooldown: int, log_level: str)
    def add_agent_monitor(self, agent_id: str) -> None
    def remove_agent_monitor(self, agent_id: str) -> None
    def add_workspace_monitor(self, workspace_id: str) -> None
    def remove_workspace_monitor(self, workspace_id: str) -> None
    def get_health_summary(self) -> Dict[str, Any]
    async def start(self) -> None
    def stop(self) -> None
```

### HealthMetric Class

```python
@dataclass
class HealthMetric:
    resource_type: ResourceType
    resource_id: str
    metric_name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unit: str = ""
    
    @property
    def status(self) -> HealthStatus
```

### HealthAlert Class

```python
@dataclass
class HealthAlert:
    resource_type: ResourceType
    resource_id: str
    alert_type: str
    severity: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
```

## Testing

Run the test suite:

```bash
python3 test_health_monitor.py
```

The tests cover:
- HealthMonitor initialization
- Database operations
- Metric collection and analysis
- Alert generation
- Monitor management
- Health summary generation

## Examples

### Basic Monitoring

```python
from agentic_coder.health_monitor import HealthMonitor

# Create monitor
monitor = HealthMonitor(
    db_path="my_health_monitor.db",
    check_interval=60,
    alert_cooldown=600,
    log_level="INFO"
)

# Add monitors
monitor.add_agent_monitor("agent_001")
monitor.add_workspace_monitor("workspace_001")

# Get health summary
summary = monitor.get_health_summary()
print(f"Active alerts: {summary['active_alerts_count']}")
```

### Custom Metrics

```python
from agentic_coder.health_monitor import HealthMetric, ResourceType, HealthStatus

# Create custom metric
metric = HealthMetric(
    resource_type=ResourceType.AGENT,
    resource_id="custom_agent",
    metric_name="response_time",
    value=150.0,
    threshold_warning=100.0,
    threshold_critical=200.0,
    unit="ms"
)

print(f"Health status: {metric.status.value}")
```

## Integration

### With Gas Town

The HealthMonitor can be integrated with Gas Town for comprehensive system monitoring:

1. **Automatic Startup**: Configure Gas Town to start the HealthMonitor on system boot
2. **Agent Lifecycle**: automatically add/remove monitors when agents are created/destroyed
3. **Alert Integration**: Forward alerts to Gas Town's escalation system
4. **Dashboard Integration**: Use health data in Gas Town's monitoring dashboard

### With Other Systems

The HealthMonitor can be extended to integrate with:
- **Prometheus/Grafana**: Export metrics for visualization
- **Alertmanager**: Forward alerts to external alerting systems
- **Log Aggregation**: Send alerts to log management systems
- **Auto-scaling**: Trigger scaling actions based on health metrics

## Troubleshooting

### Common Issues

1. **Database Access Errors**: Ensure the database file is writable
2. **Permission Errors**: Run with appropriate permissions for system metrics
3. **Missing Dependencies**: Install required packages (psutil for system metrics)
4. **High CPU Usage**: Increase the check interval
5. **Too Many Alerts**: Increase the alert cooldown period

### Debug Mode

Enable debug logging for detailed information:

```bash
python3 health_monitor_cli.py start --log-level DEBUG
```

### Database Maintenance

The database can grow over time. Consider implementing:

1. **Regular Cleanup**: Remove old metrics and resolved alerts
2. **Backup**: Regular database backups
3. **Optimization**: Periodic database optimization

## License

This project is part of the Agentic Coder system and is subject to the same license terms.