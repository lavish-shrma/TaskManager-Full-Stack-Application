# Team Task Manager

A production-grade team task management application built with FastAPI, React, PostgreSQL, and Docker. Features project-based task organization, drag-and-drop kanban board, role-based access control, and real-time collaboration.

## Features

- **User Authentication**: Secure signup and login with JWT tokens
- **Project Management**: Create projects, manage members with role-based access
- **Task Organization**: Drag-and-drop kanban board with status management (To Do, In Progress, Done)
- **Priority & Deadlines**: Set task priority levels and due dates with overdue tracking
- **Dashboard**: Overview of all tasks, projects, and team activity
- **Role-Based Access Control**: Admin and Member roles with granular permissions
- **Responsive Design**: Works seamlessly on desktop and mobile devices

## Tech Stack

### Backend
- **Framework**: FastAPI
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT (Python-Jose) + BCrypt
- **Migrations**: Alembic
- **Server**: Uvicorn
- **Async Support**: asyncpg for PostgreSQL

### Frontend
- **Framework**: React 18
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Routing**: React Router v6
- **State Management**: React Context

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Deployment**: Railway

## Local Setup

### Prerequisites
- Docker and Docker Compose installed
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Quick Start with Docker Compose

1. Clone the repository:
```bash
git clone <repository-url>
cd ethara-ai
```

2. Create environment files:
```bash
# Backend environment
cp .env.example .env
# Frontend environment
cp frontend/.env.example frontend/.env
```

3. Start all services:
```bash
docker-compose up
```

4. Migrations run automatically on startup
5. Access the application:
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Local Development Setup

#### Backend Setup

1. Create Python virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp ../.env.example .env
# Edit .env with your settings
```

4. Start PostgreSQL:
```bash
# Make sure PostgreSQL is running on localhost:5432
# Or use Docker: docker run -e POSTGRES_USER=taskmanager -e POSTGRES_PASSWORD=taskmanager -e POSTGRES_DB=taskmanager -p 5432:5432 postgres:16-alpine
```

5. Run database migrations:
```bash
alembic upgrade head
```

6. Start backend server:
```bash
uvicorn app.main:app --reload
```

#### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
# VITE_API_URL=http://localhost:8000
```

4. Start development server:
```bash
npm run dev
```

## Environment Variables

### Backend (.env)

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| DATABASE_URL | String | PostgreSQL connection string (asyncpg protocol) | `postgresql+asyncpg://taskmanager:taskmanager@localhost:5432/taskmanager` |
| SECRET_KEY | String | JWT signing secret key (min 32 chars for production) | `your-secret-key-change-in-production` |
| FRONTEND_URL | String | Frontend URL for CORS configuration | `http://localhost:5173` |
| PORT | Integer | Server port (Railway sets this automatically) | `8000` |

### Frontend (.env)

| Variable | Type | Description | Example |
|----------|------|-------------|---------|
| VITE_API_URL | String | Backend API base URL | `http://localhost:8000` |

## Database Schema

### Tables

**users**
- `id` (UUID, PK): User identifier
- `name` (String): User full name
- `email` (String, Unique): User email address
- `password_hash` (String): Bcrypt hashed password
- `role` (Enum: admin, member): User system role (not project-specific)
- `created_at` (Timestamp): Account creation time

**projects**
- `id` (UUID, PK): Project identifier
- `name` (String): Project name
- `description` (Text, Nullable): Project description
- `owner_id` (UUID, FK to users): Project creator/owner
- `created_at` (Timestamp): Project creation time

**project_members**
- `id` (UUID, PK): Membership record identifier
- `project_id` (UUID, FK to projects): Associated project
- `user_id` (UUID, FK to users): Associated user
- `role` (Enum: admin, member): Role within the project
- Unique constraint on (project_id, user_id)

**tasks**
- `id` (UUID, PK): Task identifier
- `title` (String): Task title
- `description` (Text, Nullable): Task description
- `status` (Enum: todo, in_progress, done): Task status
- `priority` (Enum: low, medium, high): Task priority
- `due_date` (Date, Nullable): Task due date
- `project_id` (UUID, FK to projects): Parent project
- `assignee_id` (UUID, FK to users, Nullable): Assigned user
- `created_by` (UUID, FK to users): Task creator
- `created_at` (Timestamp): Task creation time

## API Endpoints

### Authentication
- `POST /auth/signup` - Register new user
- `POST /auth/login` - Login and get JWT token
- `GET /auth/me` - Get current user info

### Projects
- `POST /projects` - Create project
- `GET /projects` - List user's projects
- `GET /projects/{id}` - Get project details
- `PATCH /projects/{id}` - Update project (admin only)
- `DELETE /projects/{id}` - Delete project (owner only)

