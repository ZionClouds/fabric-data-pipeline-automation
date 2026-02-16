# Technology Stack

**Analysis Date:** 2026-02-16

## Languages

**Primary:**
- Python 3.11 - Backend API, AI agents, services, database operations
- JavaScript/JSX 18.2.0 - Frontend UI components, React application
- SQL - Database queries, schema management

**Secondary:**
- Bash - Deployment scripts
- YAML - Docker Compose, GitHub Actions configuration

## Runtime

**Environment:**
- Docker containerization (both frontend and backend)
- Python 3.11-slim base image for backend
- Node.js runtime for frontend (React)

**Package Manager:**
- pip (Python) - Backend dependencies
- npm (Node.js) - Frontend dependencies
- Lockfiles: `frontend/package-lock.json` present

## Frameworks

**Core Backend:**
- FastAPI 0.104.1 - REST API framework, async support
- Uvicorn 0.24.0 - ASGI web server

**Frontend:**
- React 18.2.0 - UI framework
- React Scripts 5.0.1 - CRA bundling
- Material-UI (@mui/material, @mui/icons-material) 7.3.5 - Component library
- React-Markdown 9.0.1 - Markdown rendering

**AI & Agents:**
- Anthropic SDK 0.7.8 - Claude AI integration
- OpenAI SDK >=1.12.0 - Azure OpenAI integration
- OpenAI Agents SDK >=0.0.3 - Multi-agent orchestration
- Azure AI Projects >=1.0.0 - Azure AI Foundry integration

**Database & ORM:**
- SQLAlchemy >=2.0.36 - ORM for database abstraction
- Alembic >=1.14.0 - Database migrations
- PyODBC 5.0.1 - ODBC driver for SQL Server
- MSSQL ODBC Driver 18 - Direct SQL Server connection

**Authentication & Security:**
- python-jose[cryptography] 3.3.0 - JWT token handling
- passlib[bcrypt] 1.7.4 - Password hashing
- PyJWT 2.8.1 - JWT encoding/decoding
- cryptography 41.0.7 - Cryptographic operations
- Azure Identity 1.15.0 - Azure service principal authentication
- @azure/msal-browser 2.38.3 - Azure AD authentication (frontend)
- @azure/msal-react 1.5.8 - React integration for Azure AD

**Storage:**
- Azure Storage Blob 12.19.0 - ADLS Gen2 integration
- Azure Storage connectivity for hierarchical namespace containers

**HTTP & Networking:**
- httpx 0.25.2 - Async HTTP client
- requests 2.31.0 - Synchronous HTTP client
- axios 1.6.2 - Frontend HTTP client
- python-multipart 0.0.6 - Multipart form handling

**Development & Utilities:**
- python-dotenv 1.0.0 - Environment variable management
- Pydantic 2.5.0 - Data validation
- Certifi 2024.2.2 - SSL certificate validation

**Frontend UI Utilities:**
- PrismJS 1.29.0 - Syntax highlighting
- react-icons 4.11.0 - Icon components
- react-syntax-highlighter 16.1.0 - Code highlighting
- @emotion/react, @emotion/styled 11.14.0 - CSS-in-JS styling
- @mui/lab 7.0.1-beta.19 - Lab components

## Configuration

**Environment:**
- `.env.example` file documents required configurations
- Environment variables loaded via `python-dotenv`
- Docker Compose defines service-level env vars
- Settings centralized in `backend/settings.py`

**Build:**
- `docker-compose.yml` - Local development orchestration
- `backend/Dockerfile` - Python container with ODBC drivers
- `frontend/Dockerfile` - React build image
- GitHub Actions workflows in `.github/workflows/`

**Database:**
- Azure SQL Server connection via ODBC
- SQLAlchemy URL: `mssql+pyodbc://`
- Connection pooling with 3600s recycle time
- SSL encryption enabled, self-signed cert trusted

## Platform Requirements

**Development:**
- Docker and Docker Compose
- Python 3.11+
- Node.js for frontend
- ODBC Driver 18 for SQL Server (Linux/Mac)
- Microsoft ODBC packages (in Dockerfile)

**Production:**
- Azure Cloud services (SQL Server, Storage, AI Foundry)
- Container deployment (Docker)
- Azure Container Apps or similar orchestration
- Static storage: Azure Storage Account (ADLS Gen2)

**Key System Dependencies (in Dockerfile):**
- `ca-certificates`, `gnupg2`, `apt-transport-https`
- `unixodbc`, `unixodbc-dev` (ODBC runtime)
- `gcc`, `g++` (for compiled dependencies)
- `msodbcsql18`, `mssql-tools18` (Microsoft ODBC driver)

## Database

**Engine:** Microsoft SQL Server (Azure SQL Server)
- Server: `microfabrics.database.windows.net`
- Database: `fabrics`
- Connection encryption enabled
- ODBC Driver 18 for Server authentication

**Models:** SQLAlchemy declarative models in `backend/models/database_models.py`
- Conversation, ConversationMessage, Job, Log entities
- Enums: ConversationStatus, JobStatus, PipelineStageStatus, LogLevel

**Migrations:** Alembic version control in `backend/database/`

---

*Stack analysis: 2026-02-16*
