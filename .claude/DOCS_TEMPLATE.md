# DOCS_TEMPLATE.md - Documentation File Templates

Templates for documentation files written by the Documentation Agent. Save as root-level markdown files (e.g., `SETUP.md`, `API.md`, `COMPONENTS.md`).

## 1. SETUP.md - Installation & Setup Guide

```markdown
# Setup & Installation

## Prerequisites
- [List language/runtime requirements, e.g., Node.js 20.x, npm 10.x]
- [Database: PostgreSQL 15.x]
- [Other dependencies]

## Installation

### 1. Clone the Repository
\`\`\`bash
git clone <repository-url>
cd <project-name>
\`\`\`

### 2. Install Dependencies
\`\`\`bash
npm install
\`\`\`

### 3. Environment Setup
Create a `.env.local` file in the project root:
\`\`\`
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
API_PORT=3001
API_SECRET=your_secret_key
\`\`\`

### 4. Database Setup
\`\`\`bash
npm run db:migrate
npm run db:seed  # Optional: seed with example data
\`\`\`

### 5. Start Development Server
\`\`\`bash
npm run dev
\`\`\`

Access the app at: http://localhost:3000 (frontend) and http://localhost:3001 (backend API)

## Development Commands

- **Frontend Dev:** `npm run dev:frontend`
- **Backend Dev:** `npm run dev:backend`
- **Run Tests:** `npm run test`
- **Run Linter:** `npm run lint`
- **Format Code:** `npm run format`
- **Build for Production:** `npm run build`

## Troubleshooting

### Port Already in Use
If port 3000 or 3001 is already in use:
\`\`\`bash
lsof -i :3000  # Find process on port 3000
kill -9 <PID>   # Kill the process
\`\`\`

### Database Connection Error
- Check DATABASE_URL in .env.local
- Ensure PostgreSQL is running: `psql -U postgres` to verify
- Run migrations: `npm run db:migrate`

### Dependencies Won't Install
\`\`\`bash
npm cache clean --force
rm package-lock.json
npm install
\`\`\`

## Next Steps
See [API.md](API.md) for API documentation or [COMPONENTS.md](COMPONENTS.md) for component docs.
```

## 2. API.md - API Documentation

```markdown
# API Documentation

Base URL: `http://localhost:3001` (dev) | `https://api.example.com` (prod)

## Authentication
All endpoints require a JWT token in the Authorization header:
\`\`\`
Authorization: Bearer <token>
\`\`\`

Obtain a token by calling POST /auth/login.

## Response Format
All responses follow this structure:
\`\`\`json
{
  "success": true,
  "data": { /* actual response data */ },
  "error": null
}
\`\`\`

Error responses:
\`\`\`json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable error message",
    "details": { /* optional additional info */ }
  }
}
\`\`\`

## Endpoints

### POST /auth/login
Login and get JWT token.

**Request:**
\`\`\`json
{
  "email": "user@example.com",
  "password": "password"
}
\`\`\`

**Response (200):**
\`\`\`json
{
  "success": true,
  "data": {
    "token": "eyJhbGc...",
    "user": {
      "id": "user_123",
      "email": "user@example.com",
      "name": "John Doe"
    }
  }
}
\`\`\`

**Error (401):**
\`\`\`json
{
  "success": false,
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password"
  }
}
\`\`\`

### GET /api/users/:id
Get user details by ID.

**Response (200):**
\`\`\`json
{
  "success": true,
  "data": {
    "id": "user_123",
    "email": "user@example.com",
    "name": "John Doe",
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
\`\`\`

### POST /api/users
Create a new user (admin only).

**Request:**
\`\`\`json
{
  "email": "newuser@example.com",
  "name": "Jane Doe",
  "password": "secure_password"
}
\`\`\`

**Response (201):**
\`\`\`json
{
  "success": true,
  "data": {
    "id": "user_456",
    "email": "newuser@example.com",
    "name": "Jane Doe"
  }
}
\`\`\`

## Rate Limiting
- 100 requests per minute per IP
- Returns 429 Too Many Requests when exceeded
- Retry-After header included with wait time in seconds

## Error Codes
- `INVALID_CREDENTIALS` - Login failed
- `UNAUTHORIZED` - Missing or invalid token
- `FORBIDDEN` - Insufficient permissions
- `NOT_FOUND` - Resource not found
- `VALIDATION_ERROR` - Request validation failed
- `INTERNAL_ERROR` - Server error

## Pagination
Endpoints that return lists support pagination:
\`\`\`
GET /api/users?limit=20&offset=0
\`\`\`

Response includes pagination info:
\`\`\`json
{
  "success": true,
  "data": [ /* items */ ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 150
  }
}
\`\`\`
```

## 3. COMPONENTS.md - Frontend Component Documentation

```markdown
# Component Documentation

## UserForm

User registration and login form component.

**Location:** src/components/UserForm.tsx:15

**Props:**
- `mode: 'login' | 'register'` - Form mode (required)
- `onSubmit: (data: UserFormData) => Promise<void>` - Callback on successful submission
- `isLoading?: boolean` - Show loading state (default: false)
- `error?: string` - Error message to display

**Usage:**
\`\`\`tsx
import { UserForm } from './components/UserForm'

function LoginPage() {
  const handleSubmit = async (data) => {
    await loginUser(data)
  }

  return (
    <UserForm
      mode="login"
      onSubmit={handleSubmit}
    />
  )
}
\`\`\`

**Validation:**
- Email: valid email format required
- Password: minimum 8 characters
- Shows inline validation errors

**State:**
- `email: string`
- `password: string`
- `errors: { field: string }[]`

---

## Dashboard

Main dashboard component displaying user overview.

**Location:** src/components/Dashboard.tsx:22

**Props:**
- `userId: string` - User ID to load dashboard for (required)
- `onLogout: () => void` - Callback for logout action

**Usage:**
\`\`\`tsx
import { Dashboard } from './components/Dashboard'

function DashboardPage({ userId }) {
  return <Dashboard userId={userId} onLogout={handleLogout} />
}
\`\`\`

**Features:**
- Displays user profile
- Shows recent activity
- Lists available actions
- Responsive layout for mobile

---

[Add more components following the same format]
```