### Project Members
- `POST /projects/{id}/members` - Add member (admin only)
- `DELETE /projects/{id}/members/{user_id}` - Remove member (admin only)

### Tasks
- `POST /projects/{id}/tasks` - Create task (admin only)
- `GET /projects/{id}/tasks` - List tasks (query: status, assignee_id)
- `GET /projects/{id}/tasks/{task_id}` - Get task details
- `PATCH /projects/{id}/tasks/{task_id}` - Update task
- `DELETE /projects/{id}/tasks/{task_id}` - Delete task (admin or creator only)

### Dashboard
- `GET /dashboard` - Get dashboard statistics and overdue tasks

## Role-Based Access Control (RBAC)

### Project Membership Roles

**Admin**
- Full CRUD on all tasks in the project
- Can add/remove project members
- Can update project metadata
- Cannot delete project (only owner can)

**Member**
- Read project and task data
- Can update task status only on tasks assigned to them
- Cannot modify task details or create tasks

### Project Ownership
- Only the project owner can delete the project
- Project owner is automatically added as admin when creating a project

## Railway Deployment

### Prerequisites
- Railway account (https://railway.app)
- Git repository with this code

### Deployment Steps

1. Connect your GitHub repository to Railway

2. Create a new project in Railway dashboard

3. Add PostgreSQL plugin:
   - Click "Add Service" → "Database" → PostgreSQL
   - Railway will provide `DATABASE_URL` automatically

4. Create backend service:
   - Click "Add Service" → "GitHub Repo"
   - Select this repository
   - Set root directory to `backend/`

5. Configure environment variables:
   - Go to project settings
   - Add the following variables:
     - `SECRET_KEY`: Generate a secure random string
     - `FRONTEND_URL`: Your deployed frontend URL
     - `DATABASE_URL`: Auto-provided by PostgreSQL plugin

6. Deploy frontend to Vercel/Netlify (recommended):
   - Connect `frontend/` directory
   - Set `VITE_API_URL` to your Railway backend URL
   - Example: `https://your-project.railway.app`

### Production Checklist
- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `FRONTEND_URL` to your deployed frontend domain
- [ ] Enable HTTPS (Railway does this by default)
- [ ] Configure PostgreSQL backups in Railway dashboard
- [ ] Monitor logs in Railway dashboard

## Common Issues

### Port Already in Use
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Database Connection Failed
- Ensure PostgreSQL is running
- Verify DATABASE_URL format
- Check credentials in .env file

### CORS Errors
- Verify FRONTEND_URL matches your actual frontend domain
- Check browser console for exact error message

### JWT Token Expired
- Tokens expire after 30 minutes
- Frontend automatically clears token and redirects to login on 401 response

## Development

### Running Tests
```bash
# Backend tests (add pytest to requirements.txt first)
cd backend
pytest
```

### Database Migrations
```bash
# Create new migration
cd backend
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1
```

### Code Structure

```
.
├── backend/
│   ├── app/
│   │   ├── main.py           # FastAPI app entry point
│   │   ├── models.py         # SQLAlchemy models
│   │   ├── schemas.py        # Pydantic schemas
│   │   ├── routers/          # API route handlers
│   │   ├── dependencies/     # Dependency injection
│   │   ├── core/             # Core utilities (auth, security)
│   │   └── db/               # Database configuration
│   ├── alembic/              # Database migrations
│   └── requirements.txt       # Python dependencies
├── frontend/
│   ├── src/
│   │   ├── pages/            # React page components
│   │   ├── components/       # Reusable components
│   │   ├── context/          # React Context providers
│   │   ├── api/              # API client configuration
│   │   ├── hooks/            # Custom React hooks
│   │   ├── types.ts          # TypeScript type definitions
│   │   └── main.tsx          # React entry point
│   └── package.json          # Node dependencies
├── docker-compose.yml         # Local development setup
├── railway.toml              # Railway deployment config
└── README.md                 # This file
```

## Performance Optimizations

- Async database operations with SQLAlchemy async ORM
- Connection pooling with asyncpg
- Efficient query patterns to minimize N+1 problems
- Vite for fast frontend bundling
- Tailwind CSS for minimal CSS footprint

## Security

- Passwords hashed with bcrypt
- JWT tokens with expiration (30 minutes)
- CORS configured to frontend domain only
- SQL injection protected via SQLAlchemy ORM
- Input validation via Pydantic
- Role-based access control at dependency level

## Contributing

1. Create feature branch: `git checkout -b feature/description`
2. Commit changes: `git commit -m "lowercase imperative message"`
3. Push branch: `git push origin feature/description`
4. Create Pull Request

## License

This project is provided as-is for Ethara AI.

## Support

For issues or questions, contact the development team or create an issue in the repository.
