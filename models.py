from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class User(BaseModel):
    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[TaskStatus] = None
    priority: Optional[Priority] = None
    due_date: Optional[datetime] = None
    assigned_to: Optional[int] = None

class Task(TaskBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[int] = None

    class Config:
        use_enum_values = True

class TaskResponse(BaseModel):
    data: Task
    message: str

class TaskListResponse(BaseModel):
    data: List[Task]
    total: int
    page: int
    per_page: int

class ErrorResponse(BaseModel):
    error: str
    message: str
    status_code: int
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
    database_status: str
    tasks_count: int
    users_count: int

class APIInfoResponse(BaseModel):
    name: str
    version: str
    description: str
    endpoints: dict
    features: List[str]
    timestamp: datetime

class StatsResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    high_priority_tasks: int
    total_users: int
    timestamp: datetime