## 4. ARCHITECTURE.md - System Design & Architecture

```markdown
# Architecture & Design

## High-Level Overview

[ASCII diagram or description of overall system architecture]

```
┌─────────────────────────────────────────────────┐
│             Frontend (React)                    │
│  - User Interface Components                   │
│  - State Management (Context API)              │
│  - API Client                                  │
└──────────────────────┬──────────────────────────┘
                       │ HTTP/REST
┌──────────────────────▼──────────────────────────┐
│           Backend API (Express.js)              │
│  - Authentication & Authorization              │
│  - Business Logic                              │
│  - Data Validation                             │
└──────────────────────┬──────────────────────────┘
                       │ SQL
┌──────────────────────▼──────────────────────────┐
│          Database (PostgreSQL)                  │
│  - User Data                                   │
│  - Application State                           │
└──────────────────────────────────────────────────┘
\`\`\`

## Frontend Architecture

**Stack:** React 18 + TypeScript + Tailwind CSS

**Folder Structure:**
\`\`\`
src/
├── components/      # Reusable React components
├── pages/          # Page-level components
├── hooks/          # Custom React hooks
├── context/        # Context API providers
├── api/            # API client & requests
├── types/          # TypeScript type definitions
├── utils/          # Helper functions
└── styles/         # Global styles
\`\`\`

**State Management:** Context API with custom hooks
- User context: authentication state, user profile
- App context: global app state, notifications

**Key Components:**
- UserForm: Login/registration
- Dashboard: Main app dashboard
- Navigation: Header navigation

## Backend Architecture

**Stack:** Express.js + TypeScript + PostgreSQL

**Folder Structure:**
\`\`\`
src/
├── routes/         # API routes
├── controllers/    # Route handlers
├── services/       # Business logic
├── models/         # Database models
├── middleware/     # Express middleware
├── db/            # Database migrations & seeds
├── utils/         # Helper functions
└── types/         # TypeScript types
\`\`\`

**Middleware:**
- Authentication: Verify JWT tokens
- Error handling: Catch and format errors
- Logging: Request/response logging
- Validation: Input validation

**Database Schema:**
- Users table: id, email, password_hash, name, created_at
- [Add other tables]

## Authentication Flow

1. User submits login credentials
2. Backend validates and hashes password
3. Backend returns JWT token
4. Frontend stores token in localStorage
5. Frontend includes token in Authorization header for subsequent requests
6. Backend verifies token on each request

## Data Flow

[Describe how data flows through the system, key interactions, etc.]

## Design Decisions

[Document important architectural choices and why they were made]

- Used Context API instead of Redux for simplicity
- REST API instead of GraphQL for straightforward data needs
- PostgreSQL for relational data structure
```

## 5. TROUBLESHOOTING.md - Common Issues & Solutions

```markdown
# Troubleshooting Guide

## Common Issues

### Issue: Login fails with "Invalid credentials"

**Symptoms:**
- Login form returns 401 error
- Can't access dashboard

**Solutions:**
1. Verify email address is correct
2. Check password (passwords are case-sensitive)
3. Reset password via [password reset link]
4. Check if account is active (contact admin if disabled)

**See Also:** [API.md - POST /auth/login](API.md#post-authlogin)

### Issue: Components render twice in development

**Symptoms:**
- useEffect hook runs twice on component mount
- Console logs show duplicate messages

**Cause:** React.StrictMode double-invokes effects to catch side effect bugs

**Solutions:**
- This is expected behavior in development mode
- In production (build), effects run only once
- To disable StrictMode, remove `<React.StrictMode>` from src/main.tsx

**See Also:** src/main.tsx:12

### Issue: Database connection timeout

**Symptoms:**
- App won't start
- Error: "Unable to connect to database"

**Solutions:**
1. Check PostgreSQL is running: `psql -U postgres`
2. Verify DATABASE_URL in .env.local
3. Check credentials (user, password, host, port)
4. Verify database exists: `psql -l`
5. Run migrations: `npm run db:migrate`

**See Also:** [SETUP.md - Troubleshooting](SETUP.md#troubleshooting)

### Issue: Port 3000 or 3001 already in use

**Symptoms:**
- "EADDRINUSE: address already in use :::3000"

**Solutions:**
\`\`\`bash
# Find process on port 3000
lsof -i :3000

# Kill the process (replace PID)
kill -9 <PID>

# Or change port in .env.local
API_PORT=3002
\`\`\`

[Add more issues and solutions as needed]
```

## Usage Instructions for Documentation Agent

When assigned a documentation task:

1. **Read the task** in .claude/PLAN.md
2. **Check .claude/WIKI.md** for completed features and specs
3. **Review .claude/TECH.md** for tech stack details
4. **Choose appropriate template(s)** from above
5. **Fill in project-specific content**
6. **Save as root-level markdown** (e.g., `SETUP.md`, `API.md`)
7. **Link between docs** for navigation (see examples above)
8. **Link to source code** using file_path:line_number format
9. **Mark task complete** in TodoWrite
10. **Note in .claude/WIKI.md** under "Session Notes" if docs are stale or need updates

## Documentation Maintenance

- Review documentation quarterly
- Update when features change
- Link new docs from existing docs
- Keep code examples working
- Tag as "Documentation Stale:" in .claude/WIKI.md if diverges from code
