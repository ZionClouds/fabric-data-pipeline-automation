# Database Implementation Guide

## Overview

This document describes the SQL database implementation for the Fabric Data Pipeline Automation project. The database provides persistent storage for conversations, jobs, and logs, ensuring data persistence across page refreshes and server restarts.

## Database Schema

### Tables

#### 1. **conversations**

Stores chat conversations between users and the AI assistant.

| Column | Type | Description |
|--------|------|-------------|
| conversation_id | VARCHAR(36) PRIMARY KEY | Unique identifier (UUID) |
| user_id | VARCHAR(255) | User identifier |
| user_email | VARCHAR(255) | User email address |
| workspace_id | VARCHAR(255) | Microsoft Fabric workspace ID |
| lakehouse_id | VARCHAR(255) | Lakehouse ID |
| workspace_name | VARCHAR(255) | Workspace display name |
| lakehouse_name | VARCHAR(255) | Lakehouse display name |
| status | VARCHAR(50) | Conversation status: 'active', 'completed', 'archived' |
| created_at | DATETIME | Creation timestamp |
| updated_at | DATETIME | Last update timestamp |
| metadata | JSON | Additional metadata |

#### 2. **conversation_messages**

Stores individual messages within conversations.

| Column | Type | Description |
|--------|------|-------------|
| message_id | VARCHAR(36) PRIMARY KEY | Unique identifier (UUID) |
| conversation_id | VARCHAR(36) FOREIGN KEY | References conversations.conversation_id |
| role | VARCHAR(50) | Message role: 'user', 'assistant', 'system' |
| content | TEXT | Message content |
| timestamp | DATETIME | Message timestamp |
| metadata | JSON | Additional metadata (e.g., Bing grounding info) |

#### 3. **jobs**

Tracks pipeline generation and deployment jobs.

| Column | Type | Description |
|--------|------|-------------|
| job_id | VARCHAR(36) PRIMARY KEY | Unique identifier (UUID) |
| conversation_id | VARCHAR(36) FOREIGN KEY | References conversations.conversation_id |
| job_type | VARCHAR(100) | Job type: 'pipeline_generation', 'pipeline_deployment', etc. |
| status | VARCHAR(50) | Job status: 'pending', 'in_progress', 'completed', 'failed' |
| pipeline_generation_status | VARCHAR(50) | Pipeline generation stage status |
| pipeline_deployment_status | VARCHAR(50) | Pipeline deployment stage status |
| pipeline_preview_status | VARCHAR(50) | Pipeline preview stage status |
| pipeline_definition | JSON | Complete pipeline definition |
| pipeline_id | VARCHAR(255) | Fabric pipeline ID after deployment |
| pipeline_name | VARCHAR(255) | Pipeline name |
| workspace_id | VARCHAR(255) | Workspace ID |
| lakehouse_id | VARCHAR(255) | Lakehouse ID |
| workspace_name | VARCHAR(255) | Workspace name |
| lakehouse_name | VARCHAR(255) | Lakehouse name |
| created_at | DATETIME | Job creation time |
| updated_at | DATETIME | Last update time |
| started_at | DATETIME | Job start time |
| completed_at | DATETIME | Job completion time |
| error_message | TEXT | Error message if failed |
| error_details | JSON | Detailed error information |
| metadata | JSON | Additional metadata |

#### 4. **logs**

Comprehensive application logging.

| Column | Type | Description |
|--------|------|-------------|
| log_id | INTEGER PRIMARY KEY AUTOINCREMENT | Unique log identifier |
| timestamp | DATETIME | Log timestamp |
| level | VARCHAR(20) | Log level: 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL' |
| service | VARCHAR(100) | Service name that generated the log |
| conversation_id | VARCHAR(36) | Associated conversation ID (optional) |
| job_id | VARCHAR(36) | Associated job ID (optional) |
| user_id | VARCHAR(255) | User ID (optional) |
| message | TEXT | Log message |
| stack_trace | TEXT | Stack trace for errors |
| metadata | JSON | Additional metadata |

