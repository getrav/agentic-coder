import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "timestamp" in data

def test_health_check_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "Agentic Coder API"
    assert "tasks_count" in data
    assert "users_count" in data

def test_api_info_endpoint():
    """Test the API info endpoint"""
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Agentic Coder API"
    assert data["version"] == "1.0.0"
    assert "endpoints" in data
    assert "features" in data

def test_create_task():
    """Test creating a new task"""
    task_data = {
        "title": "Test Task",
        "description": "This is a test task",
        "status": "pending",
        "priority": "medium"
    }
    
    response = client.post("/api/v1/tasks", json=task_data)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["title"] == task_data["title"]
    assert data["data"]["description"] == task_data["description"]
    assert data["data"]["id"] is not None

def test_get_tasks():
    """Test getting all tasks"""
    # First create a task
    task_data = {
        "title": "Test Task for Get",
        "description": "This is a test task"
    }
    client.post("/api/v1/tasks", json=task_data)
    
    # Then get all tasks
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)
    assert "total" in data
    assert "page" in data
    assert "per_page" in data

def test_get_task_by_id():
    """Test getting a specific task by ID"""
    # First create a task
    task_data = {
        "title": "Test Task for Get by ID",
        "description": "This is a test task"
    }
    create_response = client.post("/api/v1/tasks", json=task_data)
    task_id = create_response.json()["data"]["id"]
    
    # Then get the task by ID
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == task_id
    assert data["data"]["title"] == task_data["title"]

def test_update_task():
    """Test updating a task"""
    # First create a task
    task_data = {
        "title": "Test Task for Update",
        "description": "This is a test task"
    }
    create_response = client.post("/api/v1/tasks", json=task_data)
    task_id = create_response.json()["data"]["id"]
    
    # Then update the task
    update_data = {
        "title": "Updated Test Task",
        "status": "completed"
    }
    response = client.put(f"/api/v1/tasks/{task_id}", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["title"] == update_data["title"]
    assert data["data"]["status"] == update_data["status"]

def test_delete_task():
    """Test deleting a task"""
    # First create a task
    task_data = {
        "title": "Test Task for Delete",
        "description": "This is a test task"
    }
    create_response = client.post("/api/v1/tasks", json=task_data)
    task_id = create_response.json()["data"]["id"]
    
    # Then delete the task
    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert f"Task {task_id} deleted successfully" in response.json()["message"]
    
    # Verify the task is deleted
    get_response = client.get(f"/api/v1/tasks/{task_id}")
    assert get_response.status_code == 404

def test_get_nonexistent_task():
    """Test getting a non-existent task"""
    response = client.get("/api/v1/tasks/999")
    assert response.status_code == 404

def test_update_nonexistent_task():
    """Test updating a non-existent task"""
    update_data = {
        "title": "Updated Non-existent Task"
    }
    response = client.put("/api/v1/tasks/999", json=update_data)
    assert response.status_code == 404

def test_delete_nonexistent_task():
    """Test deleting a non-existent task"""
    response = client.delete("/api/v1/tasks/999")
    assert response.status_code == 404

def test_create_user():
    """Test creating a new user"""
    user_data = {
        "name": "Test User",
        "email": "test@example.com"
    }
    
    response = client.post("/api/v1/users", json=user_data)
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == user_data["name"]
    assert data["data"]["email"] == user_data["email"]
    assert data["data"]["id"] is not None

def test_get_users():
    """Test getting all users"""
    # First create a user
    user_data = {
        "name": "Test User for Get",
        "email": "test2@example.com"
    }
    client.post("/api/v1/users", json=user_data)
    
    # Then get all users
    response = client.get("/api/v1/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)
    assert "count" in data

def test_get_user_by_id():
    """Test getting a specific user by ID"""
    # First create a user
    user_data = {
        "name": "Test User for Get by ID",
        "email": "test3@example.com"
    }
    create_response = client.post("/api/v1/users", json=user_data)
    user_id = create_response.json()["data"]["id"]
    
    # Then get the user by ID
    response = client.get(f"/api/v1/users/{user_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == user_id
    assert data["data"]["name"] == user_data["name"]

def test_get_stats():
    """Test getting API statistics"""
    response = client.get("/api/v1/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_tasks" in data
    assert "completed_tasks" in data
    assert "pending_tasks" in data
    assert "in_progress_tasks" in data
    assert "high_priority_tasks" in data
    assert "total_users" in data
    assert "timestamp" in data

def test_task_validation():
    """Test task validation"""
    # Test empty title
    response = client.post("/api/v1/tasks", json={"title": ""})
    assert response.status_code == 422
    
    # Test title too long
    long_title = "x" * 201
    response = client.post("/api/v1/tasks", json={"title": long_title})
    assert response.status_code == 422

def test_user_validation():
    """Test user validation"""
    # Test empty name
    response = client.post("/api/v1/users", json={"name": "", "email": "test@example.com"})
    assert response.status_code == 422
    
    # Test invalid email
    response = client.post("/api/v1/users", json={"name": "Test", "email": "invalid-email"})
    assert response.status_code == 422

if __name__ == "__main__":
    pytest.main([__file__])