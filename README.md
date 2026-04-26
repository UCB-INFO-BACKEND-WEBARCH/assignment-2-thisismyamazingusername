# Assignment 2: Production Task Manager API

## Overview

In this assignment, you will build a production-ready Task Manager API with persistent database storage, input validation, background task processing, and Docker containerization.

**This is a standalone assignment**—you will build this from scratch, not modify Assignment 1.

**Released:** Week 8
**Due:** Week 11, before Friday lab

---

## Learning Objectives

By completing this assignment, you will demonstrate your ability to:

- Design and implement database models with SQLAlchemy
- Create model relationships (one-to-many)
- Validate API input using Marshmallow schemas
- Process background tasks with Redis and rq
- Containerize a full-stack application with Docker Compose

---

## What You'll Build

A Flask application with:
- **PostgreSQL database** for persistent storage
- **SQLAlchemy ORM** for database models
- **Marshmallow schemas** for input validation
- **Redis + rq** for background task processing
- **Docker Compose** to run the entire stack

---

## Data Models

### Task

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | Integer | Primary key, auto-generated |
| `title` | String(100) | Required, max 100 characters |
| `description` | Text | Optional, max 500 characters |
| `completed` | Boolean | Default: `false` |
| `due_date` | DateTime | Optional, ISO 8601 format |
| `category_id` | Integer | Foreign key to Category (optional) |
| `created_at` | DateTime | Auto-generated |
| `updated_at` | DateTime | Auto-updated on changes |

### Category

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | Integer | Primary key, auto-generated |
| `name` | String(50) | Required, unique, max 50 characters |
| `color` | String(7) | Optional, hex color code (e.g., `#FF5733`) |

**Relationship:** A Category has many Tasks. A Task belongs to one Category (optional).

---

## API Specification

### Task Endpoints

#### GET /tasks

Returns a list of all tasks.

**Query Parameters:**
- `completed` (optional): Filter by completion status (`true` or `false`)

**Response:** `200 OK`
```json
{
    "tasks": [
        {
            "id": 1,
            "title": "Finish project",
            "description": "Complete the API assignment",
            "completed": false,
            "due_date": "2026-03-15T17:00:00Z",
            "category_id": 2,
            "category": {
                "id": 2,
                "name": "School",
                "color": "#4A90D9"
            },
            "created_at": "2026-03-01T10:00:00Z",
            "updated_at": "2026-03-01T10:00:00Z"
        }
    ]
}
```

**Example with filter:**
```
GET /tasks?completed=false
```

---

#### GET /tasks/:id

Returns a single task with its category information.

**Response (success):** `200 OK`

**Response (not found):** `404 Not Found`
```json
{
    "error": "Task not found"
}
```

---

#### POST /tasks

Creates a new task with validation.

**Request Body:**
```json
{
    "title": "New task",
    "description": "Task details",
    "due_date": "2026-03-20T09:00:00Z",
    "category_id": 1
}
```

**Response (success):** `201 Created`
```json
{
    "task": {
        "id": 5,
        "title": "New task",
        "description": "Task details",
        "completed": false,
        "due_date": "2026-03-20T09:00:00Z",
        "category_id": 1,
        "created_at": "2026-03-10T12:00:00Z",
        "updated_at": "2026-03-10T12:00:00Z"
    },
    "notification_queued": true
}
```

**Response (validation error):** `400 Bad Request`
```json
{
    "errors": {
        "title": ["Length must be between 1 and 100."],
        "description": ["Length must not exceed 500."]
    }
}
```

**Validation Rules:**
- `title`: Required, 1-100 characters
- `description`: Optional, max 500 characters
- `due_date`: Optional, must be valid ISO 8601 format
- `category_id`: Optional, must reference an existing category

---

#### PUT /tasks/:id

Updates an existing task with validation.

**Request Body:** (any subset of fields)
```json
{
    "completed": true
}
```

**Response (success):** `200 OK` with updated task

**Response (not found):** `404 Not Found`

**Response (validation error):** `400 Bad Request`

---

#### DELETE /tasks/:id

Deletes a task.

**Response (success):** `200 OK`
```json
{
    "message": "Task deleted"
}
```

**Response (not found):** `404 Not Found`

---

### Category Endpoints

#### GET /categories

Returns all categories with the count of tasks in each.

