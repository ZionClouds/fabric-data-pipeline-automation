# Database Implementation - Quick Start Guide

## What's New?

Your Fabric Data Pipeline Automation project now has a SQL database that:
- ✅ **Stores all conversations** - No more 404 errors on page refresh!
- ✅ **Tracks pipeline jobs** - Monitor generation and deployment status
- ✅ **Logs everything** - Complete audit trail for debugging
- ✅ **Persists data** - Everything survives server restarts

## Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

This installs:
- `sqlalchemy==2.0.23` - Database ORM
- `alembic==1.13.0` - Database migrations

### Step 2: Initialize Database

```bash
python backend/init_database.py
```

Output:
```
Initializing database...
Database URL: sqlite:///./fabric_pipeline.db
✓ Database tables created successfully!

Tables created:
  - conversations
  - conversation_messages
  - jobs
  - logs
```

This creates a `fabric_pipeline.db` SQLite file in the backend directory.

### Step 3: Start the Application

```bash
# Start backend
cd backend
uvicorn main:app --reload --port 8080

# Start frontend (in another terminal)
cd frontend
npm start
```

That's it! The database is now active. 🎉

## What Changed?

### Backend Changes

#### 1. **New Database Tables**
- `conversations` - Chat conversations
- `conversation_messages` - Individual messages
- `jobs` - Pipeline generation/deployment jobs
- `logs` - Application logs

#### 2. **New API Endpoints**

**Get Conversations:**
```
GET /api/conversations?user_email=user@example.com
```

**Get Conversation with Messages:**
```
GET /api/conversations/{conversation_id}
```

**Get Jobs:**
```
GET /api/jobs?status=completed
```

**Get Logs:**
```
GET /api/logs?level=ERROR&limit=100
```

#### 3. **Modified Endpoints**

**Chat endpoint now returns conversation_id:**
```javascript
POST /api/ai/chat

Response:
{
  "role": "assistant",
  "content": "I can help you build a pipeline...",
  "conversation_id": "uuid-here",  // NEW!
  "job_id": "job-uuid"              // NEW!
}
```

### Frontend Changes

#### 1. **Conversation Persistence**
- Conversation ID stored in React context
- Automatically saved to localStorage
- Restored on page refresh

#### 2. **New Context Values**
```javascript
const {
  conversationId,
  setConversationId,
  currentJobId,
  setCurrentJobId
} = usePipeline();
```

## How It Works

### Conversation Flow

1. **User sends first message**
   ```
   User → Backend: "I need a pipeline"
   ```

2. **Backend creates conversation**
   ```sql
   INSERT INTO conversations (conversation_id, user_email, workspace_id)
   VALUES ('uuid', 'user@example.com', 'workspace-id')
   ```

3. **Backend saves message**
   ```sql
   INSERT INTO conversation_messages (conversation_id, role, content)
   VALUES ('uuid', 'user', 'I need a pipeline')
   ```

4. **Backend returns conversation_id**
   ```json
   {
     "content": "I can help!",
     "conversation_id": "uuid"
   }
   ```

5. **Frontend stores conversation_id**
   ```javascript
   localStorage.setItem('conversationId', 'uuid')
   ```

6. **User refreshes page**
   - Frontend restores conversation_id from localStorage
   - Chat history persists!

### Job Tracking Flow

1. **User clicks "Generate Pipeline"**
   ```
   POST /api/pipelines/generate
   ```

2. **Backend creates job**
   ```sql
   INSERT INTO jobs (job_id, job_type, status)
   VALUES ('job-uuid', 'pipeline_generation', 'pending')
   ```

3. **Backend updates job status**
   ```sql
   UPDATE jobs
   SET status = 'in_progress', pipeline_generation_status = 'in_progress'
   WHERE job_id = 'job-uuid'
   ```

4. **Pipeline generated successfully**
   ```sql
   UPDATE jobs
   SET status = 'completed',
       pipeline_generation_status = 'completed',
       pipeline_definition = '{"activities": [...]}'
   WHERE job_id = 'job-uuid'
   ```

5. **Track deployment**
   ```sql
   UPDATE jobs
   SET pipeline_deployment_status = 'in_progress'
   WHERE job_id = 'job-uuid'
   ```

## Configuration

### Development (Default)
Uses SQLite database stored in `backend/fabric_pipeline.db`

```python
# backend/settings.py
USE_SQLITE = True  # Default
```

No additional configuration needed!

### Production (SQL Server)

1. Update `backend/settings.py`:
   ```python
   USE_SQLITE = False
   ```