### Relationships

```
conversations (1) ──────< (N) conversation_messages
     │
     └──────< (N) jobs
```

## Configuration

### Database URL Configuration

The database URL is configured in `backend/settings.py`:

```python
# Use SQLite for development
USE_SQLITE = True

if USE_SQLITE:
    DATABASE_URL = "sqlite:///./fabric_pipeline.db"
else:
    # SQL Server for production
    DATABASE_URL = (
        f"mssql+pyodbc://{DATABASE_USER}:{DATABASE_PASSWORD}"
        f"@{DATABASE_SERVER}/{DATABASE_NAME}"
        f"?driver=ODBC+Driver+18+for+SQL+Server"
    )
```

**For Development:** Set `USE_SQLITE = True` (default)
**For Production:** Set `USE_SQLITE = False` and configure SQL Server credentials

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies added:
- `sqlalchemy==2.0.23` - ORM for database operations
- `alembic==1.13.0` - Database migrations (optional)

### 2. Initialize Database

Run the initialization script to create database tables:

```bash
python backend/init_database.py
```

This will create:
- `fabric_pipeline.db` file (if using SQLite)
- All required tables (conversations, conversation_messages, jobs, logs)

## API Integration

### Backend Integration

The database is automatically initialized on application startup in `main.py`:

```python
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    init_database(settings.DATABASE_URL)
    db_service = get_db_service()
    db_service.log_info(
        service="main",
        message="Application started successfully"
    )
```

### Chat Endpoint Integration

Conversations and messages are automatically saved in the `/api/ai/chat` endpoint:

```python
# Get or create conversation
conversation_id = get_or_create_conversation(
    user_email=user['email'],
    workspace_id=request.workspace_id
)

# Save user message
save_chat_message(
    conversation_id=conversation_id,
    role="user",
    content=user_message
)

# ... AI processing ...

# Save assistant response
save_chat_message(
    conversation_id=conversation_id,
    role="assistant",
    content=response["content"]
)

# Return with conversation_id
return ChatResponse(
    content=response["content"],
    conversation_id=conversation_id,
    ...
)
```

### Job Tracking

Jobs are tracked in pipeline generation/deployment endpoints:

```python
# Create job
job = db_service.create_job(
    job_type="pipeline_generation",
    workspace_id=workspace_id,
    metadata={"pipeline_name": pipeline_name}
)

# Update job status
db_service.update_job_status(
    job_id=job['job_id'],
    status="in_progress",
    pipeline_generation_status="in_progress"
)

# On completion
db_service.update_job_status(
    job_id=job['job_id'],
    status="completed",
    pipeline_definition=pipeline_definition
)
```

## New API Endpoints

### Conversations

#### Get User Conversations
```
GET /api/conversations?user_email={email}&status=active&limit=50
```

Response:
```json
[
  {
    "conversation_id": "uuid",
    "user_email": "user@example.com",
    "workspace_id": "workspace-id",
    "status": "active",
    "created_at": "2025-01-10T10:00:00",
    "message_count": 15
  }
]
```

#### Get Conversation with Messages
```
GET /api/conversations/{conversation_id}
```

Response:
```json
{
  "conversation_id": "uuid",
  "user_email": "user@example.com",
  "workspace_id": "workspace-id",
  "status": "active",
  "created_at": "2025-01-10T10:00:00",
  "messages": [
    {
      "message_id": "msg-uuid",
      "role": "user",
      "content": "I need to create a pipeline",
      "timestamp": "2025-01-10T10:00:00"
    },
    {
      "message_id": "msg-uuid-2",
      "role": "assistant",
      "content": "I can help you with that!",
      "timestamp": "2025-01-10T10:00:05"
    }
  ]
}
```

#### Delete Conversation
```
DELETE /api/conversations/{conversation_id}
```

### Jobs