**Response:** `200 OK`
```json
{
    "categories": [
        {
            "id": 1,
            "name": "Work",
            "color": "#FF5733",
            "task_count": 5
        },
        {
            "id": 2,
            "name": "Personal",
            "color": "#33FF57",
            "task_count": 3
        }
    ]
}
```

---

#### GET /categories/:id

Returns a single category with all its tasks.

**Response (success):** `200 OK`
```json
{
    "id": 1,
    "name": "Work",
    "color": "#FF5733",
    "tasks": [
        {
            "id": 1,
            "title": "Finish report",
            "completed": false
        },
        {
            "id": 3,
            "title": "Email client",
            "completed": true
        }
    ]
}
```

**Response (not found):** `404 Not Found`

---

#### POST /categories

Creates a new category.

**Request Body:**
```json
{
    "name": "Health",
    "color": "#FF0000"
}
```

**Response (success):** `201 Created`

**Validation Rules:**
- `name`: Required, 1-50 characters, must be unique
- `color`: Optional, must be valid hex format (`#RRGGBB`)

**Response (validation error):** `400 Bad Request`
```json
{
    "errors": {
        "name": ["Category with this name already exists."]
    }
}
```

---

#### DELETE /categories/:id

Deletes a category. **Cannot delete a category that has tasks.**

**Response (success):** `200 OK`
```json
{
    "message": "Category deleted"
}
```

**Response (has tasks):** `400 Bad Request`
```json
{
    "error": "Cannot delete category with existing tasks. Move or delete tasks first."
}
```

**Response (not found):** `404 Not Found`

---

## Background Task: Due Date Notifications

When a task is created with a `due_date` that is **within 24 hours** of the current time, your application should queue a background job.

The background job should:
1. Wait 5 seconds (simulating sending a notification)
2. Log a message: `Reminder: Task 'TASK_TITLE' is due soon!`

**Requirements:**
- Use Redis as the message broker
- Use rq (Redis Queue) for job processing
- The POST /tasks response should include `"notification_queued": true` when a job is queued, or `"notification_queued": false` when no job is needed

**When to queue a notification:**
- Task has a `due_date`
- `due_date` is in the future
- `due_date` is within 24 hours from now

**When NOT to queue:**
- Task has no `due_date`
- `due_date` is more than 24 hours away
- `due_date` is in the past

---

## Docker Compose Requirements

Your application must run with Docker Compose. Create a `docker-compose.yml` that defines:

| Service | Image/Build | Purpose |
|---------|-------------|---------|
| `app` | Your Flask app | The main API server |
| `db` | `postgres:15` | PostgreSQL database |
| `redis` | `redis:7` | Message broker for background tasks |
| `worker` | Your Flask app | rq worker process |

**The entire stack should start with:**
```bash
docker-compose up --build
```

**Requirements:**
- App should wait for database to be ready before starting
- Database data should persist using a Docker volume
- Environment variables should be used for configuration (database URL, Redis URL)
- API should be accessible on a configured port (e.g., 5000)

---

## Project Structure

Suggested project structure:

```
assignment2/
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Marshmallow schemas
│   ├── routes/
│   │   ├── tasks.py       # Task endpoints# Assignment 2: Production Task Manager API

## Overview

In this assignment, you will build a production-ready Task Manager API with persistent database storage, input validation, background task processing, and Docker containerization.

**This is a standalone assignment**—you will build this from scratch, not modify Assignment 1.

**Released:** Week 8
**Due:** Week 11, before Friday lab

---

## Learning Objectives

By completing this assignment, you will demonstrate your ability to:

- Design and implement database models with SQLAlchemy
- Create model relationships (one-to-many)
- Validate API input using Marshmallow schemas
- Process background tasks with Redis and rq
- Containerize a full-stack application with Docker Compose

---

## What You'll Build

A Flask application with:
- **PostgreSQL database** for persistent storage
- **SQLAlchemy ORM** for database models
- **Marshmallow schemas** for input validation
- **Redis + rq** for background task processing
- **Docker Compose** to run the entire stack

---

## Data Models

### Task

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | Integer | Primary key, auto-generated |
| `title` | String(100) | Required, max 100 characters |
| `description` | Text | Optional, max 500 characters |
| `completed` | Boolean | Default: `false` |
| `due_date` | DateTime | Optional, ISO 8601 format |
| `category_id` | Integer | Foreign key to Category (optional) |
| `created_at` | DateTime | Auto-generated |
| `updated_at` | DateTime | Auto-updated on changes |

### Category

| Field | Type | Constraints |
|-------|------|-------------|
| `id` | Integer | Primary key, auto-generated |
| `name` | String(50) | Required, unique, max 50 characters |
| `color` | String(7) | Optional, hex color code (e.g., `#FF5733`) |

