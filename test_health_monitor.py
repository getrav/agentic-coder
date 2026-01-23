#!/usr/bin/env python3
"""
Test suite for HealthMonitor daemon.
"""

import unittest
import asyncio
import tempfile
import os
from pathlib import Path
from datetime import datetime

from src.agentic_coder.health_monitor import (
    HealthMonitor, 
    HealthStatus, 
    ResourceType, 
    HealthMetric, 
    HealthAlert
)


class TestHealthMonitor(unittest.TestCase):
    """Test cases for HealthMonitor."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_health_monitor.db")
        self.monitor = HealthMonitor(
            db_path=self.db_path,
            check_interval=1,
            alert_cooldown=1,
            log_level="DEBUG"
        )
    
    def tearDown(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_health_monitor_initialization(self):
        """Test HealthMonitor initialization."""
        self.assertIsNotNone(self.monitor)
        self.assertEqual(self.monitor.db_path, self.db_path)
        self.assertEqual(self.monitor.check_interval, 1)
        self.assertEqual(self.monitor.alert_cooldown, 1)
        self.assertFalse(self.monitor.running)
    
    def test_database_initialization(self):
        """Test database initialization."""
        # Database should be created during initialization
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check if tables exist
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check health_metrics table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='health_metrics'")
        self.assertIsNotNone(cursor.fetchone())
        
        # Check health_alerts table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='health_alerts'")
        self.assertIsNotNone(cursor.fetchone())
        
        conn.close()
    
    def test_health_metric_creation(self):
        """Test HealthMetric creation and status calculation."""
        metric = HealthMetric(
            resource_type=ResourceType.MEMORY,
            resource_id="test",
            metric_name="memory_usage",
            value=85.0,
            threshold_warning=80.0,
            threshold_critical=95.0,
            unit="%"
        )
        
        self.assertEqual(metric.resource_type, ResourceType.MEMORY)
        self.assertEqual(metric.resource_id, "test")
        self.assertEqual(metric.metric_name, "memory_usage")
        self.assertEqual(metric.value, 85.0)
        self.assertEqual(metric.status, HealthStatus.UNHEALTHY)
    
    def test_health_metric_status_calculation(self):
        """Test HealthMetric status calculation with different values."""
        # Healthy metric
        healthy_metric = HealthMetric(
            resource_type=ResourceType.CPU,
            resource_id="test",
            metric_name="cpu_usage",
            value=50.0,
            threshold_warning=80.0,
            threshold_critical=95.0
        )
        self.assertEqual(healthy_metric.status, HealthStatus.HEALTHY)
        
        # Unhealthy metric
        unhealthy_metric = HealthMetric(
            resource_type=ResourceType.CPU,
            resource_id="test",
            metric_name="cpu_usage",
            value=85.0,
            threshold_warning=80.0,
            threshold_critical=95.0
        )
        self.assertEqual(unhealthy_metric.status, HealthStatus.UNHEALTHY)
        
        # Critical metric
        critical_metric = HealthMetric(
            resource_type=ResourceType.CPU,
            resource_id="test",
            metric_name="cpu_usage",
            value=97.0,
            threshold_warning=80.0,
            threshold_critical=95.0
        )
        self.assertEqual(critical_metric.status, HealthStatus.CRITICAL)
    
    def test_collect_system_metrics(self):
        """Test system metrics collection."""
        metrics = self.monitor._collect_system_metrics()
        
        # Should return a list of metrics
        self.assertIsInstance(metrics, list)
        
        # Each item should be a HealthMetric
        for metric in metrics:
            self.assertIsInstance(metric, HealthMetric)
    
    def test_collect_agent_metrics(self):
        """Test agent metrics collection."""
        # Add an agent to monitor
        self.monitor.add_agent_monitor("test_agent")
        
        metrics = self.monitor._collect_agent_metrics("test_agent")
        
        # Should return a list of metrics
        self.assertIsInstance(metrics, list)
        
        # Each item should be a HealthMetric
        for metric in metrics:
            self.assertIsInstance(metric, HealthMetric)
    
    def test_collect_workspace_metrics(self):
        """Test workspace metrics collection."""
        # Add a workspace to monitor
        self.monitor.add_workspace_monitor("test_workspace")
        
        metrics = self.monitor._collect_workspace_metrics("test_workspace")
        
        # Should return a list of metrics
        self.assertIsInstance(metrics, list)
        
        # Each item should be a HealthMetric
        for metric in metrics:
            self.assertIsInstance(metric, HealthMetric)
    
    def test_store_metrics(self):
        """Test storing metrics in database."""
        # Create test metrics
        metrics = [
            HealthMetric(
                resource_type=ResourceType.MEMORY,
                resource_id="test",
                metric_name="memory_usage",
                value=50.0,
                threshold_warning=80.0,
                threshold_critical=95.0,
                unit="%"
            ),
            HealthMetric(
                resource_type=ResourceType.CPU,
                resource_id="test",
                metric_name="cpu_usage",
                value=30.0,
                threshold_warning=80.0,
                threshold_critical=95.0,
                unit="%"
            )
        ]
        
        # Store metrics
        self.monitor.store_metrics(metrics)
        
        # Verify metrics were stored
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM health_metrics")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        self.assertEqual(count, 2)
    
    def test_analyze_metrics_no_alerts(self):
        """Test analyzing metrics that don't trigger alerts."""
        # Create healthy metrics
        metrics = [
            HealthMetric(
                resource_type=ResourceType.MEMORY,
                resource_id="test",
                metric_name="memory_usage",
                value=50.0,
                threshold_warning=80.0,
                threshold_critical=95.0,
                unit="%"
            )
        ]
        
        alerts = self.monitor.analyze_metrics(metrics)
        
        # Should be no alerts
        self.assertEqual(len(alerts), 0)
    
    def test_analyze_metrics_with_alerts(self):
        """Test analyzing metrics that trigger alerts."""
        # Create unhealthy metric
        metrics = [
            HealthMetric(
                resource_type=ResourceType.MEMORY,
                resource_id="test",
                metric_name="memory_usage",
                value=85.0,
                threshold_warning=80.0,
                threshold_critical=95.0,
                unit="%"
            )
        ]
        
        alerts = self.monitor.analyze_metrics(metrics)
        
        # Should have one alert
        self.assertEqual(len(alerts), 1)
        
        # Check alert properties
        alert = alerts[0]
        self.assertIsInstance(alert, HealthAlert)
        self.assertEqual(alert.resource_type, ResourceType.MEMORY)
        self.assertEqual(alert.resource_id, "test")
        self.assertEqual(alert.severity, HealthStatus.UNHEALTHY)
    
    def test_store_alerts(self):
        """Test storing alerts in database."""
        # Create test alert
        alerts = [
            HealthAlert(
                resource_type=ResourceType.MEMORY,
                resource_id="test",
                alert_type="memory_usage_high",
                severity=HealthStatus.UNHEALTHY,
                message="Memory usage is too high",
                metadata={"current_value": 85.0}
            )
        ]
        
        # Store alerts
        self.monitor.store_alerts(alerts)
        
        # Verify alerts were stored
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM health_alerts")
        count = cursor.fetchone()[0]
        
        conn.close()
        
        self.assertEqual(count, 1)
    
    def test_get_health_summary(self):
        """Test getting health summary."""
        # Add some monitors
        self.monitor.add_agent_monitor("agent1")
        self.monitor.add_workspace_monitor("workspace1")
        
        # Get summary
        summary = self.monitor.get_health_summary()
        
        # Check summary structure
        self.assertIn("timestamp", summary)
        self.assertIn("running", summary)
        self.assertIn("monitored_agents", summary)
        self.assertIn("monitored_workspaces", summary)
        self.assertIn("recent_metrics_count", summary)
        self.assertIn("metrics_by_status", summary)
        self.assertIn("active_alerts_count", summary)
        self.assertIn("active_alerts", summary)
        
        # Check values
        self.assertEqual(summary["monitored_agents"], 1)
        self.assertEqual(summary["monitored_workspaces"], 1)
        self.assertFalse(summary["running"])
    
    def test_agent_monitor_management(self):
        """Test adding and removing agent monitors."""
        # Initially no agents
        self.assertEqual(len(self.monitor.monitored_agents), 0)
        
        # Add agent
        self.monitor.add_agent_monitor("test_agent")
        self.assertEqual(len(self.monitor.monitored_agents), 1)
        self.assertIn("test_agent", self.monitor.monitored_agents)
        
        # Remove agent
        self.monitor.remove_agent_monitor("test_agent")
        self.assertEqual(len(self.monitor.monitored_agents), 0)
        self.assertNotIn("test_agent", self.monitor.monitored_agents)
    
    def test_workspace_monitor_management(self):
        """Test adding and removing workspace monitors."""
        # Initially no workspaces
        self.assertEqual(len(self.monitor.monitored_workspaces), 0)
        
        # Add workspace
        self.monitor.add_workspace_monitor("test_workspace")
        self.assertEqual(len(self.monitor.monitored_workspaces), 1)
        self.assertIn("test_workspace", self.monitor.monitored_workspaces)
        
        # Remove workspace
        self.monitor.remove_workspace_monitor("test_workspace")
        self.assertEqual(len(self.monitor.monitored_workspaces), 0)
        self.assertNotIn("test_workspace", self.monitor.monitored_workspaces)


