#!/usr/bin/env python3
"""
HealthMonitor Daemon

Background async monitoring service for system health and recovery.
Provides continuous monitoring of agents, workspaces, and system resources.
"""

import asyncio
import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
import json
import sqlite3
import os
from pathlib import Path

from .workspace.agent_workspace import AgentWorkspace


class HealthStatus(Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class ResourceType(Enum):
    """Types of resources to monitor."""
    AGENT = "agent"
    WORKSPACE = "workspace"
    DATABASE = "database"
    FILESYSTEM = "filesystem"
    MEMORY = "memory"
    CPU = "cpu"
    NETWORK = "network"


@dataclass
class HealthMetric:
    """Individual health metric."""
    resource_type: ResourceType
    resource_id: str
    metric_name: str
    value: float
    threshold_warning: float
    threshold_critical: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    unit: str = ""
    
    @property
    def status(self) -> HealthStatus:
        """Determine health status based on thresholds."""
        if self.value >= self.threshold_critical:
            return HealthStatus.CRITICAL
        elif self.value >= self.threshold_warning:
            return HealthStatus.UNHEALTHY
        else:
            return HealthStatus.HEALTHY


@dataclass
class HealthAlert:
    """Health alert notification."""
    resource_type: ResourceType
    resource_id: str
    alert_type: str
    severity: HealthStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class HealthMonitor:
    """Main HealthMonitor daemon class."""
    
    def __init__(
        self,
        db_path: str = "health_monitor.db",
        check_interval: int = 30,
        alert_cooldown: int = 300,
        log_level: str = "INFO"
    ):
        """Initialize HealthMonitor."""
        self.db_path = db_path
        self.check_interval = check_interval
        self.alert_cooldown = alert_cooldown
        self.running = False
        self.last_alerts: Dict[str, datetime] = {}
        
        # Setup logging
        self.logger = logging.getLogger("HealthMonitor")
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Initialize database
        self._init_database()
        
        # Track monitored resources
        self.monitored_agents: Set[str] = set()
        self.monitored_workspaces: Set[str] = set()
        
        self.logger.info("HealthMonitor initialized")
    
    def _init_database(self) -> None:
        """Initialize SQLite database for health data storage."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create health metrics table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    metric_name TEXT NOT NULL,
                    value REAL NOT NULL,
                    threshold_warning REAL NOT NULL,
                    threshold_critical REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    unit TEXT,
                    status TEXT NOT NULL
                )
            ''')
            
            # Create health alerts table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS health_alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_at TEXT
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_metrics_resource 
                ON health_metrics(resource_type, resource_id)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_metrics_timestamp 
                ON health_metrics(timestamp)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alerts_resource 
                ON health_alerts(resource_type, resource_id)
            ''')
            
            conn.commit()
            conn.close()
            
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def add_agent_monitor(self, agent_id: str) -> None:
        """Add an agent to monitoring."""
        self.monitored_agents.add(agent_id)
        self.logger.info(f"Added agent to monitoring: {agent_id}")
    
    def remove_agent_monitor(self, agent_id: str) -> None:
        """Remove an agent from monitoring."""
        self.monitored_agents.discard(agent_id)
        self.logger.info(f"Removed agent from monitoring: {agent_id}")
    
    def add_workspace_monitor(self, workspace_id: str) -> None:
        """Add a workspace to monitoring."""
        self.monitored_workspaces.add(workspace_id)
        self.logger.info(f"Added workspace to monitoring: {workspace_id}")
    
    def remove_workspace_monitor(self, workspace_id: str) -> None:
        """Remove a workspace from monitoring."""
        self.monitored_workspaces.discard(workspace_id)
        self.logger.info(f"Removed workspace from monitoring: {workspace_id}")
    
    def collect_metrics(self) -> List[HealthMetric]:
        """Collect health metrics from all monitored resources."""
        metrics = []
        
        # System metrics
        metrics.extend(self._collect_system_metrics())
        
        # Agent metrics
        for agent_id in self.monitored_agents:
            metrics.extend(self._collect_agent_metrics(agent_id))
        
        # Workspace metrics
        for workspace_id in self.monitored_workspaces:
            metrics.extend(self._collect_workspace_metrics(workspace_id))
        
        return metrics
    
    def _collect_system_metrics(self) -> List[HealthMetric]:
        """Collect system-level metrics."""
        metrics = []
        
        try:
            # Memory usage
            import psutil
            memory = psutil.virtual_memory()
            metrics.append(HealthMetric(
                resource_type=ResourceType.MEMORY,
                resource_id="system",
                metric_name="memory_usage_percent",
                value=memory.percent,
                threshold_warning=80.0,
                threshold_critical=95.0,
                unit="%"
            ))
            
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            metrics.append(HealthMetric(
                resource_type=ResourceType.CPU,
                resource_id="system",
                metric_name="cpu_usage_percent",
                value=cpu_percent,
                threshold_warning=80.0,
                threshold_critical=95.0,
                unit="%"
            ))
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_usage_percent = (disk.used / disk.total) * 100
            metrics.append(HealthMetric(
                resource_type=ResourceType.FILESYSTEM,
                resource_id="system",
                metric_name="disk_usage_percent",
                value=disk_usage_percent,
                threshold_warning=85.0,
                threshold_critical=95.0,
                unit="%"
            ))
            
        except ImportError:
            self.logger.warning("psutil not available, skipping system metrics")
        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
        
        return metrics
    
    def _collect_agent_metrics(self, agent_id: str) -> List[HealthMetric]:
        """Collect metrics for a specific agent."""
        metrics = []
        
        try:
            # Check if agent workspace exists
            workspace_path = Path(f"/tmp/agent_{agent_id}")
            if workspace_path.exists():
                # Workspace size
                try:
                    workspace_size = sum(f.stat().st_size for f in workspace_path.rglob('*') if f.is_file())
                    workspace_size_mb = workspace_size / (1024 * 1024)
                    
                    metrics.append(HealthMetric(
                        resource_type=ResourceType.WORKSPACE,
                        resource_id=agent_id,
                        metric_name="workspace_size_mb",
                        value=workspace_size_mb,
                        threshold_warning=1000.0,  # 1GB
                        threshold_critical=5000.0,  # 5GB
                        unit="MB"
                    ))
                except Exception as e:
                    self.logger.warning(f"Error calculating workspace size for {agent_id}: {e}")
                
                # Check agent process (simplified)
                metrics.append(HealthMetric(
                    resource_type=ResourceType.AGENT,
                    resource_id=agent_id,
                    metric_name="agent_active",
                    value=1.0 if workspace_path.exists() else 0.0,
                    threshold_warning=0.5,
                    threshold_critical=0.1,
                    unit="bool"
                ))
            
        except Exception as e:
            self.logger.error(f"Error collecting agent metrics for {agent_id}: {e}")
        
        return metrics
    
    def _collect_workspace_metrics(self, workspace_id: str) -> List[HealthMetric]:
        """Collect metrics for a specific workspace."""
        metrics = []
        
        try:
            workspace = AgentWorkspace()
            workspace_path = workspace.get_workspace(workspace_id)
            
            if workspace_path and workspace_path.exists():
                # Check workspace exists and is accessible
                metrics.append(HealthMetric(
                    resource_type=ResourceType.WORKSPACE,
                    resource_id=workspace_id,
                    metric_name="workspace_exists",
                    value=1.0,
                    threshold_warning=0.5,
                    threshold_critical=0.1,
                    unit="bool"
                ))
                
                # Check if git repository is valid
                try:
                    git_dir = workspace_path / ".git"
                    if git_dir.exists():
                        metrics.append(HealthMetric(
                            resource_type=ResourceType.WORKSPACE,
                            resource_id=workspace_id,
                            metric_name="git_repository_valid",
                            value=1.0,
                            threshold_warning=0.5,
                            threshold_critical=0.1,
                            unit="bool"
                        ))
                    else:
                        metrics.append(HealthMetric(
                            resource_type=ResourceType.WORKSPACE,
                            resource_id=workspace_id,
                            metric_name="git_repository_valid",
                            value=0.0,
                            threshold_warning=0.5,
                            threshold_critical=0.1,
                            unit="bool"
                        ))
                except Exception:
                    metrics.append(HealthMetric(
                        resource_type=ResourceType.WORKSPACE,
                        resource_id=workspace_id,
                        metric_name="git_repository_valid",
                        value=0.0,
                        threshold_warning=0.5,
                        threshold_critical=0.1,
                        unit="bool"
                    ))
            else:
                # Workspace doesn't exist
                metrics.append(HealthMetric(
                    resource_type=ResourceType.WORKSPACE,
                    resource_id=workspace_id,
                    metric_name="workspace_exists",
                    value=0.0,
                    threshold_warning=0.5,
                    threshold_critical=0.1,
                    unit="bool"
                ))
            
        except Exception as e:
            self.logger.error(f"Error collecting workspace metrics for {workspace_id}: {e}")
        
        return metrics
    
    def store_metrics(self, metrics: List[HealthMetric]) -> None:
        """Store metrics in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for metric in metrics:
                cursor.execute('''
                    INSERT INTO health_metrics 
                    (resource_type, resource_id, metric_name, value, 
                     threshold_warning, threshold_critical, timestamp, unit, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    metric.resource_type.value,
                    metric.resource_id,
                    metric.metric_name,
                    metric.value,
                    metric.threshold_warning,
                    metric.threshold_critical,
                    metric.timestamp.isoformat(),
                    metric.unit,
                    metric.status.value
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.debug(f"Stored {len(metrics)} metrics")
            
        except Exception as e:
            self.logger.error(f"Error storing metrics: {e}")
    
    def analyze_metrics(self, metrics: List[HealthMetric]) -> List[HealthAlert]:
        """Analyze metrics and generate alerts."""
        alerts = []
        
        for metric in metrics:
            if metric.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]:
                # Check if we should alert (respect cooldown)
                alert_key = f"{metric.resource_type.value}_{metric.resource_id}_{metric.metric_name}"
                last_alert_time = self.last_alerts.get(alert_key)
                
                if (last_alert_time is None or 
                    (datetime.utcnow() - last_alert_time).total_seconds() > self.alert_cooldown):
                    
                    alert = HealthAlert(
                        resource_type=metric.resource_type,
                        resource_id=metric.resource_id,
                        alert_type=f"{metric.metric_name}_threshold_exceeded",
                        severity=metric.status,
                        message=f"{metric.metric_name} is {metric.value}{metric.unit} (threshold: {metric.threshold_warning})",
                        metadata={
                            "current_value": metric.value,
                            "threshold_warning": metric.threshold_warning,
                            "threshold_critical": metric.threshold_critical,
                            "unit": metric.unit
                        }
                    )
                    
                    alerts.append(alert)
                    self.last_alerts[alert_key] = datetime.utcnow()
        
        return alerts
    
    def store_alerts(self, alerts: List[HealthAlert]) -> None:
        """Store alerts in database."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for alert in alerts:
                cursor.execute('''
                    INSERT INTO health_alerts 
                    (resource_type, resource_id, alert_type, severity, 
                     message, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    alert.resource_type.value,
                    alert.resource_id,
                    alert.alert_type,
                    alert.severity.value,
                    alert.message,
                    alert.timestamp.isoformat(),
                    json.dumps(alert.metadata)
                ))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Stored {len(alerts)} alerts")
            
        except Exception as e:
            self.logger.error(f"Error storing alerts: {e}")
    
    def log_alerts(self, alerts: List[HealthAlert]) -> None:
        """Log alerts to console."""
        for alert in alerts:
            level = {
                HealthStatus.CRITICAL: logging.CRITICAL,
                HealthStatus.UNHEALTHY: logging.ERROR,
                HealthStatus.DEGRADED: logging.WARNING,
                HealthStatus.HEALTHY: logging.INFO
            }.get(alert.severity, logging.INFO)
            
            self.logger.log(
                level,
                f"ALERT [{alert.severity.value.upper()}] "
                f"{alert.resource_type.value}:{alert.resource_id} - {alert.message}"
            )
    
    async def monitoring_loop(self) -> None:
        """Main monitoring loop."""
        self.logger.info("Starting monitoring loop")
        
        while self.running:
            try:
                # Collect metrics
                metrics = self.collect_metrics()
                
                # Store metrics
                self.store_metrics(metrics)
                
                # Analyze metrics and generate alerts
                alerts = self.analyze_metrics(metrics)
                
                # Store and log alerts
                if alerts:
                    self.store_alerts(alerts)
                    self.log_alerts(alerts)
                
                # Log summary
                healthy_count = sum(1 for m in metrics if m.status == HealthStatus.HEALTHY)
                total_count = len(metrics)
                
                if total_count > 0:
                    self.logger.debug(
                        f"Health check: {healthy_count}/{total_count} metrics healthy"
                    )
                
                # Wait for next check
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                self.logger.info("Monitoring loop cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def start(self) -> None:
        """Start the HealthMonitor daemon."""
        if self.running:
            self.logger.warning("HealthMonitor is already running")
            return
        
        self.running = True
        self.logger.info("Starting HealthMonitor daemon")
        
        try:
            await self.monitoring_loop()
        except Exception as e:
            self.logger.error(f"HealthMonitor failed: {e}")
            raise
        finally:
            self.running = False
            self.logger.info("HealthMonitor stopped")
    
    def stop(self) -> None:
        """Stop the HealthMonitor daemon."""
        if not self.running:
            self.logger.warning("HealthMonitor is not running")
            return
        
        self.running = False
        self.logger.info("HealthMonitor stop requested")
    
    def get_health_summary(self) -> Dict[str, Any]:
        """Get current health summary."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get latest metrics
            cursor.execute('''
                SELECT resource_type, resource_id, metric_name, value, status, timestamp
                FROM health_metrics
                WHERE timestamp >= datetime('now', '-5 minutes')
                ORDER BY timestamp DESC
            ''')
            
            recent_metrics = cursor.fetchall()
            
            # Get unresolved alerts
            cursor.execute('''
                SELECT resource_type, resource_id, alert_type, severity, message, timestamp
                FROM health_alerts
                WHERE resolved = FALSE
                ORDER BY timestamp DESC
            ''')
            
            active_alerts = cursor.fetchall()
            
            conn.close()
            
            # Calculate summary
            metrics_by_status = {}
            for metric in recent_metrics:
                status = metric[4]
                metrics_by_status[status] = metrics_by_status.get(status, 0) + 1
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "running": self.running,
                "monitored_agents": len(self.monitored_agents),
                "monitored_workspaces": len(self.monitored_workspaces),
                "recent_metrics_count": len(recent_metrics),
                "metrics_by_status": metrics_by_status,
                "active_alerts_count": len(active_alerts),
                "active_alerts": [
                    {
                        "resource_type": alert[0],
                        "resource_id": alert[1], 
                        "alert_type": alert[2],
                        "severity": alert[3],
                        "message": alert[4],
                        "timestamp": alert[5]
                    }
                    for alert in active_alerts
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting health summary: {e}")
            return {"error": str(e)}


async def main():
    """Main entry point for HealthMonitor daemon."""
    import argparse
    
    parser = argparse.ArgumentParser(description="HealthMonitor Daemon")
    parser.add_argument(
        "--db-path", 
        default="health_monitor.db",
        help="Database file path"
    )
    parser.add_argument(
        "--interval", 
        type=int, 
        default=30,
        help="Check interval in seconds"
    )
    parser.add_argument(
        "--alert-cooldown", 
        type=int, 
        default=300,
        help="Alert cooldown period in seconds"
    )
    parser.add_argument(
        "--log-level", 
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level"
    )
    
    args = parser.parse_args()
    
    # Create HealthMonitor
    monitor = HealthMonitor(
        db_path=args.db_path,
        check_interval=args.interval,
        alert_cooldown=args.alert_cooldown,
        log_level=args.log_level
    )
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        monitor.logger.info(f"Received signal {signum}, stopping...")
        monitor.stop()
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start monitoring
        await monitor.start()
    except KeyboardInterrupt:
        monitor.logger.info("Received KeyboardInterrupt, stopping...")
    except Exception as e:
        monitor.logger.error(f"HealthMonitor failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())