**Relationship:** A Category has many Tasks. A Task belongs to one Category (optional).

---

## API Specification

### Task Endpoints

#### GET /tasks

Returns a list of all tasks.

**Query Parameters:**
- `completed` (optional): Filter by completion status (`true` or `false`)

**Response:** `200 OK`
```json
{
    "tasks": [
        {
            "id": 1,
            "title": "Finish project",
            "description": "Complete the API assignment",
            "completed": false,
            "due_date": "2026-03-15T17:00:00Z",
            "category_id": 2,
            "category": {
                "id": 2,
                "name": "School",
                "color": "#4A90D9"
            },
            "created_at": "2026-03-01T10:00:00Z",
            "updated_at": "2026-03-01T10:00:00Z"
        }
    ]
}
```

**Example with filter:**
```
GET /tasks?completed=false
```

---

#### GET /tasks/:id

Returns a single task with its category information.

**Response (success):** `200 OK`

**Response (not found):** `404 Not Found`
```json
{
    "error": "Task not found"
}
```

---

#### POST /tasks

Creates a new task with validation.

**Request Body:**
```json
{
    "title": "New task",
    "description": "Task details",
    "due_date": "2026-03-20T09:00:00Z",
    "category_id": 1
}
```

**Response (success):** `201 Created`
```json
{
    "task": {
        "id": 5,
        "title": "New task",
        "description": "Task details",
        "completed": false,
        "due_date": "2026-03-20T09:00:00Z",
        "category_id": 1,
        "created_at": "2026-03-10T12:00:00Z",
        "updated_at": "2026-03-10T12:00:00Z"
    },
    "notification_queued": true
}
```

**Response (validation error):** `400 Bad Request`
```json
{
    "errors": {
        "title": ["Length must be between 1 and 100."],
        "description": ["Length must not exceed 500."]
    }
}
```

**Validation Rules:**
- `title`: Required, 1-100 characters
- `description`: Optional, max 500 characters
- `due_date`: Optional, must be valid ISO 8601 format
- `category_id`: Optional, must reference an existing category

---

#### PUT /tasks/:id

Updates an existing task with validation.

**Request Body:** (any subset of fields)
```json
{
    "completed": true
}
```

**Response (success):** `200 OK` with updated task

**Response (not found):** `404 Not Found`

**Response (validation error):** `400 Bad Request`

---

#### DELETE /tasks/:id

Deletes a task.

**Response (success):** `200 OK`
```json
{
    "message": "Task deleted"
}
```

**Response (not found):** `404 Not Found`

---

### Category Endpoints

#### GET /categories

Returns all categories with the count of tasks in each.

**Response:** `200 OK`
```json
{
    "categories": [
        {
            "id": 1,
            "name": "Work",
            "color": "#FF5733",
            "task_count": 5
        },
        {
            "id": 2,
            "name": "Personal",
            "color": "#33FF57",
            "task_count": 3
        }
    ]
}
```

---

#### GET /categories/:id

Returns a single category with all its tasks.

**Response (success):** `200 OK`
```json
{
    "id": 1,
    "name": "Work",
    "color": "#FF5733",
    "tasks": [
        {
            "id": 1,
            "title": "Finish report",
            "completed": false
        },
        {
            "id": 3,
            "title": "Email client",
            "completed": true
        }
    ]
}
```

**Response (not found):** `404 Not Found`

---

#### POST /categories

Creates a new category.

**Request Body:**
```json
{
    "name": "Health",
    "color": "#FF0000"
}
```

**Response (success):** `201 Created`

**Validation Rules:**
- `name`: Required, 1-50 characters, must be unique
- `color`: Optional, must be valid hex format (`#RRGGBB`)

**Response (validation error):** `400 Bad Request`
```json
{
    "errors": {
        "name": ["Category with this name already exists."]
    }
}
```

---

#### DELETE /categories/:id

Deletes a category. **Cannot delete a category that has tasks.**

**Response (success):** `200 OK`
```json
{
    "message": "Category deleted"
}
```

