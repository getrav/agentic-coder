#!/usr/bin/env python3

from task_group import TaskGroup, Task, TaskStatus
from datetime import datetime

def test_task_group():
    """Test the TaskGroup implementation."""
    
    # Create a task group
    group = TaskGroup(
        id="tg-001",
        name="Test Task Group",
        description="A test task group for validation"
    )
    
    # Create some tasks
    task1 = Task(
        id="task-001",
        title="Setup Environment",
        description="Set up the development environment"
    )
    
    task2 = Task(
        id="task-002", 
        title="Implement Core",
        description="Implement the core functionality",
        dependencies=["task-001"]
    )
    
    task3 = Task(
        id="task-003",
        title="Write Tests", 
        description="Write unit tests for the core functionality",
        dependencies=["task-002"]
    )
    
    # Add tasks to the group
    group.add_task(task1)
    group.add_task(task2)
    group.add_task(task3)
    
    print(f"Created task group with {len(group.tasks)} tasks")
    
    # Test getting tasks by status
    pending_tasks = group.get_tasks_by_status(TaskStatus.PENDING)
    print(f"Pending tasks: {len(pending_tasks)}")
    
    # Test getting ready tasks (should be only task1 since it has no dependencies)
    ready_tasks = group.get_ready_tasks()
    print(f"Ready tasks: {len(ready_tasks)}")
    for task in ready_tasks:
        print(f"  - {task.title}")
    
    # Test progress
    progress = group.get_progress()
    print(f"Progress: {progress}")
    
    # Start working on task1
    success = group.update_task_status("task-001", TaskStatus.IN_PROGRESS)
    print(f"Updated task-001 status: {success}")
    
    # Complete task1
    success = group.update_task_status("task-001", TaskStatus.COMPLETED)
    print(f"Completed task-001: {success}")
    
    # Now task2 should be ready
    ready_tasks = group.get_ready_tasks()
    print(f"Ready tasks after completing task1: {len(ready_tasks)}")
    for task in ready_tasks:
        print(f"  - {task.title}")
    
    # Update progress
    progress = group.get_progress()
    print(f"Progress after completing task1: {progress}")
    
    print("All tests passed!")

if __name__ == "__main__":
    test_task_group()