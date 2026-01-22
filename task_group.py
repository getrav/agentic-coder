from typing import List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    assigned_to: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}


class TaskGroup:
    def __init__(self, id: str, name: str, description: str, 
                 tasks: Optional[List[Task]] = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None,
                 metadata: Optional[Dict[str, Any]] = None):
        self.id = id
        self.name = name
        self.description = description
        self.tasks = tasks or []
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.metadata = metadata or {}
    
    def add_task(self, task: Task) -> None:
        """Add a task to the task group."""
        task.updated_at = datetime.now()
        self.tasks.append(task)
        self.updated_at = datetime.now()
    
    def remove_task(self, task_id: str) -> bool:
        """Remove a task from the task group by ID."""
        for i, task in enumerate(self.tasks):
            if task.id == task_id:
                self.tasks.pop(i)
                self.updated_at = datetime.now()
                return True
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None
    
    def update_task_status(self, task_id: str, status: TaskStatus) -> bool:
        """Update the status of a task."""
        task = self.get_task(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.now()
            self.updated_at = datetime.now()
            return True
        return False
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status."""
        return [task for task in self.tasks if task.status == status]
    
    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to start (dependencies completed)."""
        ready_tasks = []
        for task in self.tasks:
            if task.status == TaskStatus.PENDING:
                # Check if all dependencies are completed
                dependencies_completed = True
                for dep_id in task.dependencies or []:
                    dep_task = self.get_task(dep_id)
                    if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                        dependencies_completed = False
                        break
                if dependencies_completed:
                    ready_tasks.append(task)
        return ready_tasks
    
    def get_progress(self) -> Dict[str, int]:
        """Get progress statistics for the task group."""
        total_tasks = len(self.tasks)
        if total_tasks == 0:
            return {"total": 0, "completed": 0, "in_progress": 0, "pending": 0, "blocked": 0, "failed": 0, "percentage": 0}
        
        completed = len(self.get_tasks_by_status(TaskStatus.COMPLETED))
        in_progress = len(self.get_tasks_by_status(TaskStatus.IN_PROGRESS))
        pending = len(self.get_tasks_by_status(TaskStatus.PENDING))
        blocked = len(self.get_tasks_by_status(TaskStatus.BLOCKED))
        failed = len(self.get_tasks_by_status(TaskStatus.FAILED))
        
        percentage = int((completed / total_tasks) * 100)
        
        return {
            "total": total_tasks,
            "completed": completed,
            "in_progress": in_progress,
            "pending": pending,
            "blocked": blocked,
            "failed": failed,
            "percentage": percentage
        }