#### Get Jobs
```
GET /api/jobs?conversation_id={id}&status=completed&limit=50
```

Response:
```json
[
  {
    "job_id": "job-uuid",
    "conversation_id": "conv-uuid",
    "job_type": "pipeline_generation",
    "status": "completed",
    "pipeline_generation_status": "completed",
    "pipeline_deployment_status": "not_started",
    "pipeline_name": "MyPipeline",
    "created_at": "2025-01-10T10:00:00",
    "completed_at": "2025-01-10T10:05:00"
  }
]
```

#### Get Specific Job
```
GET /api/jobs/{job_id}
```

### Logs

#### Get Logs
```
GET /api/logs?conversation_id={id}&level=ERROR&service=main&limit=100
```

Response:
```json
[
  {
    "log_id": 123,
    "timestamp": "2025-01-10T10:00:00",
    "level": "ERROR",
    "service": "main",
    "conversation_id": "conv-uuid",
    "message": "Pipeline deployment failed",
    "stack_trace": "..."
  }
]
```

## Frontend Integration

### Conversation Persistence

The frontend automatically:
1. Receives `conversation_id` from chat responses
2. Stores it in React context and localStorage
3. Restores it on page refresh

```javascript
// AIChat.js

// Save conversation_id from response
if (response.data.conversation_id) {
  setConversationId(response.data.conversation_id);
  localStorage.setItem('conversationId', response.data.conversation_id);
}

// Restore on mount
useEffect(() => {
  const storedConversationId = localStorage.getItem('conversationId');
  if (storedConversationId) {
    setConversationId(storedConversationId);
  }
}, []);
```

### Context Updates

Added to `PipelineContext.js`:
```javascript
const [conversationId, setConversationId] = useState(null);
const [currentJobId, setCurrentJobId] = useState(null);
```

## Database Service API

### Conversation Operations

```python
from services.database_service import get_db_service

db_service = get_db_service()

# Create conversation
conversation = db_service.create_conversation(
    user_email="user@example.com",
    workspace_id="workspace-id"
)

# Get conversation
conversation = db_service.get_conversation(conversation_id)

# Get user conversations
conversations = db_service.get_conversations_by_user(
    user_email="user@example.com",
    status="active"
)

# Update conversation
db_service.update_conversation(
    conversation_id,
    status="completed"
)

# Delete conversation
db_service.delete_conversation(conversation_id)
```

### Message Operations

```python
# Add message
message = db_service.add_message(
    conversation_id=conversation_id,
    role="user",
    content="Hello",
    metadata={"source": "web"}
)

# Get conversation messages
messages = db_service.get_conversation_messages(conversation_id)

# Get conversation with messages
conversation = db_service.get_conversation_with_messages(conversation_id)
```

### Job Operations

```python
# Create job
job = db_service.create_job(
    job_type="pipeline_generation",
    workspace_id="workspace-id",
    pipeline_definition={"activities": [...]}
)

# Update job status
db_service.update_job_status(
    job_id=job_id,
    status="completed",
    pipeline_generation_status="completed"
)

# Get job
job = db_service.get_job(job_id)

# Get jobs by conversation
jobs = db_service.get_jobs_by_conversation(conversation_id)
```

### Logging Operations

```python
# Add log
db_service.add_log(
    level="INFO",
    service="main",
    message="Pipeline deployed successfully",
    conversation_id=conversation_id,
    job_id=job_id
)

# Helper methods
db_service.log_info("service_name", "Message")
db_service.log_error("service_name", "Error message", job_id=job_id)
db_service.log_warning("service_name", "Warning")

# Get logs
logs = db_service.get_logs(
    conversation_id=conversation_id,
    level="ERROR",
    limit=100
)
```

## Benefits

### 1. Data Persistence
- Conversations and messages persist across page refreshes
- Jobs and pipeline definitions are stored for audit trail
- No more 404 errors on page refresh

