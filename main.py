from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
import uvicorn
from datetime import datetime
import logging

from models import (
    Task, TaskCreate, TaskUpdate, User,
    TaskStatus, Priority, TaskResponse, TaskListResponse,
    ErrorResponse, HealthResponse, APIInfoResponse, StatsResponse
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Agentic Coder API",
    description="A comprehensive FastAPI application for agentic coding tasks",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

tasks_db = []
users_db = []

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simple authentication - in real app, validate JWT token"""
    return {"user_id": 1, "username": "demo_user"}

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}")
    error_response = ErrorResponse(
        error="Internal Server Error",
        message=str(exc),
        status_code=500,
        timestamp=datetime.now()
    )
    return JSONResponse(
        status_code=500,
        content=error_response.dict()
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP exception handler"""
    error_response = ErrorResponse(
        error=exc.detail,
        message="HTTP Error occurred",
        status_code=exc.status_code,
        timestamp=datetime.now()
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.dict()
    )

@app.get("/", response_model=Dict[str, Any], tags=["General"])
async def root():
    """Root endpoint returning welcome message"""
    return {
        "message": "Welcome to Agentic Coder API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint with system info"""
    return HealthResponse(
        status="healthy",
        service="Agentic Coder API",
        timestamp=datetime.now(),
        database_status="connected",
        tasks_count=len(tasks_db),
        users_count=len(users_db)
    )

@app.get("/api/v1/info", response_model=APIInfoResponse, tags=["General"])
async def api_info():
    """API information endpoint"""
    return APIInfoResponse(
        name="Agentic Coder API",
        version="1.0.0",
        description="A comprehensive FastAPI application for agentic coding tasks",
        endpoints={
            "general": ["/", "/health", "/api/v1/info"],
            "tasks": [
                "GET /api/v1/tasks",
                "POST /api/v1/tasks", 
                "GET /api/v1/tasks/{task_id}",
                "PUT /api/v1/tasks/{task_id}",
                "DELETE /api/v1/tasks/{task_id}"
            ],
            "users": [
                "GET /api/v1/users",
                "POST /api/v1/users",
                "GET /api/v1/users/{user_id}"
            ],
            "stats": [
                "GET /api/v1/stats"
            ]
        },
        features=[
            "Task Management",
            "User Management", 
            "Authentication",
            "CORS Support",
            "API Documentation",
            "Error Handling",
            "Logging",
            "Response Models"
        ],
        timestamp=datetime.now()
    )

# Task Management Endpoints
@app.get("/api/v1/tasks", response_model=TaskListResponse, tags=["Tasks"])
async def get_tasks(
    status: Optional[TaskStatus] = None,
    priority: Optional[Priority] = None,
    page: int = 1,
    per_page: int = 10,
    user: dict = Depends(get_current_user)
):
    """Get all tasks with optional filtering and pagination"""
    tasks = tasks_db
    
    # Apply filters
    if status:
        tasks = [task for task in tasks if task.status == status]
    if priority:
        tasks = [task for task in tasks if task.priority == priority]
    
    # Apply pagination
    total = len(tasks)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_tasks = tasks[start:end]
    
    return TaskListResponse(
        data=paginated_tasks,
        total=total,
        page=page,
        per_page=per_page
    )

@app.post("/api/v1/tasks", response_model=TaskResponse, tags=["Tasks"])
async def create_task(
    task: TaskCreate,
    user: dict = Depends(get_current_user)
):
    """Create a new task"""
    task_id = (max([t.id for t in tasks_db]) + 1) if tasks_db else 1
    new_task = Task(
        id=task_id,
        **task.dict(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
        created_by=user["user_id"]
    )
    tasks_db.append(new_task)
    
    return TaskResponse(
        data=new_task,
        message="Task created successfully"
    )

@app.get("/api/v1/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def get_task(
    task_id: int,
    user: dict = Depends(get_current_user)
):
    """Get a specific task by ID"""
    for task in tasks_db:
        if task.id == task_id:
            return TaskResponse(
                data=task,
                message="Task retrieved successfully"
            )
    raise HTTPException(status_code=404, detail="Task not found")

@app.put("/api/v1/tasks/{task_id}", response_model=TaskResponse, tags=["Tasks"])
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    user: dict = Depends(get_current_user)
):
    """Update a task"""
    for task in tasks_db:
        if task.id == task_id:
            update_data = task_update.dict(exclude_unset=True)
            for field, value in update_data.items():
                setattr(task, field, value)
            task.updated_at = datetime.now()
            
            return TaskResponse(
                data=task,
                message="Task updated successfully"
            )
    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/api/v1/tasks/{task_id}", tags=["Tasks"])
async def delete_task(
    task_id: int,
    user: dict = Depends(get_current_user)
):
    """Delete a task"""
    for i, task in enumerate(tasks_db):
        if task.id == task_id:
            del tasks_db[i]
            return {
                "message": f"Task {task_id} deleted successfully",
                "task_id": task_id
            }
    raise HTTPException(status_code=404, detail="Task not found")

# User Management Endpoints
@app.get("/api/v1/users", tags=["Users"])
async def get_users(user: dict = Depends(get_current_user)):
    """Get all users"""
    return {"data": users_db, "count": len(users_db)}

@app.post("/api/v1/users", tags=["Users"])
async def create_user(
    user_data: User,
    user: dict = Depends(get_current_user)
):
    """Create a new user"""
    user_data.id = (max([u.id for u in users_db]) + 1) if users_db else 1
    user_data.created_at = datetime.now()
    user_data.updated_at = datetime.now()
    users_db.append(user_data)
    
    return {
        "data": user_data,
        "message": "User created successfully"
    }

@app.get("/api/v1/users/{user_id}", tags=["Users"])
async def get_user(
    user_id: int,
    user: dict = Depends(get_current_user)
):
    """Get a specific user by ID"""
    for user_obj in users_db:
        if user_obj.id == user_id:
            return {"data": user_obj, "message": "User retrieved successfully"}
    raise HTTPException(status_code=404, detail="User not found")

# Statistics Endpoints
@app.get("/api/v1/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_stats(user: dict = Depends(get_current_user)):
    """Get API statistics"""
    total_tasks = len(tasks_db)
    completed_tasks = len([t for t in tasks_db if t.status == TaskStatus.COMPLETED])
    pending_tasks = len([t for t in tasks_db if t.status == TaskStatus.PENDING])
    in_progress_tasks = len([t for t in tasks_db if t.status == TaskStatus.IN_PROGRESS])
    high_priority_tasks = len([t for t in tasks_db if t.priority == Priority.HIGH])
    
    return StatsResponse(
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        in_progress_tasks=in_progress_tasks,
        high_priority_tasks=high_priority_tasks,
        total_users=len(users_db),
        timestamp=datetime.now()
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)