class TestHealthMetric(unittest.TestCase):
    """Test cases for HealthMetric class."""
    
    def test_health_metric_properties(self):
        """Test HealthMetric properties."""
        metric = HealthMetric(
            resource_type=ResourceType.MEMORY,
            resource_id="test",
            metric_name="memory_usage",
            value=85.0,
            threshold_warning=80.0,
            threshold_critical=95.0,
            unit="%"
        )
        
        self.assertEqual(metric.resource_type, ResourceType.MEMORY)
        self.assertEqual(metric.resource_id, "test")
        self.assertEqual(metric.metric_name, "memory_usage")
        self.assertEqual(metric.value, 85.0)
        self.assertEqual(metric.threshold_warning, 80.0)
        self.assertEqual(metric.threshold_critical, 95.0)
        self.assertEqual(metric.unit, "%")
        self.assertEqual(metric.status, HealthStatus.UNHEALTHY)


class TestHealthAlert(unittest.TestCase):
    """Test cases for HealthAlert class."""
    
    def test_health_alert_properties(self):
        """Test HealthAlert properties."""
        alert = HealthAlert(
            resource_type=ResourceType.MEMORY,
            resource_id="test",
            alert_type="memory_usage_high",
            severity=HealthStatus.UNHEALTHY,
            message="Memory usage is too high",
            metadata={"current_value": 85.0}
        )
        
        self.assertEqual(alert.resource_type, ResourceType.MEMORY)
        self.assertEqual(alert.resource_id, "test")
        self.assertEqual(alert.alert_type, "memory_usage_high")
        self.assertEqual(alert.severity, HealthStatus.UNHEALTHY)
        self.assertEqual(alert.message, "Memory usage is too high")
        self.assertEqual(alert.metadata, {"current_value": 85.0})


if __name__ == "__main__":
    # Run the tests
    unittest.main(verbosity=2)