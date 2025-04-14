# Task Management API
# Group information
* Syed Abdullah Hassan syehassa24@student.oulu.fi
* Muhammad Hassan Sohail. hassan.sohail@student.oulu.fi
* Uswah Batool.	 uswah.batool@student.oulu.fi
* Mathéo Morin. matheo.morin@student.oulu.fi

A RESTful API for managing tasks, projects, teams, and users. Built with Flask, PostgreSQL, and JWT authentication.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Project Setup](#project-setup)
- [Database Configuration](#database-configuration)
- [Running the Application](#running-the-application)
- [API Endpoints](#api-endpoints)
- [Testing the Application](#testing-the-application)
- [Code Quality and Analysis](#code-quality-and-analysis)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

## Introduction

This project is a Task Management API built using Flask, SQLAlchemy, and JWT for authentication. It provides endpoints for managing users, teams, projects, and tasks. The API is designed to be modular, scalable, and secure.

## Features
- **JWT Authentication**: Secure user login and token-based access control.
- **CRUD Operations**:
  - Manage users, teams, projects, and tasks.
  - Assign tasks to users and link them to projects.
- **Caching**: Optimized response times using Flask-Caching.
- **Input Validation**: JSON schema validation for all endpoints.
- **Automated Testing**: pytest for functional and integration tests.
- **Code Quality**: Integrated linters (Black, Flake8, Pylint) and security checks (Bandit).

## Prerequisites

Before you start, ensure you have the following installed on your system:
- Python 3.8 or higher
- Docker and Docker Compose (for database setup)
- Git (for cloning the repository)

## Project Setup

### Clone the Repository
```bash
git clone https://github.com/Abdullah12has/Task-management-LLM-API.git
cd task-management-api
```

### Create a Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
pip install -r requirement-quality.txt
```

## Database Configuration

The project uses PostgreSQL as the database. You can set it up using Docker or manually.

### Using Docker

#### Start the PostgreSQL Container
```bash
docker-compose up -d
```

#### Verify the Database
```bash
docker exec -it my_postgres_db bash
psql -U admin -d task_management_db
\dt  # List all tables
```

#### Stop and Remove the Container
```bash
docker stop my_postgres_db
docker rm my_postgres_db
```

### Manual Setup (Without Docker)

#### Install PostgreSQL
Follow the official PostgreSQL installation guide to set up PostgreSQL on your system.

[PostgreSQL Download Page](https://www.postgresql.org/download/)

#### Create a Database and User
```sql
CREATE USER admin WITH PASSWORD 'helloworld123';
CREATE DATABASE task_management_db OWNER admin;
```

#### Update Database Configuration
Modify the SQLALCHEMY_DATABASE_URI in app.py to match your local setup:
```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://admin:helloworld123@localhost:5432/task_management_db'
```

## Running the Application

### Initialize the Database
```bash
python app.py
```

### Run the Flask Development Server
```bash
python app.py
```

### Access the API
The API will be available at http://127.0.0.1:5000.

## API Endpoints

### Authentication

#### Login
```bash
POST /login
{
  "email": "user@example.com",
  "password": "password123"
}
```

### Users

#### Create a User
```bash
POST /users
{
  "username": "newuser",
  "email": "new@example.com",
  "password": "password123",
  "role": "member"
}
```

#### Get a User
```bash
GET /users/<user_id>
```

#### Update a User
```bash
PUT /users/<user_id>
{
  "username": "updateduser",
  "email": "updated@example.com",
  "password": "newpassword123",
  "role": "admin"
}
```

#### Delete a User
```bash
DELETE /users/<user_id>
```

### Teams

#### Create a Team
```bash
POST /teams
{
  "name": "New Team",
  "description": "Team description",
  "lead_id": "user_id"
}
```

#### Get a Team
```bash
GET /teams/<team_id>
```

#### Update a Team
```bash
PUT /teams/<team_id>
{
  "name": "Updated Team",
  "description": "Updated description",
  "lead_id": "new_user_id"
}
```

#### Delete a Team
```bash
DELETE /teams/<team_id>
```

### Projects

#### Create a Project
```bash
POST /projects
{
  "title": "New Project",
  "description": "Project description",
  "team_id": "team_id",
  "category_id": "category_id"
}
```

#### Get a Project
```bash
GET /projects/<project_id>
```

#### Update a Project
```bash
PUT /projects/<project_id>
{
  "title": "Updated Project",
  "description": "Updated description",
  "team_id": "new_team_id",
  "category_id": "new_category_id"
}
```

#### Delete a Project
```bash
DELETE /projects/<project_id>
```

### Tasks

#### Create a Task
```bash
POST /tasks
{
  "title": "New Task",
  "description": "Task description",
  "project_id": "project_id",
  "assignee_id": "user_id",
  "status": "pending",
  "priority": 3
}
```

#### Get a Task
```bash
GET /tasks/<task_id>
```

#### Update a Task
```bash
PUT /tasks/<task_id>
{
  "title": "Updated Task",
  "description": "Updated description",
  "status": "in_progress",
  "priority": 2
}
```

#### Delete a Task
```bash
DELETE /tasks/<task_id>
```

## Testing the Application

### Unit Tests

#### Run Tests
```bash
pytest --html=reports/report.html --self-contained-html
```

#### View Test Report
Open `reports/report.html` in a web browser.

## Code Quality and Analysis

The project includes scripts for code quality checks:
- **Black**: Code formatter
- **isort**: Import sorter
- **Flake8**: Linter
- **Pylint**: Static analysis
- **Bandit**: Security analysis
- **MyPy**: Type checking

To automatically fix formatting issues:
```bash
python code_quality.py --fix
```

## Project Structure
```
.
├── app.py                # Application entry point
├── models/               # Database models
├── routes/               # API endpoints
├── schemas/              # Request/response validation schemas
├── utils/                # Utility functions and helpers
├── tests/                # Test suites
├── requirements.txt      # Project dependencies
├── requirements-test.txt # Testing dependencies
├── requirement-quality.txt # Code quality dependencies
└── docker-compose.yml    # Docker configuration
```

## Troubleshooting

### Database Connection Issues
- Ensure the PostgreSQL service is running.
- Verify the database credentials in app.py.

### Missing Dependencies
- Reinstall dependencies using pip install -r requirements.txt.

### Test Failures
- Check the test output for specific error messages.
- Ensure the test database is properly initialized.

### Code Quality Failures
- Review the generated reports for detailed feedback.
- Run python code_quality.py --fix to automatically correct formatting issues.

### Test Coverage 
```bash
coverage report -m
```


### Test Coverage HTML Report
```bash
 coverage html
```


### Hypermedia Design

```mermaid
stateDiagram-v2
    [*] --> Users: GET /users
    Users --> User: GET /users/{id}
    User --> UpdateUser: PUT /users/{id}
    UpdateUser --> User
    User --> [*]: DELETE /users/{id}
    
    [*] --> Teams: GET /teams
    Teams --> Team: GET /teams/{id}
    Teams --> CreateTeam: POST /teams
    CreateTeam --> Team
    Team --> UpdateTeam: PUT /teams/{id}
    UpdateTeam --> Team
    Team --> [*]: DELETE /teams/{id}
    Team --> TeamMembers: GET /teams/{id}/members
    TeamMembers --> CreateTeamMember: POST /teams/{id}/members
    CreateTeamMember --> TeamMember
    TeamMember --> UpdateTeamMember: PUT /teams/{id}/members/{user_id}
    UpdateTeamMember --> TeamMember
    TeamMember --> [*]: DELETE /teams/{id}/members/{user_id}
    
    [*] --> Projects: GET /projects
    Projects --> Project: GET /projects/{id}
    Projects --> CreateProject: POST /projects
    CreateProject --> Project
    Project --> UpdateProject: PUT /projects/{id}
    UpdateProject --> Project
    Project --> [*]: DELETE /projects/{id}
    Project --> Tasks: GET /tasks?project_id={id}
    Tasks --> Task: GET /tasks/{id}
    
    [*] --> Tasks: GET /tasks
    Tasks --> Task: GET /tasks/{id}
    Tasks --> CreateTask: POST /tasks
    CreateTask --> Task
    Task --> UpdateTask: PUT /tasks/{id}
    UpdateTask --> Task
    Task --> [*]: DELETE /tasks/{id}
    
    %% Optional connections to show better connectedness
    User --> Teams: GET /users/{id}/teams
    Task --> Project: GET /projects/{id}

```