### 2. Audit Trail
- Complete conversation history
- Job status tracking with timestamps
- Comprehensive logging for debugging

### 3. User Experience
- Users can continue conversations after page refresh
- View conversation history
- Track pipeline deployment progress

### 4. Debugging & Monitoring
- Centralized logging
- Easy error tracking
- Performance monitoring

## Migration from In-Memory Storage

Previously, the application used in-memory storage (`generated_pipelines = {}`). This data was lost on server restart.

**Before:**
```python
generated_pipelines = {}  # Lost on restart
generated_pipelines[pipeline_id] = {...}
```

**After:**
```python
# Persistent database storage
job = db_service.create_job(
    job_type="pipeline_generation",
    pipeline_definition={...}
)
```

## Troubleshooting

### Database Not Found

**Error:** `RuntimeError: Database service not initialized`

**Solution:** Ensure `init_database()` is called on startup:
```python
python backend/init_database.py
```

### SQLite Database Locked

**Error:** `sqlite3.OperationalError: database is locked`

**Solution:**
- Ensure only one instance of the application is running
- Check for zombie processes holding the database lock
- For production, use SQL Server instead of SQLite

### Missing Tables

**Error:** `Table 'conversations' doesn't exist`

**Solution:** Run the initialization script:
```bash
python backend/init_database.py
```

### Migration to SQL Server

To migrate from SQLite to SQL Server:

1. Update `settings.py`:
   ```python
   USE_SQLITE = False
   ```

2. Configure SQL Server credentials:
   ```python
   DATABASE_SERVER = "your-server.database.windows.net"
   DATABASE_NAME = "fabricdb"
   DATABASE_USER = "admin"
   DATABASE_PASSWORD = "password"
   ```

3. Run initialization:
   ```bash
   python backend/init_database.py
   ```

## Testing

### Test Database Operations

```python
# Test conversation creation
from services.database_service import init_database, get_db_service

init_database("sqlite:///./test.db")
db_service = get_db_service()

# Create conversation
conv = db_service.create_conversation(
    user_email="test@example.com",
    workspace_id="test-workspace"
)
print(f"Created conversation: {conv['conversation_id']}")

# Add message
msg = db_service.add_message(
    conversation_id=conv['conversation_id'],
    role="user",
    content="Test message"
)
print(f"Added message: {msg['message_id']}")

# Get conversation with messages
full_conv = db_service.get_conversation_with_messages(conv['conversation_id'])
print(f"Messages: {len(full_conv['messages'])}")
```

## Future Enhancements

1. **Conversation History UI**
   - Add UI to browse past conversations
   - Resume conversations from history

2. **Advanced Search**
   - Full-text search across conversations
   - Filter by date range, workspace, status

3. **Analytics Dashboard**
   - Conversation metrics
   - Job success/failure rates
   - Performance analytics

4. **Data Export**
   - Export conversations to PDF/JSON
   - Bulk export for compliance

5. **Database Migrations**
   - Use Alembic for schema migrations
   - Version control for database schema

## Security Considerations

1. **Data Encryption**
   - Consider encrypting sensitive data in `pipeline_definition`
   - Use Azure Key Vault for database credentials

2. **Access Control**
   - Implement row-level security
   - Ensure users can only access their own conversations

3. **Data Retention**
   - Implement auto-archival of old conversations
   - Add data retention policies

4. **Backup Strategy**
   - Regular database backups
   - Point-in-time recovery for SQL Server

## Summary

The database implementation provides a robust, scalable solution for persisting conversations, jobs, and logs. It eliminates 404 errors on page refresh, provides comprehensive audit trails, and enables future enhancements like conversation history and analytics.

**Key Features:**
- ✅ Persistent conversation storage
- ✅ Job tracking with status updates
- ✅ Comprehensive logging
- ✅ RESTful API for data access
- ✅ Frontend integration with localStorage
- ✅ Supports both SQLite (dev) and SQL Server (prod)
- ✅ Full audit trail