2. Configure SQL Server:
   ```python
   DATABASE_SERVER = "your-server.database.windows.net"
   DATABASE_NAME = "fabricdb"
   DATABASE_USER = "admin"
   DATABASE_PASSWORD = "your-password"
   ```

3. Initialize database:
   ```bash
   python backend/init_database.py
   ```

## Testing the Implementation

### Test 1: Verify Database Created

```bash
# Check if database file exists
ls backend/fabric_pipeline.db

# Output: fabric_pipeline.db
```

### Test 2: Check API Endpoints

```bash
# Get conversations (will be empty at first)
curl http://localhost:8080/api/conversations?user_email=test@example.com

# Response: []
```

### Test 3: Send Chat Message

1. Open frontend: http://localhost:3000
2. Send a chat message
3. Check browser console for:
   ```
   Conversation ID: uuid-here
   ```
4. Refresh page - conversation persists!

### Test 4: Check Database Content

```bash
# Use SQLite CLI to query database
sqlite3 backend/fabric_pipeline.db

# List conversations
SELECT * FROM conversations;

# List messages
SELECT role, content FROM conversation_messages;

# List jobs
SELECT job_type, status FROM jobs;

# Exit
.exit
```

## Common Issues

### Issue: "Database service not initialized"

**Solution:** Run initialization:
```bash
python backend/init_database.py
```

### Issue: "No such table: conversations"

**Solution:** Delete old database and reinitialize:
```bash
rm backend/fabric_pipeline.db
python backend/init_database.py
```

### Issue: "Database is locked" (SQLite)

**Solution:** Restart the backend server:
```bash
# Kill existing process
pkill -f "uvicorn main:app"

# Start fresh
uvicorn main:app --reload --port 8080
```

### Issue: "Conversation not persisting"

**Solution:** Check browser console for errors. Ensure conversation_id is being saved:
```javascript
// Check localStorage
console.log(localStorage.getItem('conversationId'));
```

## Database Schema Overview

```
┌─────────────────┐
│  conversations  │
│  (Primary Key)  │
└────────┬────────┘
         │
         │ (1 to many)
         │
    ┌────┴─────────────────┬──────────────────┐
    │                      │                  │
    v                      v                  v
┌──────────────────┐  ┌───────┐  ┌───────────────┐
│ conv_messages    │  │ jobs  │  │     logs      │
│ (Foreign Key)    │  │ (FK)  │  │  (Optional)   │
└──────────────────┘  └───────┘  └───────────────┘
```

**Key Points:**
- Each conversation has many messages
- Each conversation can have many jobs
- Logs can reference conversations and jobs
- Cascade delete: Deleting a conversation deletes all its messages and jobs

## Next Steps

### View Conversation History
The API endpoints are ready, but you need to build the UI:

```javascript
// Example: Fetch user conversations
const response = await fetch(
  '/api/conversations?user_email=user@example.com'
);
const conversations = await response.json();

// Display in UI
conversations.forEach(conv => {
  console.log(`${conv.created_at}: ${conv.message_count} messages`);
});
```

### Monitor Jobs
Track pipeline generation/deployment progress:

```javascript
// Fetch job status
const response = await fetch(`/api/jobs/${jobId}`);
const job = await response.json();

console.log(`Status: ${job.status}`);
console.log(`Generation: ${job.pipeline_generation_status}`);
console.log(`Deployment: ${job.pipeline_deployment_status}`);
```

### View Logs
Check application logs for debugging:

```javascript
// Fetch error logs
const response = await fetch('/api/logs?level=ERROR&limit=50');
const logs = await response.json();

logs.forEach(log => {
  console.error(`${log.timestamp}: ${log.message}`);
});
```

## Benefits

### Before Database
- ❌ Chat history lost on refresh
- ❌ 404 errors
- ❌ No job tracking
- ❌ Limited debugging

### After Database
- ✅ Chat persists across refreshes
- ✅ No more 404 errors
- ✅ Complete job tracking
- ✅ Comprehensive logging
- ✅ Audit trail
- ✅ Ready for production

## Documentation

For detailed documentation, see:
- **Full Guide:** `backend/docs/DATABASE_IMPLEMENTATION.md`
- **API Reference:** Swagger UI at http://localhost:8080/docs

## Support

If you encounter issues:
1. Check logs: `GET /api/logs?level=ERROR`
2. Verify database: `python backend/init_database.py`
3. Check console: Browser DevTools → Console
4. Review: `backend/docs/DATABASE_IMPLEMENTATION.md`

---

**Happy Building! 🚀**

Your conversations now persist, jobs are tracked, and everything is logged. No more 404 errors!