**Response (has tasks):** `400 Bad Request`
```json
{
    "error": "Cannot delete category with existing tasks. Move or delete tasks first."
}
```

**Response (not found):** `404 Not Found`

---

## Background Task: Due Date Notifications

When a task is created with a `due_date` that is **within 24 hours** of the current time, your application should queue a background job.

The background job should:
1. Wait 5 seconds (simulating sending a notification)
2. Log a message: `Reminder: Task 'TASK_TITLE' is due soon!`

**Requirements:**
- Use Redis as the message broker
- Use rq (Redis Queue) for job processing
- The POST /tasks response should include `"notification_queued": true` when a job is queued, or `"notification_queued": false` when no job is needed

**When to queue a notification:**
- Task has a `due_date`
- `due_date` is in the future
- `due_date` is within 24 hours from now

**When NOT to queue:**
- Task has no `due_date`
- `due_date` is more than 24 hours away
- `due_date` is in the past

---

## Docker Compose Requirements

Your application must run with Docker Compose. Create a `docker-compose.yml` that defines:

| Service | Image/Build | Purpose |
|---------|-------------|---------|
| `app` | Your Flask app | The main API server |
| `db` | `postgres:15` | PostgreSQL database |
| `redis` | `redis:7` | Message broker for background tasks |
| `worker` | Your Flask app | rq worker process |

**The entire stack should start with:**
```bash
docker-compose up --build
```

**Requirements:**
- App should wait for database to be ready before starting
- Database data should persist using a Docker volume
- Environment variables should be used for configuration (database URL, Redis URL)
- API should be accessible on a configured port (e.g., 5000)

---

## Project Structure

Suggested project structure:

```
assignment2/
├── app/
│   ├── __init__.py        # Flask app factory
│   ├── models.py          # SQLAlchemy models
│   ├── schemas.py         # Marshmallow schemas
│   ├── routes/
│   │   ├── tasks.py       # Task endpoints
│   │   └── categories.py  # Category endpoints
│   └── jobs.py            # Background job functions
├── migrations/            # Flask-Migrate migrations
├── worker.py              # rq worker entry point
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Getting Started

1. Accept the GitHub Classroom assignment (link on bCourses)
2. Clone your repository
3. Review the Week 6-8 lecture materials on:
   - Flask-Smorest and Marshmallow (Week 6)
   - SQLAlchemy and migrations (Week 7)
   - Background tasks with rq (Week 8)
4. Start with the models, then endpoints, then background tasks, then Docker

### Local Development (without Docker)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask flask-sqlalchemy flask-migrate marshmallow psycopg2-binary redis rq

# Set up local PostgreSQL and Redis (or use Docker for just these)
docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15
docker run -d --name redis -p 6379:6379 redis:7

# Run migrations
flask db upgrade

# Start the app
flask run

# In another terminal, start the worker
rq worker
```

### Running with Docker Compose

```bash
docker-compose up --build
```

---

## Submission

1. Push your code to your GitHub Classroom repository
2. Ensure `docker-compose up --build` runs successfully
3. Submit the repository link on bCourses before the deadline

---

## Rubric

| Category | Points | Description |
|----------|--------|-------------|
| **Database Models** | 20 | Task model has all required fields with proper types and constraints. Category model has required fields with unique constraint on name. Relationship between Task and Category is properly configured. |
| **Task Endpoints with Validation** | 30 | All CRUD endpoints work correctly (GET list with filtering, GET single, POST, PUT, DELETE). Marshmallow schemas validate input according to specified rules. Proper HTTP status codes returned. Error responses include structured validation messages. |
| **Category Endpoints** | 15 | GET returns categories with accurate task counts. POST creates categories with validation for unique names and hex color format. DELETE prevents deletion of categories with existing tasks. |
| **Background Task Processing** | 15 | Redis and rq worker are properly configured. Notification job is queued only for tasks with due_date within 24 hours. Job executes and logs the reminder message. POST response includes notification_queued field. |
| **Docker Compose** | 20 | docker-compose.yml defines all required services (app, db, redis, worker). `docker-compose up --build` runs without errors. All services connect properly. API is accessible and functional. |
| **Total** | **100** | |

---

## Tips

