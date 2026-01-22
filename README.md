# Agentic Coder API

A comprehensive FastAPI application for agentic coding tasks with full CRUD operations, authentication, and best practices.

## Features

- **Task Management**: Full CRUD operations for tasks with status and priority
- **User Management**: User creation and management
- **Authentication**: JWT-based authentication
- **API Documentation**: Interactive Swagger UI and ReDoc
- **Error Handling**: Comprehensive error handling with proper HTTP status codes
- **Validation**: Input validation with Pydantic models
- **Pagination**: Paginated responses for large datasets
- **CORS Support**: Cross-origin resource sharing enabled
- **Middleware**: Request logging, security headers, and more
- **Testing**: Comprehensive test suite with pytest
- **Docker Support**: Docker and Docker Compose configurations
- **Development Tools**: Makefile for common development tasks

## Project Structure

```
ac/
├── main.py              # Main FastAPI application
├── models.py            # Pydantic models for request/response
├── middleware.py        # Custom middleware implementations
├── utils.py             # Utility functions and helpers
├── config.py            # Application configuration
├── test_api.py          # Test suite
├── requirements.txt     # Production dependencies
├── requirements-dev.txt # Development dependencies
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose configuration
├── .env.example         # Environment variables template
├── Makefile            # Development tasks
├── setup.cfg           # Development tools configuration
└── README.md           # This file
```

## Quick Start

### Using Docker (Recommended)

```bash
# Clone and run with Docker Compose
git clone <repository>
cd ac
docker-compose up --build

# Access the API
curl http://localhost:8000/health
```

### Manual Setup

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Set up environment
cp .env.example .env

# Run the application
uvicorn main:app --reload

# Or use the Makefile
make install
make run
```

## Development

### Setting up development environment

```bash
# Initialize development environment
make setup-dev

# Run tests
make test

# Run tests with coverage
make test-coverage

# Lint code
make lint

# Format code
make format

# Run all checks
make check
```

### API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## API Endpoints

### General Endpoints
- `GET /` - Welcome message with timestamp
- `GET /health` - Health check with system info
- `GET /api/v1/info` - API information and features

### Task Management Endpoints
- `GET /api/v1/tasks` - Get all tasks (with filtering and pagination)
- `POST /api/v1/tasks` - Create a new task
- `GET /api/v1/tasks/{task_id}` - Get a specific task
- `PUT /api/v1/tasks/{task_id}` - Update a task
- `DELETE /api/v1/tasks/{task_id}` - Delete a task

### User Management Endpoints
- `GET /api/v1/users` - Get all users
- `POST /api/v1/users` - Create a new user
- `GET /api/v1/users/{user_id}` - Get a specific user

### Statistics Endpoints
- `GET /api/v1/stats` - Get API statistics

## Task Model

Tasks have the following properties:
- `id`: Unique identifier
- `title`: Task title (1-200 characters)
- `description`: Task description (optional, max 1000 characters)
- `status`: Task status (pending, in_progress, completed)
- `priority`: Task priority (low, medium, high)
- `due_date`: Due date (optional)
- `assigned_to`: Assigned user ID (optional)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp
- `created_by`: Creator user ID

## User Model

Users have the following properties:
- `id`: Unique identifier
- `name`: User name (1-100 characters)
- `email`: User email (validated format)
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

## Error Handling

The API provides comprehensive error handling with:
- Proper HTTP status codes
- Detailed error messages
- Timestamp information
- Structured error responses

Example error response:
```json
{
  "success": false,
  "error": "Task not found",
  "message": "The requested task was not found",
  "status_code": 404,
  "timestamp": "2024-01-22T12:00:00"
}
```

## Authentication

The API uses JWT-based authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your-jwt-token>
```

## Environment Variables

The application can be configured using environment variables. See `.env.example` for available options.

## Testing

Run the test suite:
```bash
# Run all tests
pytest test_api.py -v

# Run with coverage
pytest test_api.py --cov=. --cov-report=html
```

## Deployment

### Production Deployment

```bash
# Build and run with Docker
docker build -t agentic-coder-api .
docker run -p 8000:8000 agentic-coder-api

# Or use Docker Compose
docker-compose -f docker-compose.prod.yml up --build
```

### Development Deployment

```bash
# Run with hot reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Or use Makefile
make run
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting: `make check`
5. Commit your changes
6. Push to the branch
7. Create a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the repository.