- **Start with models**: Get your SQLAlchemy models working first, then add endpoints
- **Test validation early**: Use Insomnia/Postman to test your Marshmallow validation
- **Docker last**: Get everything working locally before containerizing
- **Use Flask-Migrate**: Don't manually create database tables; use migrations
- **Check worker logs**: Make sure your rq worker is processing jobs

---

## Resources

- [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/)
- [Marshmallow Documentation](https://marshmallow.readthedocs.io/)
- [Flask-Migrate Documentation](https://flask-migrate.readthedocs.io/)
- [rq (Redis Queue) Documentation](https://python-rq.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

## Academic Integrity

This is an individual assignment. You may:
- Use official documentation for Flask, SQLAlchemy, Marshmallow, rq, and Docker
- Reference Stack Overflow for specific syntax questions
- Discuss concepts with classmates

You may NOT:
- Use AI tools (ChatGPT, Copilot, Claude, etc.) for initial submission
- Copy code from classmates
- Submit code you didn't write

AI tools are allowed for resubmissions after receiving your initial grade.

│   │   └── categories.py  # Category endpoints
│   └── jobs.py            # Background job functions
├── migrations/            # Flask-Migrate migrations
├── worker.py              # rq worker entry point
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Getting Started

1. Accept the GitHub Classroom assignment (link on bCourses)
2. Clone your repository
3. Review the Week 6-8 lecture materials on:
   - Flask-Smorest and Marshmallow (Week 6)
   - SQLAlchemy and migrations (Week 7)
   - Background tasks with rq (Week 8)
4. Start with the models, then endpoints, then background tasks, then Docker

### Local Development (without Docker)

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install flask flask-sqlalchemy flask-migrate marshmallow psycopg2-binary redis rq

# Set up local PostgreSQL and Redis (or use Docker for just these)
docker run -d --name postgres -p 5432:5432 -e POSTGRES_PASSWORD=password postgres:15
docker run -d --name redis -p 6379:6379 redis:7

# Run migrations
flask db upgrade

# Start the app
flask run

# In another terminal, start the worker
rq worker
```

### Running with Docker Compose

```bash
docker-compose up --build
```

---

## Submission

1. Push your code to your GitHub Classroom repository
2. Ensure `docker-compose up --build` runs successfully
3. Submit the repository link on bCourses before the deadline

---

## Rubric

| Category | Points | Description |
|----------|--------|-------------|
| **Database Models** | 20 | Task model has all required fields with proper types and constraints. Category model has required fields with unique constraint on name. Relationship between Task and Category is properly configured. |
| **Task Endpoints with Validation** | 30 | All CRUD endpoints work correctly (GET list with filtering, GET single, POST, PUT, DELETE). Marshmallow schemas validate input according to specified rules. Proper HTTP status codes returned. Error responses include structured validation messages. |
| **Category Endpoints** | 15 | GET returns categories with accurate task counts. POST creates categories with validation for unique names and hex color format. DELETE prevents deletion of categories with existing tasks. |
| **Background Task Processing** | 15 | Redis and rq worker are properly configured. Notification job is queued only for tasks with due_date within 24 hours. Job executes and logs the reminder message. POST response includes notification_queued field. |
| **Docker Compose** | 20 | docker-compose.yml defines all required services (app, db, redis, worker). `docker-compose up --build` runs without errors. All services connect properly. API is accessible and functional. |
| **Total** | **100** | |

---

## Tips

- **Start with models**: Get your SQLAlchemy models working first, then add endpoints
- **Test validation early**: Use Insomnia/Postman to test your Marshmallow validation
- **Docker last**: Get everything working locally before containerizing
- **Use Flask-Migrate**: Don't manually create database tables; use migrations
- **Check worker logs**: Make sure your rq worker is processing jobs

---

## Resources

- [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/)
- [Marshmallow Documentation](https://marshmallow.readthedocs.io/)
- [Flask-Migrate Documentation](https://flask-migrate.readthedocs.io/)
- [rq (Redis Queue) Documentation](https://python-rq.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

## Academic Integrity

This is an individual assignment. You may:
- Use official documentation for Flask, SQLAlchemy, Marshmallow, rq, and Docker
- Reference Stack Overflow for specific syntax questions
- Discuss concepts with classmates

You may NOT:
- Use AI tools (ChatGPT, Copilot, Claude, etc.) for initial submission
- Copy code from classmates
- Submit code you didn't write

AI tools are allowed for resubmissions after receiving your initial grade.
